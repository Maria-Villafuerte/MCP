import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

from mcp.server import Server
from mcp.types import Tool, TextContent, ServerCapabilities, ToolsCapability
from mcp.server.stdio import stdio_server

from tools import (
    tool_fs_list_dir,
    tool_fs_read_file,
    tool_fs_write_file,
    tool_fs_delete
)

BASE_DIR = Path(__file__).parent
server = Server("filesystem_server")
STATE = {"base": BASE_DIR}

TOOL_SCHEMAS = [
    Tool(
        name="fs-list-dir",
        description="Lista archivos y carpetas de un directorio.",
        inputSchema={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "additionalProperties": False
        }
    ),
    Tool(
        name="fs-read-file",
        description="Lee un archivo de texto.",
        inputSchema={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False
        }
    ),
    Tool(
        name="fs-write-file",
        description="Escribe contenido en un archivo (sobrescribe si existe).",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"],
            "additionalProperties": False
        }
    ),
    Tool(
        name="fs-delete",
        description="Elimina un archivo o directorio (recursivo).",
        inputSchema={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False
        }
    )
]

TOOLS = {
    "fs-list-dir": tool_fs_list_dir,
    "fs-read-file": tool_fs_read_file,
    "fs-write-file": tool_fs_write_file,
    "fs-delete": tool_fs_delete
}


@server.list_tools()
async def list_tools() -> list[Tool]:
    return TOOL_SCHEMAS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    func = TOOLS.get(name)
    if not func:
        result = {"error": f"Tool desconocida: {name}"}
    else:
        result = func(STATE["base"], arguments)
    return [{
        "type": "text",
        "text": json.dumps(result, ensure_ascii=False, indent=2)
    }]


async def main():
    caps = ServerCapabilities(tools=ToolsCapability())
    init_opts = SimpleNamespace(
        server_name="filesystem_server",
        server_version="1.0.0",
        description="Servidor MCP para operaciones de sistema de archivos.",
        instructions="Tools: fs-list-dir, fs-read-file, fs-write-file, fs-delete.",
        capabilities=caps
    )
    print(" MCP Filesystem Server corriendo...")
    async with stdio_server() as (read, write):
        await server.run(read, write, initialization_options=init_opts)


if __name__ == "__main__":
    asyncio.run(main())