#!/usr/bin/env python3
"""
Cliente Universal MCP Multi-Servidor - BASADO EN BEAUTY_CLIENT EXITOSO
Funciona igual que beauty_client pero con múltiples servidores MCP
"""

import os
import json
import yaml
import asyncio
from typing import Dict, Any, Optional, List
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

print(f"📂 Directorio actual: {CURRENT_DIR}")
print(f"🌐 Raíz del proyecto: {PROJECT_ROOT}")

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

# Inicializar contexto
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
    try:
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
    except Exception as e:
        print(f"Error guardando contexto: {e}")

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

# Variable global para historial de conversación
conversation_history: List[Dict[str, str]] = []

# CONFIGURACIÓN DE SERVIDORES
def create_default_config():
    """Crear configuración por defecto si no existe"""
    default_config = {
        "servers": {
            "beauty_server": {
                "name": "Beauty & Color Analysis Server",
                "description": "Servidor de análisis de belleza y colorimetría",
                "command": "python",
                "args": [str(PROJECT_ROOT / "Servidores" / "Local" / "beauty_server.py")],
                "enabled": True,
                "cwd": str(PROJECT_ROOT)
            },
            "sleep_coach": {
                "name": "Sleep Coaching Server", 
                "description": "Servidor de coaching de sueño",
                "command": "python",
                "args": [str(PROJECT_ROOT / "Servidores" / "Externos" / "Fabi" / "sleep_coach.py")],
                "enabled": True,
                "cwd": str(PROJECT_ROOT)
            },
            "game_server": {
                "name": "Video Game Analysis Server",
                "description": "Servidor de análisis de videojuegos", 
                "command": "python",
                "args": [str(PROJECT_ROOT / "Servidores" / "Externos" / "JP" / "server.py")],
                "enabled": True,
                "cwd": str(PROJECT_ROOT)
            }
        }
    }
    
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"📄 Configuración por defecto creada en: {CONFIG_FILE}")

# SISTEMA DE SELECCIÓN DE HERRAMIENTAS MEJORADO
TOOL_SELECTION_SYSTEM = """Eres un asistente especializado con acceso a múltiples servidores MCP:

ESTRATEGIA INTELIGENTE POR SERVIDOR:

🎮 GAME_SERVER - Usa géneros exactos:
- Para RPG: usa "Role-Playing" (no "RPG") 
- Para contar géneros: count_games_by_genre con {} (sin argumentos)
- Para mejores juegos: top_games_by_sales con {"genre": "Role-Playing", "limit": 10}
- Para publishers: publisher_leaderboard con {"limit": 10}

😴 SLEEP_COACH - Usa herramientas simples:
- Para consultas generales: quick_sleep_advice con {"query": "texto_literal_del_usuario"}
- NO uses create_user_profile (requiere muchos datos)

💄 BEAUTY_SERVER - Usa herramientas correctas según la información:
- Para paletas SIN perfil: quick_palette con {"palette_type": "ropa|maquillaje|accesorios", "event_type": "trabajo|casual|formal"}
- Para crear perfil: SOLO si el usuario proporciona TODOS los datos necesarios (user_id, name, skin_tone, vein_color, jewelry_preference, sun_reaction, eye_color, hair_color, natural_lip_color, contrast_level)
- Para listar perfiles: list_profiles con {}
- Para mostrar perfil: show_profile con {"user_id": "id"}

REGLAS CRÍTICAS:
- NUNCA uses create_profile sin TODOS los argumentos requeridos
- Para "crear perfil" sin datos específicos, usa quick_palette en su lugar
- Para sueño usa quick_sleep_advice, no create_user_profile
- Para videojuegos usa géneros exactos como "Role-Playing"

HERRAMIENTAS DISPONIBLES:
{tools_catalog}

Responde SOLO con JSON válido:
{{ "tool_name": string|null, "server_name": string|null, "arguments": object, "reasoning_summary": string }}"""

