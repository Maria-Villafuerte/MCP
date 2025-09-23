#!/usr/bin/env python3
"""
Servidor Local MCP - expone funcionalidades de belleza, citas y git como herramientas MCP
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
app = Server("local-mcp")
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
        if not await claude_service.initialize():
            raise Exception("Claude service no disponible")

        beauty_controller = BeautyController(claude_service, logging_model)
        quotes_controller = QuotesController(logging_model)
        git_controller = GitController(logging_model)

        await beauty_controller.initialize()
        await quotes_controller.initialize()
        await git_controller.initialize()

        print("✅ MCP Local inicializado")
    except Exception as e:
        print(f"❌ Error inicializando sistema: {e}")
        raise

# -------------------------------------------------------------------
# Definir herramientas disponibles
# -------------------------------------------------------------------
@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="chat",
            description="Enviar un mensaje al asistente Claude",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                },
                "required": ["message"]
            }
        ),
        types.Tool(
            name="create_profile",
            description="Crear un perfil de belleza",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "name": {"type": "string"},
                    "skin_tone": {"type": "string"},
                    "eye_color": {"type": "string"},
                    "hair_color": {"type": "string"}
                },
                "required": ["user_id", "name", "skin_tone", "eye_color", "hair_color"]
            }
        ),
        types.Tool(
            name="get_quote",
            description="Obtener una cita inspiracional",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {"type": "string"}
                }
            }
        ),
        types.Tool(
            name="git_command",
            description="Ejecutar un comando de Git o filesystem",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string"}
                },
                "required": ["command"]
            }
        )
    ]

# -------------------------------------------------------------------
# Manejar llamadas a herramientas
# -------------------------------------------------------------------
@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "chat":
            msg = arguments["message"]
            response = await claude_service.send_message(msg, context=[])
            return [types.TextContent(type="text", text=response)]

        elif name == "create_profile":
            profile = beauty_controller.beauty_model.create_profile(arguments)
            return [types.TextContent(type="text", text=f"Perfil creado: {profile.user_id} - {profile.name}")]

        elif name == "get_quote":
            category = arguments.get("category")
            cmd = f"/quotes get {category}" if category else "/quotes get"
            response = await quotes_controller.handle_command(cmd)
            return [types.TextContent(type="text", text=response)]

        elif name == "git_command":
            cmd = arguments["command"]
            response = await git_controller.handle_command(cmd)
            return [types.TextContent(type="text", text=response)]

        else:
            return [types.TextContent(type="text", text=f"Herramienta desconocida: {name}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"❌ Error: {str(e)}")]

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
                server_name="local-mcp-beauty",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
