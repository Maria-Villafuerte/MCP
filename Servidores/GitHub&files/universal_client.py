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

print(f" Directorio actual: {CURRENT_DIR}")
print(f" Raíz del proyecto: {PROJECT_ROOT}")

# Configuración
CONFIG_FILE = PROJECT_ROOT / "universal_servers.yaml"
ANTHROPIC_MODEL = "claude-3-5-haiku-20241022"

# Archivos de contexto
DATA_DIR = PROJECT_ROOT / "Data"
CONTEXT_FILE = DATA_DIR / "universal_context.json"
LOG_FILE = DATA_DIR / "universal_log.txt"

# Buscar .env
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
    raise SystemExit("❌ Missing .env file with ANTHROPIC_API_KEY")

if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("❌ Missing ANTHROPIC_API_KEY in .env")

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Crear directorios necesarios
DATA_DIR.mkdir(exist_ok=True)

# Inicializar contexto
if not CONTEXT_FILE.exists():
    with open(CONTEXT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "active_servers": {},
            "history": [],
            "last_tool_memory": {},
            "session_info": {
                "created_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
                "total_interactions": 0
            }
        }, f, ensure_ascii=False, indent=2)

# Crear configuración por defecto
if not CONFIG_FILE.exists():
    default_config = {
        "servers": {
            "git_server": {
                "name": "Git Server",
                "command": "python",
                "args": [str(PROJECT_ROOT / "git_server.py")],
                "env": {},
                "cwd": str(PROJECT_ROOT),
                "description": "Servidor para operaciones Git"
            },
            "filesystem_server": {
                "name": "Filesystem Server", 
                "command": "python",
                "args": [str(PROJECT_ROOT / "filesystem_server.py")],
                "env": {},
                "cwd": str(PROJECT_ROOT),
                "description": "Servidor para operaciones del sistema de archivos"
            }
        }
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)

conversation_history: List[Dict[str, str]] = []

# Funciones de contexto
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
        print(f"⚠️ Error guardando contexto: {e}")

def get_last_args_for_tool(tool_name: Optional[str]) -> Optional[Dict[str, Any]]:
    """Obtener últimos argumentos para una herramienta"""
    if not tool_name:
        return None
    try:
        with open(CONTEXT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["last_tool_memory"].get(tool_name)
    except FileNotFoundError:
        return None

def log_interaction(entry: Dict[str, Any]):
    """Registrar interacción en log"""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"⚠️ Error guardando log: {e}")

# Sistema de prompts inteligente
TOOL_SELECTION_SYSTEM = """Eres un asistente especializado en operaciones Git y sistema de archivos. Tu trabajo es analizar las solicitudes del usuario y seleccionar la herramienta correcta.

HERRAMIENTAS GIT DISPONIBLES:
- git_init: Inicializar repositorio Git
- git_status: Ver estado del repositorio  
- git_add: Agregar archivos al staging area
- git_commit: Hacer commit de cambios
- git_branch_create: Crear nueva rama
- git_checkout: Cambiar de rama
- git_log: Ver historial de commits
- git_remote_add: Agregar repositorio remoto
- git_push: Subir cambios al repositorio remoto
- git_pull: Descargar cambios del repositorio remoto
- git_diff: Ver diferencias entre commits/archivos
- git_ls_files: Listar archivos tracked
- git_clone: Clonar repositorio

HERRAMIENTAS FILESYSTEM DISPONIBLES:
- fs_list_dir: Listar contenido de directorio
- fs_read_file: Leer archivo de texto
- fs_write_file: Escribir archivo
- fs_append_file: Agregar contenido a archivo
- fs_mkdir: Crear directorio
- fs_remove: Eliminar archivo o directorio
- fs_move: Mover/renombrar archivos
- fs_copy: Copiar archivos/directorios
- fs_stat: Obtener metadatos de archivo
- fs_glob: Buscar archivos con patrón
- fs_find_text: Buscar texto en archivos
- fs_replace_text: Reemplazar texto en archivos
- fs_get_cwd: Obtener directorio actual
- fs_set_cwd: Cambiar directorio actual

REGLAS DE SELECCIÓN:
- Para operaciones Git: "inicializar repo", "hacer commit", "ver estado git", "crear rama", "subir cambios"
- Para archivos: "crear carpeta", "leer archivo", "copiar archivo", "buscar texto", "listar archivos"
- Si menciona "git" o "repositorio" -> herramientas git_*
- Si menciona "archivo", "carpeta", "directorio" -> herramientas fs_*
- Si NO coincide claramente, usa "tool_name": null

ARGUMENTOS IMPORTANTES:
- Para rutas Git: usa "path" (ej: ".", "/ruta/al/repo")
- Para archivos: usa "path" para rutas de archivos/directorios
- Para git_add: usa "patterns" como lista (ej: [".", "*.py"])
- Para git_commit: incluye "message"
- Para fs_write_file: incluye "content" y "path"

Responde SOLO con JSON:
{ "tool_name": string|null, "arguments": object, "reasoning_summary": string }"""

