import os, json, yaml, asyncio, re
import httpx
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from anthropic import Anthropic

# MCP client (para servidor local)
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession

# Configuración
CONFIG_FILE = "beauty_servers.yaml"
SERVER_KEY = "beauty_server"  
ANTHROPIC_MODEL = "claude-3-5-haiku-20241022"
REMOTE_SERVER_URL = "https://web-production-de5ff.up.railway.app"

# Cargar API Key
load_dotenv()
if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("Missing ANTHROPIC_API_KEY in .env")
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Archivos de contexto
CONTEXT_FILE = "../Data/beauty_context.json"
LOG_FILE = "../Data/beauty_log.txt"

# Inicializar archivo de contexto
with open(CONTEXT_FILE, "w", encoding="utf-8") as f:
    json.dump(
        {"server": SERVER_KEY, "mode": "auto", "history": [], "last_tool_memory": {}, "last_list": None},
        f, ensure_ascii=False, indent=2
    )

# Crear configuración híbrida por defecto
if not os.path.exists(CONFIG_FILE):
    default_config = {
        "connection_mode": "auto",  # auto, local, remote
        "servers": {
            "beauty_server": {
                "command": "python",
                "args": ["beauty_server.py"],
                "env": {},
                "cwd": os.getcwd()
            }
        },
        "remote_server": {
            "url": REMOTE_SERVER_URL,
            "timeout": 30
        }
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)

conversation_history: List[Dict[str, str]] = []

