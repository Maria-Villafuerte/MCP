import os, json, yaml, asyncio, re
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

# CONFIGURACIÓN ROBUSTA DE RUTAS PARA WINDOWS Y ESTRUCTURA DE CARPETAS
# Obtener directorio actual del script
CURRENT_DIR = Path(__file__).parent.absolute()  # Clientes/
PROJECT_ROOT = CURRENT_DIR.parent.absolute()    # MCP/

print(f" Directorio actual: {CURRENT_DIR}")
print(f" Raíz del proyecto: {PROJECT_ROOT}")

# Configuración con rutas absolutas
CONFIG_FILE = PROJECT_ROOT / "beauty_servers.yaml"
SERVER_KEY = "beauty_server"
ANTHROPIC_MODEL = "claude-3-5-haiku-20241022"

# Archivos de contexto con rutas absolutas
DATA_DIR = PROJECT_ROOT / "Data"
CONTEXT_FILE = DATA_DIR / "beauty_context.json"
LOG_FILE = DATA_DIR / "beauty_log.txt"

# Archivos del servidor
SERVIDOR_DIR = PROJECT_ROOT / "Servidores" / "Local"
BEAUTY_SERVER_FILE = SERVIDOR_DIR / "beauty_server.py"
METODOS_SERVER_FILE = SERVIDOR_DIR / "metodos_server.py"

# Buscar .env en múltiples ubicaciones
ENV_LOCATIONS = [
    PROJECT_ROOT / ".env",        # MCP/.env (correcto)
    CURRENT_DIR / ".env",         # Clientes/.env (actual)
    Path(".env"),                 # Directorio actual
]

env_loaded = False
for env_path in ENV_LOCATIONS:
    if env_path.exists():
        print(f"✅ Encontrado .env en: {env_path}")
        load_dotenv(env_path)
        env_loaded = True
        break

if not env_loaded:
    print("❌ No se encontró archivo .env en ninguna ubicación")
    print(" Ubicaciones buscadas:")
    for loc in ENV_LOCATIONS:
        print(f"   - {loc}")
    print("\n Crea un archivo .env en la raíz del proyecto (MCP/.env) con:")
    print("   ANTHROPIC_API_KEY=tu_api_key_aqui")

# Verificar API Key
if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("❌ Missing ANTHROPIC_API_KEY in .env")

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Crear directorios necesarios
DATA_DIR.mkdir(exist_ok=True)

# Inicializar archivo de contexto
if not CONTEXT_FILE.exists():
    with open(CONTEXT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "server": SERVER_KEY, 
                "history": [], 
                "last_tool_memory": {}, 
                "last_list": None,
                "session_info": {
                    "created_at": datetime.now().isoformat(),
                    "last_active": datetime.now().isoformat(),
                    "total_interactions": 0
                }
            },
            f, ensure_ascii=False, indent=2
        )

# Crear configuración por defecto con rutas absolutas
if not CONFIG_FILE.exists():
    default_config = {
        "servers": {
            "beauty_server": {
                "command": "python",
                "args": [str(BEAUTY_SERVER_FILE)],  # Ruta absoluta
                "env": {},
                "cwd": str(PROJECT_ROOT)  # Working directory en la raíz
            }
        }
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)

conversation_history: List[Dict[str, str]] = []