def build_tools_catalog(all_tools) -> str:
    """Construir catálogo completo de herramientas"""
    lines = []
    git_tools = []
    fs_tools = []
    
    for server_name, tools_resp in all_tools.items():
        for tool in tools_resp.tools:
            schema_str = json.dumps(tool.inputSchema, ensure_ascii=False, indent=2)
            tool_info = f"- name: {tool.name}\n  server: {server_name}\n  desc: {tool.description}\n  schema: {schema_str}"
            
            if tool.name.startswith("git_"):
                git_tools.append(tool_info)
            elif tool.name.startswith("fs_"):
                fs_tools.append(tool_info)
            else:
                lines.append(tool_info)
    
    result = ""
    if git_tools:
        result += "=== HERRAMIENTAS GIT ===\n" + "\n".join(git_tools) + "\n\n"
    if fs_tools:
        result += "=== HERRAMIENTAS FILESYSTEM ===\n" + "\n".join(fs_tools) + "\n\n"
    if lines:
        result += "=== OTRAS HERRAMIENTAS ===\n" + "\n".join(lines)
        
    return result

def ask_claude_for_tool(user_message: str, tools_catalog: str) -> Dict[str, Any]:
    """Preguntar a Claude qué herramienta usar"""
    prompt = f"""Herramientas disponibles:
{tools_catalog}

Mensaje del usuario: {user_message}

Analiza el mensaje y selecciona la herramienta más apropiada. Considera el contexto de Git vs operaciones de archivos.
Devuelve SOLO JSON con: tool_name, arguments, reasoning_summary.
"""
    
    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1000,
            temperature=0.2,
            system=TOOL_SELECTION_SYSTEM,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = response.content[0].text.strip()
        return json.loads(text)
    except Exception as e:
        print(f"⚠️ Error en selección de herramienta: {e}")
        return {"tool_name": None, "arguments": {}, "reasoning_summary": "Error en análisis del modelo."}

def ask_claude_for_final_answer(tool_output_text: str, user_message: str, tool_used: str = None) -> str:
    """Generar respuesta final amigable"""
    system_message = """Eres un asistente experto en Git y manejo de archivos. Convierte la salida técnica de las herramientas en respuestas naturales y útiles.

DIRECTRICES:
- Usa un tono profesional pero amigable
- Explica qué se hizo de manera clara
- Si hay errores, explica qué pasó y sugiere soluciones
- Para Git: explica el estado del repositorio, commits, ramas, etc.
- Para archivos: confirma operaciones realizadas, muestra contenido relevante
- Usa la información EXACTAMENTE como viene de la herramienta
- Si la salida contiene rutas, hazlas más legibles"""
    
    context = f"Herramienta usada: {tool_used}\n" if tool_used else ""
    prompt = f"""Mensaje original del usuario: {user_message}

{context}Salida de la herramienta:
{tool_output_text}

Convierte esta información en una respuesta natural y útil para el usuario."""
    
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
        return f"Operación completada. Resultado técnico: {tool_output_text}"

def ask_claude_basic_fallback(user_message: str) -> str:
    """Respuesta general cuando no hay herramienta específica disponible"""
    system_message = """Eres un asistente inteligente que puede responder cualquier pregunta de manera precisa y útil.

Si la pregunta NO es sobre Git o archivos, responde normalmente como un asistente general.
Si la pregunta SÍ es sobre Git/archivos pero no tienes herramientas disponibles, ofrece consejos generales.

Siempre sé útil, preciso y conversacional."""
    
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
        return reply
    except Exception as e:
        return f"Lo siento, no pude procesar tu solicitud. Error: {e}"