def ask_claude_for_tool(user_message: str, tools_catalog: str) -> Dict[str, Any]:
    """Preguntar a Claude qué herramienta usar - MEJORADO CON ESTRATEGIAS INTELIGENTES"""
    prompt = f"""Herramientas disponibles por servidor:
{tools_catalog}

Mensaje del usuario: {user_message}

ESTRATEGIAS ESPECÍFICAS OBLIGATORIAS:
1. Para belleza/paletas SIN datos específicos del usuario: USA quick_palette
2. Para sueño SIN datos específicos: USA quick_sleep_advice  
3. Para videojuegos: USA géneros exactos ("Role-Playing" no "RPG")
4. NUNCA uses create_profile o create_user_profile sin datos completos

Analiza y selecciona la herramienta correcta con argumentos apropiados."""
    
    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1000,
            temperature=0.1,  # Más determinista
            system=TOOL_SELECTION_SYSTEM,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = response.content[0].text.strip()
        
        # Limpiar respuesta si viene envuelta en markdown
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()
        if text.startswith("```"):
            text = text.replace("```", "").strip()
        
        result = json.loads(text)
        
        # Debug: mostrar la selección
        print(f" Debug - Herramienta seleccionada: {result.get('tool_name')}")
        print(f" Debug - Argumentos: {result.get('arguments')}")
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"❌ Debug - JSON Error: {e}")
        print(f"❌ Debug - Raw text: {text if 'text' in locals() else 'No text'}")
        return {"tool_name": None, "server_name": None, "arguments": {}, "reasoning_summary": "Error parseando JSON del modelo."}
    except Exception as e:
        print(f"❌ Debug - General Error: {e}")
        return {"tool_name": None, "server_name": None, "arguments": {}, "reasoning_summary": "Error general en selección de herramienta."}

def ask_claude_for_final_answer(tool_output_text: str, user_message: str, server_name: str) -> str:
    """Generar respuesta final amigable - IGUAL QUE BEAUTY_CLIENT"""
    system_message = f"""Eres un experto con acceso a múltiples servidores especializados. La información viene del servidor {server_name}.

DIRECTRICES:
- Usa un tono cálido y profesional
- Convierte la salida técnica en respuestas naturales y útiles
- Da consejos prácticos cuando sea relevante
- Usa la información EXACTAMENTE como viene de la herramienta
- Menciona sutilmente el análisis especializado cuando sea relevante"""
    
    prompt = f"""Mensaje del usuario: {user_message}

Salida del servidor {server_name}:
{tool_output_text}

Convierte esta información en una respuesta natural y útil."""
    
    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1500,
            temperature=0.3,
            system=system_message,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text.strip()
    except Exception as e:
        return f"Error generando respuesta final: {e}"

def ask_claude_basic_fallback(user_message: str) -> str:
    """Respuesta general - IGUAL QUE BEAUTY_CLIENT"""
    global conversation_history
    
    system_message = """Eres un asistente inteligente que puede responder cualquier pregunta de manera precisa y útil. Respondes de forma natural y completa, sin limitaciones de tema.

Si la pregunta NO es sobre temas especializados (belleza, sueño, videojuegos), responde normalmente como un asistente general.
Si la pregunta SÍ es sobre temas especializados pero no tienes herramientas específicas, ofrece consejos generales.

Siempre sé útil, preciso y conversacional."""
    
    # Asegurar que conversation_history esté inicializada
    if conversation_history is None:
        conversation_history = []
    
    messages = conversation_history + [
        {"role": "user", "content": user_message}
    ]
    
    try:
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
        
        # Limitar historial para evitar que crezca demasiado
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]
            
        return reply
    except Exception as e:
        return f"Error en respuesta general: {e}"

