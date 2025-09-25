# chat_simple.py
import asyncio
import json
import os
from contextlib import AsyncExitStack
from typing import Any, Optional
from dataclasses import dataclass, field

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from dotenv import load_dotenv

load_dotenv()

try:
    import anthropic
except Exception:
    anthropic = None

@dataclass
class ServerConn:
    name: str
    command: str = ""
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)

class MCPHost:
    """Host MCP simplificado para Git y Filesystem"""
    def __init__(self):
        # Configuración de servidores
        self.server_defs = [
            ServerConn(
                name="filesystem",
                command="python",
                args=["filesystem_server.py"],
                env={
                    "FS_ROOT": os.getcwd(),  # Usa el directorio actual como raíz
                    "FS_CWD": "."
                }
            ),
            ServerConn(
                name="git_server", 
                command="python",
                args=["git_server.py"],
                env={}
            )
        ]
        
        self._stack: AsyncExitStack | None = None
        self.sessions: dict[str, ClientSession] = {}
        self.tools_schema: list[dict[str, Any]] = []
        self.tool_name_map: dict[str, tuple[str, str]] = {}

    async def connect_all(self):
        """Conecta a todos los servidores MCP"""
        self._stack = AsyncExitStack()
        await self._stack.__aenter__()

        for server_def in self.server_defs:
            try:
                print(f"Conectando a {server_def.name}...")
                
                params = StdioServerParameters(
                    command=server_def.command, 
                    args=server_def.args, 
                    env=server_def.env
                )
                
                client_cmgr = stdio_client(params)
                streams = await self._stack.enter_async_context(client_cmgr)
                read, write = streams
                
                session_cmgr = ClientSession(read, write)
                session = await self._stack.enter_async_context(session_cmgr)
                
                await session.initialize()
                
                self.sessions[server_def.name] = session
                print(f"✅ Conectado a {server_def.name}")
                
            except Exception as e:
                print(f"❌ Error conectando a {server_def.name}: {e}")

        # Descubrir herramientas disponibles
        await self._discover_all_tools()

    async def _discover_all_tools(self):
        """Descubre todas las herramientas disponibles en los servidores"""
        self.tools_schema.clear()
        self.tool_name_map.clear()
        
        for server_name, session in self.sessions.items():
            try:
                tools = await session.list_tools()
                print(f"\n Herramientas en {server_name}:")
                
                for tool in tools.tools:
                    safe_name = f"{server_name}__{tool.name}"
                    self.tool_name_map[safe_name] = (server_name, tool.name)
                    
                    self.tools_schema.append({
                        "name": safe_name,
                        "description": f"[{server_name}] {tool.description or ''}",
                        "input_schema": tool.inputSchema or {"type": "object", "properties": {}}
                    })
                    
                    print(f"  - {tool.name}: {tool.description or 'Sin descripción'}")
                    
            except Exception as e:
                print(f"❌ Error listando herramientas de {server_name}: {e}")

    async def call_tool(self, namespaced: str, arguments: dict[str, Any]):
        """Ejecuta una herramienta"""
        if namespaced not in self.tool_name_map:
            raise ValueError(f"Herramienta '{namespaced}' no encontrada")
            
        server_name, tool_name = self.tool_name_map[namespaced]
        session = self.sessions[server_name]
        
        # Auto-wrap argumentos si es necesario
        tool_args = arguments
        if "params" not in arguments and any(prop == "params" for prop in self.tools_schema):
            # Buscar si esta herramienta específica necesita wrapping
            for schema in self.tools_schema:
                if schema["name"] == namespaced:
                    props = schema.get("input_schema", {}).get("properties", {})
                    if "params" in props:
                        tool_args = {"params": arguments}
                    break
        
        print(f"\n🔧 Ejecutando: {server_name}.{tool_name}")
        print(f"📥 Argumentos: {json.dumps(tool_args, indent=2)}")
        
        result = await session.call_tool(tool_name, arguments=tool_args)
        
        # Extraer texto de la respuesta
        text_blocks = []
        for content in getattr(result, "content", []) or []:
            if hasattr(content, "text"):
                text_blocks.append(content.text)
        
        response_text = "\n".join(text_blocks)
        print(f" Resultado: {response_text[:200]}{'...' if len(response_text) > 200 else ''}")
        
        return {
            "server": server_name,
            "tool": tool_name, 
            "text": response_text
        }

    async def disconnect_all(self):
        """Desconecta todos los servidores"""
        if self._stack:
            try:
                await self._stack.aclose()
            finally:
                self._stack = None
        self.sessions.clear()

