#!/usr/bin/env python3
"""
Cliente Universal MCP Multi-Servidor
Conecta y utiliza múltiples servidores MCP simultáneamente:
- Beauty Server (análisis de belleza y color)
- Sleep Coach (recomendaciones de sueño)
- Game Server (análisis de videojuegos)
"""

import os
import json
import yaml
import asyncio
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from anthropic import Anthropic

# MCP client
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession

# CONFIGURACIÓN ROBUSTA DE RUTAS
CURRENT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = CURRENT_DIR.parent.absolute()

print(f"🏠 Directorio actual: {CURRENT_DIR}")
print(f"🌍 Raíz del proyecto: {PROJECT_ROOT}")

# Configuración de archivos
CONFIG_FILE = PROJECT_ROOT / "universal_servers.yaml"
ANTHROPIC_MODEL = "claude-3-5-haiku-20241022"

# Archivos de contexto
DATA_DIR = PROJECT_ROOT / "Data"
CONTEXT_FILE = DATA_DIR / "universal_context.json"
LOG_FILE = DATA_DIR / "universal_log.txt"

# Cargar .env
ENV_LOCATIONS = [
    PROJECT_ROOT / ".env",
    CURRENT_DIR / ".env",
    Path(".env"),
]

env_loaded = False
for env_path in ENV_LOCATIONS:
    if env_path.exists():
        print(f"✅ Encontrado .env en: {env_path}")
        load_dotenv(env_path)
        env_loaded = True
        break

if not env_loaded:
    print("❌ No se encontró archivo .env")

# Verificar API Key
if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("❌ Missing ANTHROPIC_API_KEY in .env")

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Crear directorios necesarios
DATA_DIR.mkdir(exist_ok=True)