# Función principal
async def main():
    """Función principal del cliente universal"""
    print(" CLIENTE UNIVERSAL MCP - GIT & FILESYSTEM")
    print("=" * 60)
    
    # Cargar configuración
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error cargando configuración: {e}")
        return
    
    print("🔧 Conectando a servidores MCP...")
    
    # Conectar a múltiples servidores
    active_sessions = {}
    all_tools = {}
    
    for server_key, server_config in cfg["servers"].items():
        try:
            cmd = server_config["command"]
            args = server_config.get("args", [])
            env = server_config.get("env", {})
            
            print(f"   📡 Conectando a {server_config['name']}...")
            server_params = StdioServerParameters(command=cmd, args=args, env=env)
            
            # Crear contexto asíncrono para cada servidor
            read, write = await stdio_client(server_params).__aenter__()
            session = await ClientSession(read, write).__aenter__()
            await session.initialize()
            
            tools = await session.list_tools()
            active_sessions[server_key] = session
            all_tools[server_key] = tools
            
            print(f"   ✅ {server_config['name']}: {len(tools.tools)} herramientas")
            
        except Exception as e:
            print(f"   ⚠️ Error conectando {server_key}: {e}")
            continue
    
    if not active_sessions:
        print("❌ No se pudo conectar a ningún servidor")
        return
    
    # Crear catálogo unificado de herramientas
    tools_catalog = build_tools_catalog(all_tools)
    all_tool_names = {}  # tool_name -> (server_key, session)
    
    for server_key, tools_resp in all_tools.items():
        for tool in tools_resp.tools:
            all_tool_names[tool.name] = (server_key, active_sessions[server_key])
    
    print(f"\n✅ Cliente universal listo. Servidores activos: {len(active_sessions)}")
    print(f" Herramientas totales disponibles: {len(all_tool_names)}")
    
    print("\n🎯 ¡Bienvenido al Asistente Universal!")
    print("-" * 60)
    print("Puedo ayudarte con:")
    print("🔄 OPERACIONES GIT: crear repos, commits, ramas, push/pull")
    print(" GESTIÓN DE ARCHIVOS: crear, leer, copiar, buscar, organizar")
    print(" PREGUNTAS GENERALES: cualquier tema que necesites")
    print("")
    print("Ejemplos de comandos en lenguaje natural:")
    print("  'inicializar un repositorio git aquí'")
    print("  'ver el estado de mi repositorio'")
    print("  'crear un archivo llamado readme.md'")
    print("  'listar todos los archivos python'")
    print("  'hacer commit con mensaje inicial'")
    print("  'buscar texto en todos los archivos'")
    print("-" * 60)
    print("Comandos: 'tools' (ver herramientas), 'servers' (estado), 'exit' (salir)")
    print()
    
    ps = PromptSession()
    
    try:
        while True:
            try:
                user_msg = (await ps.prompt_async(" > ")).strip()
                
                if not user_msg:
                    continue
                    
                if user_msg.lower() in ("exit", "quit", "salir"):
                    print("👋 ¡Hasta pronto! Espero haber sido útil.")
                    break
                    
                if user_msg.lower() == "tools":
                    print("\n HERRAMIENTAS DISPONIBLES:")
                    for server_key, tools_resp in all_tools.items():
                        print(f"\n  🔧 {cfg['servers'][server_key]['name']}:")
                        for tool in tools_resp.tools:
                            print(f"    • {tool.name}: {tool.description}")
                    print()
                    continue
                    
                if user_msg.lower() == "servers":
                    print(f"\n🖥️ ESTADO DE SERVIDORES:")
                    for server_key, session in active_sessions.items():
                        name = cfg["servers"][server_key]["name"]
                        tool_count = len(all_tools[server_key].tools)
                        print(f"  ✅ {name}: {tool_count} herramientas activas")
                    print()
                    continue
                
                # Analizar solicitud
                print("🔍 Analizando tu solicitud...")
                selection = ask_claude_for_tool(user_msg, tools_catalog)
                tool_name = selection.get("tool_name")
                tool_args = selection.get("arguments", {}) or {}
                
                # Usar argumentos previos si están vacíos
                last_args = get_last_args_for_tool(tool_name)
                if tool_name and last_args and not tool_args:
                    tool_args = last_args

                print(f"🎯 Herramienta: {tool_name or 'ninguna'}")
                print(f"💭 Análisis: {selection.get('reasoning_summary', 'N/A')}")
                
                tool_output_text = ""
                server_used = None
                
                if tool_name and tool_name in all_tool_names:
                    try:
                        server_key, session = all_tool_names[tool_name]
                        server_used = cfg["servers"][server_key]["name"]
                        
                        print(f"⚙️ Ejecutando en {server_used}...")
                        result = await session.call_tool(name=tool_name, arguments=tool_args)
                        collected = [c.text for c in result.content if c.type == "text"]
                        tool_output_text = "\n".join(collected).strip()
                        
                        print("✨ Generando respuesta personalizada...")
                        final_answer = ask_claude_for_final_answer(tool_output_text, user_msg, tool_name)
                        
                    except Exception as e:
                        final_answer = f"❌ Error ejecutando {tool_name}: {e}"
                else:
                    print(" Respondiendo como asistente general...")
                    final_answer = ask_claude_basic_fallback(user_msg)

                print("\n" + "="*60)
                print(" RESPUESTA:")
                if server_used:
                    print(f"🔧 (usando {server_used})")
                print(final_answer)
                print("="*60 + "\n")

                # Guardar contexto
                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "user": user_msg,
                    "tool_used": tool_name,
                    "server_used": server_used,
                    "arguments": tool_args,
                    "tool_output": tool_output_text,
                    "final_answer": final_answer,
                }
                
                save_to_context(entry)
                log_interaction(entry)
                
            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta pronto!")
                break
            except Exception as e:
                print(f"❌ Error inesperado: {e}")
                
    finally:
        # Cerrar todas las sesiones
        print("🔌 Cerrando conexiones...")
        for session in active_sessions.values():
            try:
                await session.__aexit__(None, None, None)
            except:
                pass

if __name__ == "__main__":
    asyncio.run(main())