# Funciones de contexto (actualizadas para usar rutas absolutas)
def save_to_context(entry: Dict[str, Any]):
    """Guardar entrada en el contexto"""
    with open(CONTEXT_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data["history"].append(entry)
        if entry.get("tool_used") and entry.get("arguments"):
            data["last_tool_memory"][entry["tool_used"]] = entry["arguments"]
        if entry.get("last_list"):
            data["last_list"] = entry["last_list"]
        f.seek(0)
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.truncate()

def get_last_args_for_tool(tool_name: Optional[str]) -> Optional[Dict[str, Any]]:
    """Obtener últimos argumentos usados para una herramienta específica"""
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

# Prompts del sistema (sin cambios)
TOOL_SELECTION_SYSTEM = """Eres un asistente especializado en belleza y paletas de colores. Tu trabajo es analizar las solicitudes del usuario y seleccionar la herramienta correcta del servidor MCP de belleza.

HERRAMIENTAS DISPONIBLES:
- create_profile: Crear un nuevo perfil de belleza
- show_profile: Mostrar información de un perfil específico  
- list_profiles: Listar todos los perfiles existentes
- delete_profile: Eliminar un perfil específico
- generate_palette: Generar paleta personalizada basada en perfil
- quick_palette: Generar paleta rápida sin perfil específico
- export_data: Exportar datos de usuario

REGLAS:
- Si el usuario quiere "crear usuario/perfil", usa create_profile
- Si pregunta por "ver/mostrar perfil", usa show_profile
- Si quiere "listar/ver todos los perfiles", usa list_profiles  
- Si quiere "eliminar/borrar perfil", usa delete_profile
- Si quiere "generar/crear paleta" con perfil específico, usa generate_palette
- Si quiere "paleta rápida" o sin mencionar perfil, usa quick_palette
- Si quiere "exportar datos", usa export_data
- Si NO coincide con ninguna herramienta, usa "tool_name": null

Responde SOLO con JSON:
{ "tool_name": string|null, "arguments": object, "reasoning_summary": string }"""

def build_tools_catalog(tools_resp) -> str:
    """Construir catálogo de herramientas disponibles"""
    lines = []
    for t in tools_resp.tools:
        schema_str = json.dumps(t.inputSchema, ensure_ascii=False, indent=2)
        lines.append(f"- name: {t.name}\n  desc: {t.description}\n  schema: {schema_str}")
    return "\n".join(lines)

def ask_claude_for_tool(user_message: str, tools_catalog: str) -> Dict[str, Any]:
    """Preguntar a Claude qué herramienta usar"""
    prompt = f"""Herramientas disponibles para belleza:
{tools_catalog}

Mensaje del usuario: {user_message}

Analiza el mensaje y selecciona la herramienta más apropiada. Devuelve SOLO JSON con: tool_name, arguments, reasoning_summary.
"""
    
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1000,
        temperature=0.2,
        system=TOOL_SELECTION_SYSTEM,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    text = response.content[0].text.strip()
    try:
        return json.loads(text)
    except Exception:
        return {"tool_name": None, "arguments": {}, "reasoning_summary": "No se pudo parsear la respuesta del modelo."}

def ask_claude_for_final_answer(tool_output_text: str, user_message: str) -> str:
    """Pedir a Claude que genere respuesta final amigable"""
    system_message = """Eres un experto en belleza y paletas de colores. Convierte la salida técnica de las herramientas en respuestas naturales y útiles para el usuario. 

DIRECTRICES:
- Usa un tono cálido y profesional
- Explica los colores de manera descriptiva y atractiva
- Da consejos prácticos cuando sea relevante
- Usa la información EXACTAMENTE como viene de la herramienta
- Si hay colores con códigos hex, menciona tanto el código como el nombre descriptivo"""
    
    prompt = f"""Mensaje original del usuario: {user_message}

Salida de la herramienta:
{tool_output_text}

Convierte esta información en una respuesta natural y útil para el usuario."""
    
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1500,
        temperature=0.3,
        system=system_message,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.content[0].text.strip()

def ask_claude_basic_fallback(user_message: str) -> str:
    """Respuesta general cuando no hay herramienta de belleza disponible"""
    system_message = """Eres un asistente inteligente que puede responder cualquier pregunta de manera precisa y útil. Respondes de forma natural y completa, sin limitaciones de tema.

Si la pregunta NO es sobre belleza o paletas de colores, responde normalmente como un asistente general.
Si la pregunta SÍ es sobre belleza pero no tienes herramientas específicas, ofrece consejos generales de belleza.

Siempre sé útil, preciso y conversacional."""
    
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
    """Función principal del cliente"""
    print(" SISTEMA DE BELLEZA MCP - CLIENTE INTELIGENTE")
    print("=" * 60)
    
    # Verificar estructura de archivos con rutas absolutas
    print(" Verificando estructura de archivos...")
    
    files_to_check = [
        (BEAUTY_SERVER_FILE, "Servidor de belleza"),
        (METODOS_SERVER_FILE, "Métodos del servidor"),
        (CONFIG_FILE, "Configuración"),
    ]
    
    missing_files = []
    for file_path, description in files_to_check:
        if file_path.exists():
            print(f"✅ {description}: {file_path}")
        else:
            print(f"❌ FALTA {description}: {file_path}")
            missing_files.append((file_path, description))
    
    if missing_files:
        print(f"\n❌ ERROR: Archivos faltantes encontrados")
        print(" Estructura actual detectada:")
        print(f"   Raíz: {PROJECT_ROOT}")
        print(f"   Cliente: {CURRENT_DIR}")
        print(f"   Data: {DATA_DIR}")
        print(f"   Servidores: {SERVIDOR_DIR}")
        return
    
    print("✅ Todos los archivos encontrados correctamente")
    
    # Cargar configuración
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        
        if "servers" not in cfg or SERVER_KEY not in cfg["servers"]:
            raise SystemExit(f"❌ Servidor '{SERVER_KEY}' no encontrado en {CONFIG_FILE}")
            
    except Exception as e:
        print(f"❌ Error cargando configuración: {e}")
        return
    
    s = cfg["servers"][SERVER_KEY]
    cmd, args, env = s["command"], s.get("args", []), s.get("env", {})
    
    print(f" Intentando conectar al servidor MCP...")
    print(f"   Comando: {cmd} {' '.join(args)}")
    print(f"   Directorio de trabajo: {s.get('cwd', '.')}")

    server_params = StdioServerParameters(command=cmd, args=args, env=env)
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print(" Conectando al servidor MCP...")
                await session.initialize()
                
                print("\n ¡Bienvenido al Asistente Inteligente de Belleza!")
                print("-" * 60)
                print("Soy tu asistente personal que puede:")
                print(" Responder CUALQUIER pregunta general")
                print(" Crear perfiles de belleza personalizados")
                print(" Generar paletas de colores especializadas")
                print(" Manejar temas de moda, maquillaje y estilo")
                print("")
                print("Ejemplos de lo que puedo hacer:")
                print("  GENERAL: '¿Quién es Isaac Newton?', '¿Cómo funciona la fotosíntesis?'")
                print("  BELLEZA: 'Crear usuario', 'Generar paleta de maquillaje'")
                print("  CONVERSACIÓN: '¿Qué tal tu día?', 'Cuéntame un chiste'")
                print("-" * 60)
                print("Comandos especiales: 'tools' (ver herramientas), 'exit' (salir)")
                print()
                
                tools = await session.list_tools()
                tool_names = [t.name for t in tools.tools]
                tools_catalog = build_tools_catalog(tools)
                
                print(f"✅ Servidor conectado correctamente. Herramientas disponibles: {len(tool_names)}")
                print(f" Trabajando desde: {PROJECT_ROOT}")
                print()
                
                ps = PromptSession()
                
                while True:
                    try:
                        user_msg = (await ps.prompt_async("> ")).strip()
                        
                        if not user_msg:
                            continue
                            
                        if user_msg.lower() in ("exit", "quit", "salir"):
                            print(" ¡Hasta pronto! Espero haberte ayudado con tus paletas de colores.")
                            break
                            
                        if user_msg.lower() == "tools":
                            print("\n HERRAMIENTAS DISPONIBLES:")
                            for tool in tools.tools:
                                print(f"  • {tool.name}: {tool.description}")
                            print()
                            continue
                        
                        # Seleccionar herramienta con Claude
                        print(" Analizando tu solicitud...")
                        selection = ask_claude_for_tool(user_msg, tools_catalog)
                        tool_name = selection.get("tool_name")
                        tool_args = selection.get("arguments", {}) or {}
                        
                        # Usar argumentos previos si están vacíos
                        last_args = get_last_args_for_tool(tool_name)
                        if tool_name and last_args and not tool_args:
                            tool_args = last_args

                        print(f" Herramienta seleccionada: {tool_name or 'ninguna'}")
                        print(f" Razonamiento: {selection.get('reasoning_summary', 'N/A')}")
                        
                        tool_output_text = ""
                        
                        if tool_name and tool_name in tool_names:
                            try:
                                print(" Ejecutando herramienta...")
                                result = await session.call_tool(name=tool_name, arguments=tool_args)
                                collected = [c.text for c in result.content if c.type == "text"]
                                tool_output_text = "\n".join(collected).strip()
                                
                                print(" Generando respuesta personalizada...")
                                final_answer = ask_claude_for_final_answer(tool_output_text, user_msg)
                            except Exception as e:
                                final_answer = f"❌ Error ejecutando {tool_name}: {e}"
                        else:
                            print(" No se encontró herramienta de belleza específica.")
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

    except Exception as e:
        print(f"\n❌ ERROR DE CONEXIÓN:")
        print(f"   {str(e)}")
        print(f"\n DIAGNÓSTICO Y SOLUCIONES:")
        print(f"    Raíz del proyecto: {PROJECT_ROOT}")
        print(f"    Servidor esperado: {BEAUTY_SERVER_FILE}")
        print(f"    Métodos esperados: {METODOS_SERVER_FILE}")
        print(f"\n Pasos para resolver:")
        print(f"   1. Verifica que los archivos existan en las rutas mostradas")
        print(f"   2. Instala dependencias: pip install -r requirements.txt")
        print(f"   3. Verifica tu API key en .env")
        print(f"   4. Ejecuta desde cualquier ubicación - las rutas son absolutas")
        return

if __name__ == "__main__":
    asyncio.run(main())