class ChatApp:
    """Aplicación de chat que usa herramientas MCP"""
    def __init__(self, host: MCPHost):
        self.host = host
        self.messages: list[dict[str, Any]] = []
        
        # Configurar cliente de Anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic and api_key:
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        else:
            self.client = None
            print("⚠️  No se encontró ANTHROPIC_API_KEY o librería anthropic no disponible")
            
        self.system = (
            "Eres un asistente útil que puede usar herramientas para trabajar con archivos y Git.\n"
            "Cuando el usuario solicite operaciones de archivos o Git, usa las herramientas disponibles.\n"
            "Responde en español de manera clara y útil."
        )

    async def ask(self, user_text: str) -> str:
        """Procesa una pregunta del usuario"""
        self.messages.append({
            "role": "user", 
            "content": [{"type": "text", "text": user_text}]
        })

        if not self.client:
            return "❌ No hay cliente de Anthropic configurado. Verifica tu ANTHROPIC_API_KEY."

        try:
            # Primera llamada - el LLM decide si usar herramientas
            response = self.client.messages.create(
                model=self.model,
                system=self.system,
                tools=self.host.tools_schema,
                messages=self.messages,
                max_tokens=1000
            )

            # Guardar respuesta del asistente
            self.messages.append({"role": "assistant", "content": response.content})
            
            # Verificar si hay tool_use
            tool_uses = [c for c in response.content if getattr(c, "type", "") == "tool_use"]
            
            if tool_uses:
                # Ejecutar herramientas
                tool_results = []
                confirmations = []
                
                for tool_use in tool_uses:
                    name = tool_use.name
                    args = tool_use.input or {}
                    
                    try:
                        result = await self.host.call_tool(name, args)
                        
                        confirmations.append(f"✅ Ejecuté {result['server']}.{result['tool']}")
                        
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": json.dumps(result, ensure_ascii=False)
                        })
                        
                    except Exception as e:
                        error_msg = f"Error ejecutando {name}: {str(e)}"
                        confirmations.append(f"❌ {error_msg}")
                        
                        tool_results.append({
                            "type": "tool_result", 
                            "tool_use_id": tool_use.id,
                            "content": f"Error: {str(e)}"
                        })

                # Segunda llamada con resultados de herramientas
                self.messages.append({"role": "user", "content": tool_results})
                
                response2 = self.client.messages.create(
                    model=self.model,
                    system=self.system,
                    messages=self.messages,
                    max_tokens=1000
                )
                
                final_text = "".join([
                    c.text for c in response2.content 
                    if getattr(c, "type", "") == "text"
                ])
                
                self.messages.append({"role": "assistant", "content": response2.content})
                
                # Combinar confirmaciones con respuesta final
                return "\n\n".join(confirmations + [final_text])
            
            else:
                # No se usaron herramientas, respuesta directa
                direct_text = "".join([
                    c.text for c in response.content 
                    if getattr(c, "type", "") == "text"
                ])
                return direct_text

        except Exception as e:
            return f"❌ Error procesando solicitud: {str(e)}"

async def main():
    """Función principal"""
    print(" Iniciando cliente MCP simplificado...")
    print(" Servidores: Filesystem + Git")
    
    # Crear y conectar host
    host = MCPHost()
    await host.connect_all()
    
    if not host.sessions:
        print("❌ No se pudo conectar a ningún servidor. Verifica las rutas de los servidores.")
        return
    
    # Crear aplicación de chat
    app = ChatApp(host)
    
    print("\n" + "="*50)
    print(" Cliente MCP listo!")
    print("Puedes hacer preguntas como:")
    print("- 'Lista los archivos en el directorio actual'")
    print("- 'Crea un archivo llamado test.txt con contenido de prueba'") 
    print("- 'Inicializa un repositorio Git aquí'")
    print("- 'Haz commit de los cambios'")
    print("\nEscribe 'quit' o 'salir' para terminar.")
    print("="*50)
    
    try:
        while True:
            user_input = input("\n Tu pregunta: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'salir', 'exit']:
                break
                
            print("\nProcesando...")
            response = await app.ask(user_input)
            print(f"\n Respuesta:\n{response}")
            
    except (EOFError, KeyboardInterrupt):
        print("\n\n👋 ¡Hasta luego!")
        
    finally:
        await host.disconnect_all()

if __name__ == "__main__":
    asyncio.run(main())