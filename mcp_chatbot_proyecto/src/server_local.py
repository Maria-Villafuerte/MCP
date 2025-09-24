#!/usr/bin/env python3
"""
Servidor Local MCP Expandido - Todas las funcionalidades de belleza, citas y git
Compatible con cliente MCP tradicional
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import mcp.types as types
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server

# Agregar src al path
import sys
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Importar controladores
from controllers.beauty_controller import BeautyController
from controllers.quotes_controller import QuotesController
from controllers.git_controller import GitController
from services.claude_service import ClaudeService
from models.logging_model import LoggingModel

# Inicializar servidor MCP
app = Server("local-mcp-expanded")
claude_service = None
beauty_controller = None
quotes_controller = None
git_controller = None
logging_model = None

# -------------------------------------------------------------------
# Inicialización del sistema
# -------------------------------------------------------------------
async def initialize_system():
    global claude_service, beauty_controller, quotes_controller, git_controller, logging_model
    try:
        load_dotenv()
        logging_model = LoggingModel()

        claude_service = ClaudeService()
        claude_available = await claude_service.initialize()
        if not claude_available:
            print("⚠️ Claude service no disponible - funcionalidad limitada")

        beauty_controller = BeautyController(claude_service, logging_model)
        quotes_controller = QuotesController(logging_model)
        git_controller = GitController(logging_model)

        await beauty_controller.initialize()
        await quotes_controller.initialize()
        await git_controller.initialize()

        print("✅ MCP Local Expandido inicializado")
    except Exception as e:
        print(f"❌ Error inicializando sistema: {e}")
        # No hacer raise para permitir funcionamiento parcial

# -------------------------------------------------------------------
# Definir herramientas disponibles (EXPANDIDO)
# -------------------------------------------------------------------
@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        # === HERRAMIENTAS PRINCIPALES ===
        types.Tool(
            name="chat",
            description="Enviar un mensaje al asistente Claude",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Mensaje para Claude API"}
                },
                "required": ["message"]
            }
        ),
        
        # === HERRAMIENTAS DE BELLEZA BÁSICAS ===
        types.Tool(
            name="create_profile",
            description="Crear un perfil de belleza completo",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID único del usuario"},
                    "name": {"type": "string", "description": "Nombre completo"},
                    "skin_tone": {"type": "string", "enum": ["clara", "media", "oscura"]},
                    "undertone": {"type": "string", "enum": ["frio", "calido", "neutro"], "default": "neutro"},
                    "eye_color": {"type": "string", "enum": ["azul", "verde", "cafe", "gris", "negro"]},
                    "hair_color": {"type": "string", "enum": ["rubio", "castano", "negro", "rojo", "gris"]},
                    "hair_type": {"type": "string", "enum": ["liso", "ondulado", "rizado"], "default": "liso"},
                    "style_preference": {"type": "string", "enum": ["clasico", "moderno", "bohemio", "minimalista", "romantico", "edgy"], "default": "moderno"}
                },
                "required": ["user_id", "name", "skin_tone", "eye_color", "hair_color"]
            }
        ),
        
        # === HERRAMIENTAS DE BELLEZA AVANZADAS ===
        types.Tool(
            name="list_beauty_profiles",
            description="Listar todos los perfiles de belleza disponibles",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        
        types.Tool(
            name="get_beauty_profile",
            description="Obtener detalles de un perfil de belleza específico",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID del usuario"}
                },
                "required": ["user_id"]
            }
        ),
        
        types.Tool(
            name="get_beauty_history",
            description="Obtener historial de paletas de un usuario",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID del usuario"}
                },
                "required": ["user_id"]
            }
        ),
        
        types.Tool(
            name="process_beauty_command",
            description="Procesar comando complejo de belleza (paletas, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Comando completo de belleza"}
                },
                "required": ["command"]
            }
        ),
        
        # === HERRAMIENTAS DE CITAS ===
        types.Tool(
            name="get_quote",
            description="Obtener una cita inspiracional",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Categoría opcional: motivacion, belleza, confianza, etc."}
                }
            }
        ),
        
        types.Tool(
            name="search_quotes",
            description="Buscar citas por palabra clave",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Término de búsqueda"},
                    "limit": {"type": "integer", "default": 5, "description": "Máximo número de resultados"}
                },
                "required": ["query"]
            }
        ),
        
        types.Tool(
            name="get_wisdom",
            description="Obtener sabiduría diaria inspiracional",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        
        types.Tool(
            name="process_quotes_command",
            description="Procesar comando complejo de citas",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Comando completo de citas"}
                },
                "required": ["command"]
            }
        ),
        
        # === HERRAMIENTAS DE GIT Y FILESYSTEM ===
        types.Tool(
            name="git_command",
            description="Ejecutar un comando de Git o filesystem genérico",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Comando completo"}
                },
                "required": ["command"]
            }
        ),
        
        types.Tool(
            name="read_file",
            description="Leer contenido de un archivo",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Nombre del archivo a leer"}
                },
                "required": ["filename"]
            }
        ),
        
        types.Tool(
            name="write_file",
            description="Escribir contenido a un archivo",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Nombre del archivo"},
                    "content": {"type": "string", "description": "Contenido a escribir"}
                },
                "required": ["filename", "content"]
            }
        ),
        
        types.Tool(
            name="list_files",
            description="Listar archivos en un directorio",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "default": ".", "description": "Directorio a listar"}
                }
            }
        ),
        
        types.Tool(
            name="git_status",
            description="Ver estado del repositorio git",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        
        types.Tool(
            name="git_add",
            description="Agregar archivos al staging area",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "default": ".", "description": "Archivo o patrón a agregar"}
                }
            }
        ),
        
        types.Tool(
            name="git_commit",
            description="Hacer commit con mensaje",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Mensaje del commit"}
                },
                "required": ["message"]
            }
        ),
        
        # === HERRAMIENTAS DE ESTADÍSTICAS Y MONITOREO ===
        types.Tool(
            name="get_server_stats",
            description="Obtener estadísticas del servidor y sistema",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        )
    ]

# -------------------------------------------------------------------
# Manejar llamadas a herramientas (EXPANDIDO)
# -------------------------------------------------------------------
@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        # === HERRAMIENTAS PRINCIPALES ===
        if name == "chat":
            msg = arguments["message"]
            if claude_service and claude_service.is_initialized:
                response = await claude_service.send_message(msg, context=[])
                return [types.TextContent(type="text", text=response or "Claude no proporcionó respuesta")]
            else:
                return [types.TextContent(type="text", text="❌ Claude API no disponible. Verifica ANTHROPIC_API_KEY")]

        # === HERRAMIENTAS DE BELLEZA ===
        elif name == "create_profile":
            if not beauty_controller:
                return [types.TextContent(type="text", text="❌ Beauty controller no disponible")]
            
            profile = beauty_controller.beauty_model.create_profile(arguments)
            return [types.TextContent(type="text", text=f"✅ Perfil de belleza creado: {profile.user_id} - {profile.name}")]

        elif name == "list_beauty_profiles":
            if not beauty_controller:
                return [types.TextContent(type="text", text="❌ Beauty controller no disponible")]
            
            profiles = beauty_controller.beauty_model.list_profiles()
            if not profiles:
                return [types.TextContent(type="text", text="ℹ️ No hay perfiles de belleza creados")]
            
            result = "👥 PERFILES DE BELLEZA DISPONIBLES:\n\n"
            for i, profile_id in enumerate(profiles, 1):
                result += f"{i}. {profile_id}\n"
            result += f"\n📊 Total: {len(profiles)} perfiles"
            return [types.TextContent(type="text", text=result)]

        elif name == "get_beauty_profile":
            if not beauty_controller:
                return [types.TextContent(type="text", text="❌ Beauty controller no disponible")]
            
            user_id = arguments["user_id"]
            profile = beauty_controller.beauty_model.load_profile(user_id)
            if not profile:
                return [types.TextContent(type="text", text=f"❌ Perfil '{user_id}' no encontrado")]
            
            result = f"👤 PERFIL DE BELLEZA: {profile.name.upper()}\n\n"
            result += f"🆔 ID: {profile.user_id}\n"
            result += f"🎨 Tono de piel: {profile.skin_tone.title()} ({profile.undertone.title()})\n"
            result += f"👁️ Color de ojos: {profile.eye_color.title()}\n"
            result += f"💇‍♀️ Cabello: {profile.hair_color.title()} ({profile.hair_type.title()})\n"
            result += f"✨ Estilo: {profile.style_preference.title()}\n"
            result += f"📅 Creado: {profile.created_at[:19].replace('T', ' ')}\n"
            
            return [types.TextContent(type="text", text=result)]

        elif name == "get_beauty_history":
            if not beauty_controller:
                return [types.TextContent(type="text", text="❌ Beauty controller no disponible")]
            
            user_id = arguments["user_id"]
            profile = beauty_controller.beauty_model.load_profile(user_id)
            if not profile:
                return [types.TextContent(type="text", text=f"❌ Perfil '{user_id}' no encontrado")]
            
            palettes = beauty_controller.beauty_model.load_user_palettes(user_id)
            if not palettes:
                return [types.TextContent(type="text", text=f"ℹ️ No hay historial de paletas para {user_id}")]
            
            result = f"📈 HISTORIAL DE PALETAS - {profile.name.upper()}\n\n"
            for i, palette in enumerate(palettes[:10], 1):  # Últimas 10
                date = palette.created_at[:10]
                result += f"{i:2d}. {date} | {palette.palette_type.title():12} | {palette.event_type.title():10} | {len(palette.colors)} colores\n"
            
            if len(palettes) > 10:
                result += f"\n... y {len(palettes) - 10} paletas más"
            result += f"\n📊 Total: {len(palettes)} paletas generadas"
            
            return [types.TextContent(type="text", text=result)]

        elif name == "process_beauty_command":
            if not beauty_controller:
                return [types.TextContent(type="text", text="❌ Beauty controller no disponible")]
            
            cmd = arguments["command"]
            response = await beauty_controller.handle_command(cmd)
            return [types.TextContent(type="text", text=response or "✅ Comando de belleza procesado")]

        # === HERRAMIENTAS DE CITAS ===
        elif name == "get_quote":
            if not quotes_controller:
                return [types.TextContent(type="text", text="❌ Quotes controller no disponible")]
            
            category = arguments.get("category")
            cmd = f"/quotes get {category}" if category else "/quotes get"
            response = await quotes_controller.handle_command(cmd)
            return [types.TextContent(type="text", text=response or "❌ No se pudo obtener cita")]

        elif name == "search_quotes":
            if not quotes_controller:
                return [types.TextContent(type="text", text="❌ Quotes controller no disponible")]
            
            query = arguments["query"]
            cmd = f"/quotes search {query}"
            response = await quotes_controller.handle_command(cmd)
            return [types.TextContent(type="text", text=response or f"❌ No se encontraron citas para '{query}'")]

        elif name == "get_wisdom":
            if not quotes_controller:
                return [types.TextContent(type="text", text="❌ Quotes controller no disponible")]
            
            response = await quotes_controller.handle_command("/quotes wisdom")
            return [types.TextContent(type="text", text=response or "❌ No se pudo obtener sabiduría")]

        elif name == "process_quotes_command":
            if not quotes_controller:
                return [types.TextContent(type="text", text="❌ Quotes controller no disponible")]
            
            cmd = arguments["command"]
            response = await quotes_controller.handle_command(cmd)
            return [types.TextContent(type="text", text=response or "✅ Comando de citas procesado")]

        # === HERRAMIENTAS DE GIT Y FILESYSTEM ===
        elif name == "git_command":
            if not git_controller:
                return [types.TextContent(type="text", text="❌ Git controller no disponible")]
            
            cmd = arguments["command"]
            response = await git_controller.handle_command(cmd)
            return [types.TextContent(type="text", text=response or "✅ Comando ejecutado")]

        elif name == "read_file":
            if not git_controller:
                return [types.TextContent(type="text", text="❌ Git controller no disponible")]
            
            filename = arguments["filename"]
            response = await git_controller.handle_command(f"/fs read {filename}")
            return [types.TextContent(type="text", text=response or "❌ No se pudo leer archivo")]

        elif name == "write_file":
            if not git_controller:
                return [types.TextContent(type="text", text="❌ Git controller no disponible")]
            
            filename = arguments["filename"]
            content = arguments["content"]
            response = await git_controller.handle_command(f"/fs write {filename} {content}")
            return [types.TextContent(type="text", text=response or "✅ Archivo escrito")]

        elif name == "list_files":
            if not git_controller:
                return [types.TextContent(type="text", text="❌ Git controller no disponible")]
            
            directory = arguments.get("directory", ".")
            response = await git_controller.handle_command(f"/fs list {directory}")
            return [types.TextContent(type="text", text=response or "❌ No se pudo listar directorio")]

        elif name == "git_status":
            if not git_controller:
                return [types.TextContent(type="text", text="❌ Git controller no disponible")]
            
            response = await git_controller.handle_command("/git status")
            return [types.TextContent(type="text", text=response or "❌ Error en git status")]

        elif name == "git_add":
            if not git_controller:
                return [types.TextContent(type="text", text="❌ Git controller no disponible")]
            
            filename = arguments.get("filename", ".")
            response = await git_controller.handle_command(f"/git add {filename}")
            return [types.TextContent(type="text", text=response or "✅ Archivos agregados")]

        elif name == "git_commit":
            if not git_controller:
                return [types.TextContent(type="text", text="❌ Git controller no disponible")]
            
            message = arguments["message"]
            response = await git_controller.handle_command(f'/git commit "{message}"')
            return [types.TextContent(type="text", text=response or "✅ Commit realizado")]

        # === ESTADÍSTICAS ===
        elif name == "get_server_stats":
            stats = []
            
            if beauty_controller:
                profiles = beauty_controller.beauty_model.list_profiles()
                stats.append(f"👥 Perfiles de belleza: {len(profiles)}")
            
            if logging_model:
                try:
                    beauty_stats = logging_model.get_beauty_stats()
                    mcp_stats = logging_model.get_mcp_stats()
                    stats.append(f"🎨 Interacciones de belleza: {beauty_stats.get('total_interactions', 0)}")
                    stats.append(f"🔧 Interacciones MCP: {mcp_stats.get('total_interactions', 0)}")
                except:
                    stats.append("📊 Estadísticas no disponibles")
            
            claude_status = "✅ Conectado" if (claude_service and claude_service.is_initialized) else "❌ Desconectado"
            stats.append(f"🤖 Claude API: {claude_status}")
            
            result = "📊 ESTADÍSTICAS DEL SERVIDOR:\n\n" + "\n".join(stats)
            return [types.TextContent(type="text", text=result)]

        else:
            return [types.TextContent(type="text", text=f"❌ Herramienta desconocida: {name}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"❌ Error ejecutando {name}: {str(e)}")]

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
async def main():
    await initialize_system()
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="local-mcp-expanded",
                server_version="2.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    print("🚀 Iniciando Servidor Local MCP Expandido...")
    print("🎨 Sistema de Belleza Completo")
    print("💬 Citas Inspiracionales Avanzadas") 
    print("📁 Gestión Completa de Archivos y Git")
    print("🤖 Claude API Integration")
    print("📊 Sistema de Monitoreo y Estadísticas")
    asyncio.run(main())