# Clase para manejar conexiones híbridas
class BeautyServerManager:
    def __init__(self):
        self.mode = None  # 'local' o 'remote'
        self.remote_url = REMOTE_SERVER_URL
        self.local_session = None
        self.local_tools = None
        
    async def initialize(self, preferred_mode: str = "auto"):
        """Inicializar conexión según modo preferido"""
        if preferred_mode == "remote":
            if await self._test_remote_connection():
                self.mode = "remote"
                print("✅ Conectado al servidor remoto (Railway)")
                return True
            else:
                print("❌ Servidor remoto no disponible, intentando local...")
                preferred_mode = "local"
        
        if preferred_mode in ["local", "auto"]:
            if await self._test_local_connection():
                self.mode = "local"
                print("✅ Conectado al servidor local (MCP)")
                return True
            elif preferred_mode == "auto":
                print("❌ Servidor local no disponible, intentando remoto...")
                if await self._test_remote_connection():
                    self.mode = "remote"
                    print("✅ Conectado al servidor remoto (Railway)")
                    return True
        
        print("❌ No se pudo conectar a ningún servidor")
        return False
    
    async def _test_remote_connection(self) -> bool:
        """Probar conexión al servidor remoto"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.remote_url}/health")
                return response.status_code == 200
        except:
            return False
    
    async def _test_local_connection(self) -> bool:
        """Probar conexión al servidor local"""
        try:
            if not os.path.exists("beauty_server.py") or not os.path.exists("metodos_server.py"):
                return False
            
            cfg = yaml.safe_load(open(CONFIG_FILE, "r", encoding="utf-8"))
            s = cfg["servers"][SERVER_KEY]
            server_params = StdioServerParameters(
                command=s["command"], 
                args=s.get("args", []), 
                env=s.get("env", {})
            )
            
            # Prueba rápida de conexión
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self.local_session = session
                    self.local_tools = await session.list_tools()
                    return True
        except:
            return False
    
    async def list_tools(self) -> Dict[str, Any]:
        """Listar herramientas disponibles según el modo"""
        if self.mode == "local":
            return {
                "tools": [
                    {"name": "create_profile", "description": "Crear perfil de belleza con análisis MCP"},
                    {"name": "show_profile", "description": "Mostrar perfil específico"},
                    {"name": "list_profiles", "description": "Listar todos los perfiles"},
                    {"name": "delete_profile", "description": "Eliminar perfil específico"},
                    {"name": "generate_palette", "description": "Generar paleta personalizada"},
                    {"name": "quick_palette", "description": "Generar paleta rápida"},
                    {"name": "export_data", "description": "Exportar datos de usuario"}
                ],
                "source": "MCP Local"
            }
        else:  # remote
            return {
                "tools": [
                    {"name": "create_profile", "description": "Crear perfil con análisis avanzado (Remoto)"},
                    {"name": "show_profile", "description": "Mostrar perfil específico (Remoto)"},
                    {"name": "list_profiles", "description": "Listar perfiles (Remoto)"},
                    {"name": "delete_profile", "description": "Eliminar perfil (Remoto)"},
                    {"name": "generate_palette", "description": "Generar paleta personalizada (Remoto)"},
                    {"name": "quick_palette", "description": "Generar paleta rápida (Remoto)"},
                    {"name": "generate_simple_palette", "description": "Generar paleta con API original"},
                    {"name": "analyze_harmony", "description": "Analizar armonía de colores"},
                    {"name": "get_quote", "description": "Obtener cita inspiracional"}
                ],
                "source": "REST API Remoto"
            }
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Ejecutar herramienta según el modo"""
        if self.mode == "local":
            return await self._call_local_tool(tool_name, arguments)
        else:
            return await self._call_remote_tool(tool_name, arguments)
    
    async def _call_local_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Ejecutar herramienta MCP local"""
        try:
            # Reconectar si es necesario
            if not self.local_session:
                await self._test_local_connection()
            
            cfg = yaml.safe_load(open(CONFIG_FILE, "r", encoding="utf-8"))
            s = cfg["servers"][SERVER_KEY]
            server_params = StdioServerParameters(
                command=s["command"], 
                args=s.get("args", []), 
                env=s.get("env", {})
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(name=tool_name, arguments=arguments)
                    return "\n".join([c.text for c in result.content if c.type == "text"])
        except Exception as e:
            return f"Error en herramienta local {tool_name}: {str(e)}"
    
    async def _call_remote_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Ejecutar herramienta remota via HTTP"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                
                # Mapear herramientas a endpoints
                if tool_name == "create_profile":
                    response = await client.post(f"{self.remote_url}/mcp/create-profile", json=arguments)
                    
                elif tool_name == "show_profile":
                    user_id = arguments.get("user_id", "")
                    response = await client.get(f"{self.remote_url}/mcp/profile/{user_id}")
                    
                elif tool_name == "list_profiles":
                    response = await client.get(f"{self.remote_url}/mcp/profiles")
                    
                elif tool_name == "delete_profile":
                    user_id = arguments.get("user_id", "")
                    response = await client.delete(f"{self.remote_url}/mcp/profile/{user_id}")
                    
                elif tool_name == "generate_palette":
                    response = await client.post(f"{self.remote_url}/mcp/generate-palette", json=arguments)
                    
                elif tool_name == "quick_palette":
                    response = await client.post(f"{self.remote_url}/mcp/quick-palette", json=arguments)
                    
                elif tool_name == "export_data":
                    user_id = arguments.get("user_id", "")
                    response = await client.get(f"{self.remote_url}/mcp/export/{user_id}")
                    
                elif tool_name == "generate_simple_palette":
                    # Usar endpoint original de API
                    response = await client.post(f"{self.remote_url}/api/generate-palette", json=arguments)
                    
                elif tool_name == "analyze_harmony":
                    response = await client.post(f"{self.remote_url}/api/analyze-harmony", json=arguments)
                    
                elif tool_name == "get_quote":
                    category = arguments.get("category", "")
                    params = {"category": category} if category else {}
                    response = await client.get(f"{self.remote_url}/api/quote", params=params)
                    
                else:
                    return f"Herramienta {tool_name} no reconocida para servidor remoto"
                
                if response.status_code == 200:
                    result = response.json()
                    return json.dumps(result, ensure_ascii=False, indent=2)
                else:
                    return f"Error HTTP {response.status_code}: {response.text}"
                    
        except Exception as e:
            return f"Error en herramienta remota {tool_name}: {str(e)}"

# Instancia global del manager
server_manager = BeautyServerManager()

# Funciones de contexto (sin cambios)
def save_to_context(entry: Dict[str, Any]):
    """Guardar entrada en el contexto"""
    with open(CONTEXT_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data["history"].append(entry)
        data["mode"] = server_manager.mode
        if entry.get("tool_used") and entry.get("arguments"):
            data["last_tool_memory"][entry["tool_used"]] = entry["arguments"]
        f.seek(0)
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.truncate()

def get_last_args_for_tool(tool_name: Optional[str]) -> Optional[Dict[str, Any]]:
    """Obtener últimos argumentos usados para una herramienta"""
    if not tool_name:
        return None
    try:
        with open(CONTEXT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["last_tool_memory"].get(tool_name)
    except FileNotFoundError:
        return None

def log_interaction(entry: Dict[str, Any]):
    """Registrar interacción en archivo de log"""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# Prompts del sistema actualizados
TOOL_SELECTION_SYSTEM = """Eres un asistente especializado en belleza y paletas de colores. Tienes acceso a herramientas tanto locales (MCP) como remotas (API).