class MultiServerManager:
    """Manager para múltiples conexiones MCP - BASADO EN BEAUTY_CLIENT"""
    
    def __init__(self):
        self.servers = {}
        self.server_configs = {}
        self.connected_servers = []
        
    async def initialize_servers(self) -> List[str]:
        """Inicializar todos los servidores disponibles"""
        if not CONFIG_FILE.exists():
            create_default_config()
        
        # Cargar configuración
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        self.server_configs = config.get("servers", {})
        connected = []
        
        for server_name, server_config in self.server_configs.items():
            if not server_config.get("enabled", True):
                continue
            
            try:
                # Verificar que el archivo del servidor existe
                server_file = Path(server_config["args"][0])
                if not server_file.exists():
                    print(f"❌ {server_name}: Archivo no encontrado - {server_file}")
                    continue
                
                # Probar conexión
                server_params = StdioServerParameters(
                    command=server_config["command"],
                    args=server_config["args"],
                    env=server_config.get("env", {}),
                    cwd=server_config.get("cwd", str(PROJECT_ROOT))
                )
                
                # Test de conexión rápido
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await asyncio.wait_for(session.initialize(), timeout=10.0)
                        
                        self.servers[server_name] = {
                            "params": server_params,
                            "config": server_config
                        }
                        connected.append(server_name)
                        print(f"✅ {server_name}: {server_config.get('description', 'Sin descripción')}")
                        
            except Exception as e:
                print(f"❌ {server_name}: Error - {str(e)}")
        
        self.connected_servers = connected
        return connected
    
    async def get_all_tools(self) -> str:
        """Obtener catálogo de todas las herramientas - IGUAL QUE BEAUTY_CLIENT"""
        tools_catalog = []
        
        for server_name in self.connected_servers:
            try:
                server_params = self.servers[server_name]["params"]
                
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        tools = await session.list_tools()
                        
                        tools_catalog.append(f"SERVIDOR: {server_name}")
                        for tool in tools.tools:
                            tools_catalog.append(f"- {tool.name}: {tool.description}")
                        tools_catalog.append("")
                        
            except Exception as e:
                print(f"Error obteniendo herramientas de {server_name}: {e}")
        
        return "\n".join(tools_catalog)
    
    async def call_tool_on_server(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Ejecutar herramienta en servidor específico - IGUAL QUE BEAUTY_CLIENT"""
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

# Función principal - ESTRUCTURA IGUAL QUE BEAUTY_CLIENT
async def main():
    """Función principal del cliente universal"""
    print("🌟 ASISTENTE INTELIGENTE UNIVERSAL")
    print("=" * 60)
    
    # Inicializar contexto
    init_context()
    
    # Inicializar manager de servidores
    server_manager = MultiServerManager()
    
    print("🔍 Conectando a servidores especializados...")
    try:
        connected_servers = await server_manager.initialize_servers()
    except Exception as e:
        print(f"❌ Error inicializando servidores: {e}")
        return
    
    if not connected_servers:
        print("❌ No se pudo conectar a ningún servidor MCP")
        return
    
    # Construir catálogo de herramientas
    print(" Construyendo catálogo de herramientas...")
    tools_catalog = await server_manager.get_all_tools()
    
    print("\n¡Bienvenido al Asistente Inteligente Universal!")
    print("-" * 60)
    print("Soy tu asistente personal que puede:")
    print(" Responder CUALQUIER pregunta general")
    
    if "beauty_server" in connected_servers:
        print("💄 Crear perfiles de belleza y generar paletas de colores")
    if "sleep_coach" in connected_servers:
        print("😴 Ayudarte con rutinas de sueño y análisis de patrones")
    if "game_server" in connected_servers:
        print("🎮 Analizar videojuegos y estadísticas de gaming")
    
    print("")
    print("Ejemplos de lo que puedo hacer:")
    print("  GENERAL: '¿Quién es Isaac Newton?', '¿Cómo funciona la fotosíntesis?'")
    if "beauty_server" in connected_servers:
        print("  BELLEZA: 'Crear perfil de usuario', 'Generar paleta de maquillaje'")
    if "sleep_coach" in connected_servers:
        print("  SUEÑO: 'Tengo insomnio', 'Crear rutina de sueño'")
    if "game_server" in connected_servers:
        print("  JUEGOS: 'Mejores juegos de RPG', 'Estadísticas de Nintendo'")
    print("  CONVERSACIÓN: '¿Qué tal tu día?', 'Cuéntame un chiste'")
    print("-" * 60)
    print("Comandos especiales: 'tools' (ver herramientas), 'exit' (salir)")
    print()
    print(f"✅ Sistema conectado a {len(connected_servers)} servidores especializados")
    print()
    
    ps = PromptSession()
    
    while True:
        try:
            user_msg = (await ps.prompt_async("> ")).strip()
            
            if not user_msg:
                continue
                
            if user_msg.lower() in ("exit", "quit", "salir"):
                print("🌟 ¡Hasta pronto! Espero haberte ayudado.")
                break
                
            if user_msg.lower() == "tools":
                print("\n🛠️ HERRAMIENTAS DISPONIBLES:")
                for server_name in connected_servers:
                    try:
                        server_params = server_manager.servers[server_name]["params"]
                        async with stdio_client(server_params) as (read, write):
                            async with ClientSession(read, write) as session:
                                await session.initialize()
                                tools = await session.list_tools()
                                print(f"\n {server_name.upper()}:")
                                for tool in tools.tools:
                                    print(f"  • {tool.name}: {tool.description}")
                    except Exception as e:
                        print(f"  Error listando herramientas de {server_name}: {e}")
                print()
                continue
            
            # Seleccionar herramienta con Claude - IGUAL QUE BEAUTY_CLIENT
            print("🔍 Analizando tu solicitud...")
            selection = ask_claude_for_tool(user_msg, tools_catalog)
            tool_name = selection.get("tool_name")
            server_name = selection.get("server_name")
            tool_args = selection.get("arguments", {}) or {}
            
            # Usar argumentos previos si están vacíos
            last_args = get_last_args_for_tool(tool_name)
            if tool_name and last_args and not tool_args:
                tool_args = last_args

            print(f"🎯 Herramienta seleccionada: {tool_name or 'ninguna'}")
            if server_name:
                print(f"🖥️ Servidor: {server_name}")
            print(f"💭 Razonamiento: {selection.get('reasoning_summary', 'N/A')}")
            
            tool_output_text = ""
            
            if tool_name and server_name and server_name in connected_servers:
                try:
                    print("⚡ Ejecutando herramienta especializada...")
                    tool_output_text = await server_manager.call_tool_on_server(
                        server_name, tool_name, tool_args
                    )
                    
                    # Debug: mostrar respuesta raw
                    print(f" Debug - Respuesta del servidor: {tool_output_text[:200]}...")
                    
                    # Verificar errores específicos
                    error_keywords = [
                        "validation error", "required property", "missing", "not found",
                        "campo requerido", "error ejecutando", "input validation error"
                    ]
                    
                    has_error = any(keyword in tool_output_text.lower() for keyword in error_keywords)
                    
                    if has_error:
                        print(f"⚠️ Error específico detectado en la herramienta {tool_name}")
                        print(f"⚠️ Error: {tool_output_text[:300]}")
                        
                        # Si es un error de create_profile, sugerir quick_palette
                        if tool_name == "create_profile":
                            print("🔄 Intentando con quick_palette en su lugar...")
                            fallback_args = {"palette_type": "ropa", "event_type": "casual"}
                            tool_output_text = await server_manager.call_tool_on_server(
                                server_name, "quick_palette", fallback_args
                            )
                            if not any(keyword in tool_output_text.lower() for keyword in error_keywords):
                                print("✅ Éxito con quick_palette")
                                final_answer = ask_claude_for_final_answer(tool_output_text, user_msg, server_name)
                            else:
                                print("⚠️ También falló quick_palette, usando respuesta general...")
                                final_answer = ask_claude_basic_fallback(user_msg)
                        else:
                            print("⚠️ Cambiando a respuesta general...")
                            final_answer = ask_claude_basic_fallback(user_msg)
                    else:
                        print("✅ Herramienta ejecutada exitosamente")
                        print("✨ Generando respuesta personalizada...")
                        final_answer = ask_claude_for_final_answer(tool_output_text, user_msg, server_name)
                        
                except Exception as e:
                    print(f"⚠️ Excepción ejecutando herramienta: {e}")
                    final_answer = ask_claude_basic_fallback(user_msg)
            else:
                if tool_name and server_name not in connected_servers:
                    print(f"⚠️ Servidor {server_name} no está conectado")
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
                "tool_used": tool_name,
                "server_used": server_name, 
                "arguments": tool_args,
                "tool_output": tool_output_text,
                "final_answer": final_answer,
            }
            
            save_to_context(entry)
            log_interaction(entry)
        
        except KeyboardInterrupt:
            print("\n\n🌟 ¡Hasta pronto!")
            break
        except Exception as e:
            print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    asyncio.run(main())