class MultiServerManager:
    """Manager para múltiples conexiones MCP"""
    
    def __init__(self):
        self.servers = {}  # server_name -> session info
        self.tools_catalog = {}  # server_name -> tools
        self.server_configs = {}
        self.active_connections = {}
        
    async def initialize_servers(self):
        """Inicializar todos los servidores disponibles"""
        # Configuración de servidores
        server_configs = {
            "beauty_server": {
                "command": "python",
                "args": [str(PROJECT_ROOT / "Servidores" / "Local" / "beauty_server.py")],
                "env": {},
                "cwd": str(PROJECT_ROOT),
                "description": "Servidor de análisis de belleza y colorimetría"
            },
            "sleep_coach": {
                "command": "python", 
                "args": [str(PROJECT_ROOT / "Servidores" / "Externos" / "Fabi" / "sleep_coach.py")],
                "env": {},
                "cwd": str(PROJECT_ROOT),
                "description": "Servidor de coaching de sueño personalizado"
            },
            "game_server": {
                "command": "python",
                "args": [str(PROJECT_ROOT / "Servidores"  / "Externos" / "JP" / "server.py")], 
                "env": {},
                "cwd": str(PROJECT_ROOT),
                "description": "Servidor de análisis de videojuegos"
            }
        }
        
        self.server_configs = server_configs
        
        # Intentar conectar a cada servidor
        connected_servers = []
        for server_name, config in server_configs.items():
            try:
                success = await self._test_server_connection(server_name, config)
                if success:
                    connected_servers.append(server_name)
                    print(f"✅ {server_name}: {config['description']}")
                else:
                    print(f"❌ {server_name}: No disponible")
            except Exception as e:
                print(f"❌ {server_name}: Error - {str(e)}")
        
        if not connected_servers:
            raise Exception("No se pudo conectar a ningún servidor MCP")
            
        print(f"\n🌟 Servidores conectados: {len(connected_servers)}")
        return connected_servers
    
    async def _test_server_connection(self, server_name: str, config: Dict[str, Any]) -> bool:
        """Probar conexión a un servidor específico"""
        try:
            # Verificar que los archivos existan
            server_file = Path(config["args"][0])
            if not server_file.exists():
                return False
            
            server_params = StdioServerParameters(
                command=config["command"],
                args=config["args"],
                env=config.get("env", {})
            )
            
            # Prueba rápida de conexión
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    
                    # Guardar información del servidor
                    self.servers[server_name] = {
                        "config": config,
                        "params": server_params,
                        "status": "available"
                    }
                    self.tools_catalog[server_name] = tools.tools
                    
                    return True
        except Exception:
            return False
    
    async def call_tool_on_server(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Ejecutar herramienta en servidor específico"""
        if server_name not in self.servers:
            return f"Error: Servidor {server_name} no disponible"
        
        try:
            server_params = self.servers[server_name]["params"]
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(name=tool_name, arguments=arguments)
                    return "\n".join([c.text for c in result.content if c.type == "text"])
                    
        except Exception as e:
            return f"Error ejecutando {tool_name} en {server_name}: {str(e)}"
    
    def get_all_tools(self) -> Dict[str, List]:
        """Obtener todas las herramientas de todos los servidores"""
        all_tools = {}
        for server_name, tools in self.tools_catalog.items():
            all_tools[server_name] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "server": server_name
                }
                for tool in tools
            ]
        return all_tools
    
    def find_server_for_tool(self, tool_name: str) -> Optional[str]:
        """Encontrar qué servidor tiene una herramienta específica"""
        for server_name, tools in self.tools_catalog.items():
            for tool in tools:
                if tool.name == tool_name:
                    return server_name
        return None

# Funciones de contexto
def init_context():
    """Inicializar archivo de contexto"""
    if not CONTEXT_FILE.exists():
        with open(CONTEXT_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "servers": [],
                "history": [],
                "last_tool_memory": {},
                "session_info": {
                    "created_at": datetime.now().isoformat(),
                    "last_active": datetime.now().isoformat(),
                    "total_interactions": 0
                }
            }, f, ensure_ascii=False, indent=2)

def save_to_context(entry: Dict[str, Any]):
    """Guardar entrada en el contexto"""
    with open(CONTEXT_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data["history"].append(entry)
        if entry.get("tool_used") and entry.get("arguments"):
            data["last_tool_memory"][entry["tool_used"]] = entry["arguments"]
        data["session_info"]["last_active"] = datetime.now().isoformat()
        data["session_info"]["total_interactions"] += 1
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

# Prompts del sistema
TOOL_SELECTION_SYSTEM = """Eres un asistente especializado que puede usar múltiples servidores MCP:

SERVIDORES DISPONIBLES:
- beauty_server: Análisis de belleza, colorimetría, paletas de color, perfiles personales
- sleep_coach: Coaching de sueño, análisis de patrones, recomendaciones personalizadas
- game_server: Análisis de videojuegos, estadísticas, rankings

HERRAMIENTAS DISPONIBLES:
{tools_catalog}

REGLAS:
- Analiza la consulta del usuario y selecciona la herramienta más apropiada
- Si es sobre belleza/color/maquillaje/ropa -> beauty_server
- Si es sobre sueño/descanso/rutinas/cronotipos -> sleep_coach  
- Si es sobre videojuegos/juegos/rankings/géneros -> game_server
- Si NO coincide con ninguna herramienta específica, usa "tool_name": null
- Si necesitas más información, pregunta al usuario

Responde SOLO con JSON:
{ "tool_name": string|null, "server_name": string|null, "arguments": object, "reasoning_summary": string }"""

conversation_history: List[Dict[str, str]] = []

def ask_claude_for_tool(user_message: str, all_tools: Dict[str, List]) -> Dict[str, Any]:
    """Preguntar a Claude qué herramienta usar y en qué servidor"""
    # Construir catálogo de herramientas
    tools_catalog = ""
    for server_name, tools in all_tools.items():
        tools_catalog += f"\n{server_name.upper()}:\n"
        for tool in tools:
            tools_catalog += f"  - {tool['name']}: {tool['description']}\n"
    
    formatted_system = TOOL_SELECTION_SYSTEM.format(tools_catalog=tools_catalog)
    
    prompt = f"""Mensaje del usuario: {user_message}

Analiza el mensaje y selecciona la herramienta más apropiada y el servidor correcto."""
    
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1000,
        temperature=0.2,
        system=formatted_system,
        messages=[{"role": "user", "content": prompt}]
    )
    
    text = response.content[0].text.strip()
    try:
        return json.loads(text)
    except:
        return {
            "tool_name": None,
            "server_name": None, 
            "arguments": {},
            "reasoning_summary": "No se pudo parsear respuesta."
        }

def ask_claude_for_final_answer(tool_output_text: str, user_message: str, server_name: str) -> str:
    """Generar respuesta final amigable"""
    system_message = f"""Eres un asistente experto que usa múltiples servidores especializados para ayudar al usuario.

El resultado viene del servidor: {server_name.upper()}

DIRECTRICES:
- Usa un tono cálido y profesional
- Convierte la información técnica en respuestas naturales y útiles
- Da contexto sobre qué tipo de análisis se realizó
- Usa la información EXACTAMENTE como viene
- Menciona sutilmente que la respuesta proviene del servidor {server_name}"""
    
    prompt = f"""Mensaje del usuario: {user_message}

Salida del servidor {server_name}:
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

def ask_claude_general_fallback(user_message: str) -> str:
    """Respuesta general cuando no hay herramienta específica"""
    system_message = """Eres un asistente inteligente con acceso a servidores especializados en:
- Belleza y colorimetría (análisis de color personal, maquillaje, moda)
- Coaching de sueño (rutinas, análisis de patrones, recomendaciones)  
- Análisis de videojuegos (estadísticas, rankings, datos)

Si la pregunta no es específica de estas áreas, responde como asistente general.
Si es de estas áreas pero necesitas más información, guía al usuario sobre qué puede hacer."""
    
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

# Función principal
async def main():
    """Función principal del cliente universal"""
    print("🌟 CLIENTE UNIVERSAL MCP - MULTI-SERVIDOR")
    print("=" * 60)
    
    # Inicializar contexto
    init_context()
    
    # Inicializar manager de servidores
    server_manager = MultiServerManager()
    
    print("🔍 Detectando servidores disponibles...")
    try:
        connected_servers = await server_manager.initialize_servers()
    except Exception as e:
        print(f"❌ Error inicializando servidores: {e}")
        return
    
    # Obtener catálogo completo de herramientas
    all_tools = server_manager.get_all_tools()
    total_tools = sum(len(tools) for tools in all_tools.values())
    
    print("\n🎯 ¡SISTEMA UNIVERSAL ACTIVO!")
    print("-" * 60)
    print("Capacidades disponibles:")
    print("💄 BELLEZA: Análisis de color, paletas personalizadas, consejos de moda")
    print("😴 SUEÑO: Rutinas personalizadas, análisis de patrones, mejora del descanso") 
    print("🎮 VIDEOJUEGOS: Estadísticas, rankings, análisis de datos")
    print("🤖 GENERAL: Responder cualquier pregunta como asistente inteligente")
    print("")
    print("Comandos especiales:")
    print("  'servers' - Ver servidores conectados")
    print("  'tools' - Ver todas las herramientas disponibles")
    print("  'help [área]' - Ayuda específica (belleza/sueño/juegos)")
    print("  'exit' - Salir")
    print("-" * 60)
    print(f"✅ {len(connected_servers)} servidores | {total_tools} herramientas disponibles")
    print()
    
    ps = PromptSession()
    
    while True:
        try:
            user_msg = (await ps.prompt_async("[UNIVERSAL] > ")).strip()
            
            if not user_msg:
                continue
                
            if user_msg.lower() in ("exit", "quit", "salir"):
                print("\n🌟 ¡Hasta pronto! Gracias por usar el sistema universal.")
                break
            
            if user_msg.lower() == "servers":
                print("\n📡 SERVIDORES CONECTADOS:")
                for server_name, server_info in server_manager.servers.items():
                    config = server_info["config"]
                    print(f"  ✅ {server_name}: {config['description']}")
                print()
                continue
            
            if user_msg.lower() == "tools":
                print("\n🛠️ HERRAMIENTAS DISPONIBLES:")
                for server_name, tools in all_tools.items():
                    print(f"\n📋 {server_name.upper()} ({len(tools)} herramientas):")
                    for tool in tools:
                        print(f"  • {tool['name']}: {tool['description']}")
                print()
                continue
                
            if user_msg.lower().startswith("help"):
                parts = user_msg.split()
                area = parts[1] if len(parts) > 1 else None
                
                if area == "belleza":
                    print("""
💄 AYUDA - ANÁLISIS DE BELLEZA:
  • "crear perfil [nombre]" - Crear análisis de color personal
  • "mostrar perfil [usuario]" - Ver análisis existente  
  • "generar paleta de ropa para trabajo" - Paletas personalizadas
  • "paleta rápida de maquillaje" - Paletas sin perfil
  • "listar usuarios" - Ver todos los perfiles
                    """)
                elif area == "sueño":
                    print("""
😴 AYUDA - COACHING DE SUEÑO:
  • "crear perfil de sueño [nombre]" - Análisis personalizado
  • "analizar mi patrón de sueño" - Detectar problemas
  • "recomendaciones personalizadas" - Consejos específicos
  • "horario semanal optimizado" - Rutinas completas
  • "consejo rápido sobre insomnio" - Ayuda inmediata
                    """)
                elif area == "juegos":
                    print("""
🎮 AYUDA - ANÁLISIS DE VIDEOJUEGOS:
  • "información del juego [nombre]" - Datos completos
  • "mejores juegos de RPG" - Rankings por género
  • "top ventas Nintendo DS" - Mejores por plataforma  
  • "publisher con más ventas" - Análisis de editores
  • "juegos más vendidos en Japón" - Datos por región
                    """)
                else:
                    print("""
🌟 AYUDA GENERAL:
  Puedo ayudarte con:
  • Preguntas generales sobre cualquier tema
  • Análisis especializado de belleza y color
  • Coaching personalizado de sueño y rutinas
  • Estadísticas y análisis de videojuegos
  
  Usa 'help [área]' para ayuda específica:
  • help belleza
  • help sueño  
  • help juegos
                    """)
                continue
            
            # Procesar solicitud normal
            print("🔍 Analizando solicitud...")
            
            selection = ask_claude_for_tool(user_msg, all_tools)
            tool_name = selection.get("tool_name")
            server_name = selection.get("server_name") 
            tool_args = selection.get("arguments", {}) or {}
            
            # Usar argumentos previos si están vacíos
            last_args = get_last_args_for_tool(tool_name)
            if tool_name and last_args and not tool_args:
                tool_args = last_args

            print(f"🎯 Herramienta: {tool_name or 'ninguna'}")
            print(f"🖥️ Servidor: {server_name or 'ninguno'}")  
            print(f"💭 Razonamiento: {selection.get('reasoning_summary', 'N/A')}")
            
            tool_output_text = ""
            
            if tool_name and server_name and server_name in server_manager.servers:
                try:
                    print(f"⚡ Ejecutando en {server_name}...")
                    tool_output_text = await server_manager.call_tool_on_server(
                        server_name, tool_name, tool_args
                    )
                    
                    print("✨ Generando respuesta personalizada...")
                    final_answer = ask_claude_for_final_answer(tool_output_text, user_msg, server_name)
                except Exception as e:
                    final_answer = f"❌ Error ejecutando {tool_name} en {server_name}: {e}"
            else:
                print("🤖 Respondiendo como asistente general...")
                final_answer = ask_claude_general_fallback(user_msg)

            print("\n" + "="*60)
            print("📋 RESPUESTA:")
            print(final_answer)
            print("="*60 + "\n")

            # Guardar contexto
            entry = {
                "timestamp": datetime.now().isoformat(),
                "user": user_msg,
                "tool_used": tool_name,
                "server_used": server_name,
                "arguments": tool_args,
                "tool_output": tool_output_text,
                "final_answer": final_answer,
            }
            
            save_to_context(entry)
        
        except KeyboardInterrupt:
            print("\n\n🌟 ¡Hasta pronto!")
            break
        except Exception as e:
            print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    asyncio.run(main())