HERRAMIENTAS DISPONIBLES:
- create_profile: Crear perfil de belleza con análisis científico
- show_profile: Mostrar información de perfil específico
- list_profiles: Listar todos los perfiles existentes
- delete_profile: Eliminar perfil específico
- generate_palette: Generar paleta personalizada basada en perfil
- quick_palette: Generar paleta rápida sin perfil específico
- export_data: Exportar datos de usuario
- generate_simple_palette: Generar paleta con API simple (solo remoto)
- analyze_harmony: Analizar armonía de colores (solo remoto)
- get_quote: Obtener cita inspiracional (solo remoto)

REGLAS:
- Si el usuario quiere "crear usuario/perfil", usa create_profile
- Si pregunta por "ver/mostrar perfil", usa show_profile
- Si quiere "listar perfiles", usa list_profiles
- Si quiere "eliminar perfil", usa delete_profile
- Si quiere "generar paleta" con perfil, usa generate_palette
- Si quiere "paleta rápida", usa quick_palette
- Si quiere "analizar colores/armonía", usa analyze_harmony
- Si quiere "cita/frase inspiracional", usa get_quote
- Si NO coincide con ninguna herramienta, usa "tool_name": null

Responde SOLO con JSON:
{ "tool_name": string|null, "arguments": object, "reasoning_summary": string }"""

def ask_claude_for_tool(user_message: str, available_tools: List[Dict]) -> Dict[str, Any]:
    """Preguntar a Claude qué herramienta usar"""
    tools_desc = "\n".join([f"- {t['name']}: {t['description']}" for t in available_tools])
    
    prompt = f"""Herramientas disponibles:
{tools_desc}

Mensaje del usuario: {user_message}

Analiza el mensaje y selecciona la herramienta más apropiada. Devuelve SOLO JSON."""
    
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1000,
        temperature=0.2,
        system=TOOL_SELECTION_SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )
    
    text = response.content[0].text.strip()
    try:
        return json.loads(text)
    except:
        return {"tool_name": None, "arguments": {}, "reasoning_summary": "No se pudo parsear respuesta."}

def ask_claude_for_final_answer(tool_output_text: str, user_message: str, server_mode: str) -> str:
    """Generar respuesta final amigable"""
    mode_info = "servidor local MCP" if server_mode == "local" else "servidor remoto Railway"
    
    system_message = f"""Eres un experto en belleza y paletas de colores. Convierte la salida técnica en respuestas naturales y útiles.

Estás usando el {mode_info} para procesar las solicitudes.

DIRECTRICES:
- Usa un tono cálido y profesional
- Explica colores de manera descriptiva y atractiva  
- Da consejos prácticos cuando sea relevante
- Usa la información EXACTAMENTE como viene
- Si hay códigos hex, menciona tanto el código como descripción
- Menciona sutilmente que la respuesta viene del {mode_info}"""
    
    prompt = f"""Mensaje del usuario: {user_message}

Salida de la herramienta:
{tool_output_text}

Convierte esta información en una respuesta natural y útil."""
    
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1500,
        temperature=0.3,
        system=system_message,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text.strip()

def ask_claude_basic_fallback(user_message: str) -> str:
    """Respuesta general cuando no hay herramienta específica"""
    system_message = """Eres un asistente inteligente especializado en belleza pero que puede responder cualquier pregunta. 

Respondes de forma natural y completa, sin limitaciones de tema. Si no es sobre belleza, actúas como asistente general. Si es sobre belleza pero no tienes herramientas, ofreces consejos generales."""
    
    messages = conversation_history + [
        {"role": "user", "content": user_message}
    ]
    
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1500,
        temperature=0.3,
        system=system_message,
        messages=messages
    )
    
    reply = response.content[0].text.strip()
    conversation_history.append({"role": "user", "content": user_message})
    conversation_history.append({"role": "assistant", "content": reply})
    return reply

# Función principal actualizada
async def main():
    """Función principal del cliente híbrido"""
    print(" Iniciando Cliente Híbrido de Belleza...")
    print("-" * 60)
    
    # Cargar configuración
    cfg = yaml.safe_load(open(CONFIG_FILE, "r", encoding="utf-8"))
    connection_mode = cfg.get("connection_mode", "auto")
    
    print(f"Modo de conexión configurado: {connection_mode}")
    print("Probando conexiones...")
    
    # Intentar inicializar servidor
    if not await server_manager.initialize(connection_mode):
        print("\n❌ No se pudo conectar a ningún servidor.")
        print("Verificaciones sugeridas:")
        print("1. Para servidor local: beauty_server.py y metodos_server.py en directorio")
        print("2. Para servidor remoto: conexión a internet")
        print("3. Dependencias instaladas correctamente")
        return
    
    print(f"\n Cliente Híbrido de Belleza Activo!")
    print(f" Conectado a: {server_manager.mode}")
    print("-" * 60)
    print("Funcionalidades disponibles:")
    print("- Responder CUALQUIER pregunta general")
    print("- Análisis avanzado de belleza y colorimetría")
    print("- Generación de paletas especializadas")
    print("- Consejos de moda, maquillaje y estilo")
    print("")
    print("Comandos especiales:")
    print("  'tools' - Ver herramientas disponibles")
    print("  'mode' - Ver modo de conexión actual")
    print("  'switch' - Cambiar entre local/remoto")
    print("  'exit' - Salir")
    print("-" * 60)
    print()
    
    tools_info = await server_manager.list_tools()
    available_tools = tools_info["tools"]
    
    print(f"✅ Sistema listo. Herramientas disponibles: {len(available_tools)} ({tools_info['source']})")
    
    ps = PromptSession()
    
    while True:
        try:
            user_msg = (await ps.prompt_async(f"[{server_manager.mode}] > ")).strip()
            
            if not user_msg:
                continue
                
            if user_msg.lower() in ("exit", "quit", "salir"):
                print(" ¡Hasta pronto! Espero haberte ayudado con tus consultas.")
                break
                
            if user_msg.lower() == "tools":
                print(f"\nHERRAMIENTAS DISPONIBLES ({tools_info['source']}):")
                for tool in available_tools:
                    print(f"  - {tool['name']}: {tool['description']}")
                print()
                continue
            
            if user_msg.lower() == "mode":
                mode_desc = "MCP Local" if server_manager.mode == "local" else "REST API Remoto"
                print(f"\n Modo actual: {server_manager.mode} ({mode_desc})")
                print(f" Fuente: {tools_info['source']}")
                print()
                continue
            
            if user_msg.lower() == "switch":
                new_mode = "remote" if server_manager.mode == "local" else "local"
                print(f"\n Cambiando a modo {new_mode}...")
                
                if await server_manager.initialize(new_mode):
                    tools_info = await server_manager.list_tools()
                    available_tools = tools_info["tools"]
                    print(f"✅ Cambiado exitosamente a {server_manager.mode}")
                else:
                    print(f"❌ No se pudo cambiar a {new_mode}, manteniendo {server_manager.mode}")
                print()
                continue
            
            # Procesar solicitud normal
            print(" Analizando solicitud...")
            selection = ask_claude_for_tool(user_msg, available_tools)
            tool_name = selection.get("tool_name")
            tool_args = selection.get("arguments", {}) or {}
            
            # Usar argumentos previos si están vacíos
            last_args = get_last_args_for_tool(tool_name)
            if tool_name and last_args and not tool_args:
                tool_args = last_args

            print(f" Herramienta: {tool_name or 'ninguna'}")
            print(f" Razonamiento: {selection.get('reasoning_summary', 'N/A')}")
            
            tool_output_text = ""
            
            if tool_name and any(t["name"] == tool_name for t in available_tools):
                try:
                    print(f" Ejecutando en servidor {server_manager.mode}...")
                    tool_output_text = await server_manager.call_tool(tool_name, tool_args)
                    
                    print(" Generando respuesta personalizada...")
                    final_answer = ask_claude_for_final_answer(tool_output_text, user_msg, server_manager.mode)
                except Exception as e:
                    final_answer = f"Error ejecutando {tool_name}: {e}"
            else:
                print(" Respondiendo como asistente general...")
                final_answer = ask_claude_basic_fallback(user_msg)

            print("\n" + "="*60)
            print(" RESPUESTA:")
            print(final_answer)
            print("="*60 + "\n")

            # Guardar contexto
            entry = {
                "timestamp": datetime.now().isoformat(),
                "user": user_msg,
                "server_mode": server_manager.mode,
                "tool_used": tool_name,
                "arguments": tool_args,
                "tool_output": tool_output_text,
                "final_answer": final_answer,
            }
            
            save_to_context(entry)
            log_interaction(entry)
        
        except KeyboardInterrupt:
            print("\n\n ¡Hasta pronto!")
            break
        except Exception as e:
            print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    asyncio.run(main())