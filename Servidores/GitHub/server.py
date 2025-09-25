import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

from mcp.server import Server
from mcp.types import Tool, TextContent, ServerCapabilities, ToolsCapability
from mcp.server.stdio import stdio_server

from Tools.tools import (
    init_repo,
    tool_git_list_branches,
    tool_git_commits,
    tool_git_show_file,
    tool_git_diff,
    tool_git_grep,
    tool_git_init,
    tool_git_create_file,
    tool_git_add,
    tool_git_commit,
    tool_git_status,
    tool_git_set_remote,   
    tool_git_push,
    tool_git_create_branch        
)


BASE_DIR = Path(__file__).parent
DEFAULT_REPO = BASE_DIR  # repositorio por defecto

server = Server("git_server")
STATE = {"repo": None}

# ---------- Declaración de tools ----------
TOOL_SCHEMAS = [
    Tool(
        name="git-init",
        description="Inicializa un nuevo repositorio Git en la ruta especificada.",
        inputSchema={
            "type": "object",
            "properties": {
                "repo_path": {"type": "string", "description": "Ruta donde crear el repo."}
            },
            "required": ["repo_path"],
            "additionalProperties": False
        }
    ),
    Tool(
        name="git-create-file",
        description="Crea o sobrescribe un archivo en el repositorio con el contenido dado.",
        inputSchema={
            "type": "object",
            "properties": {
                "repo_path": {"type": "string"},
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["repo_path", "path", "content"],
            "additionalProperties": False
        }
    ),
    Tool(
        name="git-add",
        description="Agrega archivos al staging area (git add).",
        inputSchema={
            "type": "object",
            "properties": {
                "repo_path": {"type": "string"},
                "paths": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["repo_path", "paths"],
            "additionalProperties": False
        }
    ),
    Tool(
        name="git-commit",
        description="Realiza un commit con mensaje y autor opcional.",
        inputSchema={
            "type": "object",
            "properties": {
                "repo_path": {"type": "string"},
                "message": {"type": "string"},
                "author": {"type": "string", "description": "Ej: 'Nombre <email>'"}
            },
            "required": ["repo_path", "message"],
            "additionalProperties": False
        }
    ),
    Tool(
        name="git-status",
        description="Muestra el estado del repositorio (git status --short).",
        inputSchema={
            "type": "object",
            "properties": {
                "repo_path": {"type": "string"}
            },
            "required": ["repo_path"],
            "additionalProperties": False
        }
    ),
    Tool(
        name="git-list-branches",
        description="Lista ramas locales o remotas del repositorio.",
        inputSchema={
            "type": "object",
            "properties": {
                "remote": {"type": "boolean"},
                "repo_path": {"type": "string"}
            },
            "additionalProperties": False
        }
    ),
    Tool(
        name="git-commits",
        description="Lista commits recientes de una rama.",
        inputSchema={
            "type": "object",
            "properties": {
                "branch": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
                "repo_path": {"type": "string"}
            },
            "additionalProperties": False
        }
    ),
    Tool(
        name="git-show-file",
        description="Muestra el contenido de un archivo en un commit/revisión.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "rev": {"type": "string"},
                "repo_path": {"type": "string"}
            },
            "required": ["path"],
            "additionalProperties": False
        }
    ),
    Tool(
        name="git-diff",
        description="Muestra el diff entre dos commits.",
        inputSchema={
            "type": "object",
            "properties": {
                "rev_a": {"type": "string"},
                "rev_b": {"type": "string"},
                "path": {"type": "string"},
                "repo_path": {"type": "string"}
            },
            "required": ["rev_a", "rev_b"],
            "additionalProperties": False
        }
    ),
    Tool(
        name="git-grep",
        description="Busca un patrón de texto en el repositorio.",
        inputSchema={
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "rev": {"type": "string"},
                "repo_path": {"type": "string"}
            },
            "required": ["pattern"],
            "additionalProperties": False
        }
    ),
    Tool(
        name="git-set-remote",
        description="Configura el remoto origin usando SSH.",
        inputSchema={
            "type": "object",
            "properties": {
                "repo_path": {"type": "string"},
                "remote_url": {"type": "string", "description": "Ej: git@github.com:usuario/repo.git"}
            },
            "required": ["repo_path", "remote_url"],
            "additionalProperties": False
        }
    ),
    Tool(
        name="git-push",
        description="Hace git push al remoto configurado (branch main).",
        inputSchema={
            "type": "object",
            "properties": {
                "repo_path": {"type": "string"}
            },
            "required": ["repo_path"],
            "additionalProperties": False
        }
    ),
    Tool(
        name="git-create-branch",
        description="Crea una nueva rama en el repositorio.",
        inputSchema={
            "type": "object",
            "properties": {
                "repo_path": {"type": "string"},
                "branch": {"type": "string"}
            },
            "required": ["repo_path", "branch"],
            "additionalProperties": False
        }
    ),




]

TOOLS = {
    "git-init": tool_git_init,
    "git-create-file": tool_git_create_file,
    "git-add": tool_git_add,
    "git-commit": tool_git_commit,
    "git-status": tool_git_status,
    "git-list-branches": tool_git_list_branches,
    "git-commits": tool_git_commits,
    "git-show-file": tool_git_show_file,
    "git-diff": tool_git_diff,
    "git-grep": tool_git_grep,
    "git-set-remote": tool_git_set_remote,
    "git-push": tool_git_push,
    "git-create-branch": tool_git_create_branch
}


@server.list_tools()
async def list_tools() -> list[Tool]:
    return TOOL_SCHEMAS

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    # Helper para resolver repo_path: nombre simple -> ~/repos/<nombre>
    def _resolve_repo_path(arg):
        p = Path(arg).expanduser()
        if not p.is_absolute() and "/" not in str(arg):
            p = Path.home() / "repos" / str(arg)
        return p.resolve()

    try:
        if name == "git-init":
            # No forzar que exista/sea repo: la tool lo creará
            result = TOOLS[name](STATE.get("repo") or DEFAULT_REPO, arguments)
        else:
            if "repo_path" in arguments and arguments["repo_path"]:
                effective = _resolve_repo_path(arguments["repo_path"])
                init_repo(effective, STATE)
            elif STATE["repo"] is None:
                init_repo(DEFAULT_REPO, STATE)

            func = TOOLS.get(name)
            if not func:
                result = {"error": f"Tool desconocida: {name}"}
            else:
                result = func(STATE["repo"], arguments)

    except Exception as e:
        result = {"error": str(e), "args": arguments}

    return [{
        "type": "text",
        "text": json.dumps(result, ensure_ascii=False, indent=2)
    }]


async def main():
    caps = ServerCapabilities(tools=ToolsCapability())
    init_opts = SimpleNamespace(
        server_name="git_server",
        server_version="1.0.0",
        description="Servidor MCP para operaciones Git (lectura y escritura segura).",
        instructions="Tools disponibles: git-init, git-create-file, git-add, git-commit, git-status, git-list-branches, git-commits, git-show-file, git-diff, git-grep.",
        capabilities=caps
    )
    print(" MCP Git Server corriendo...")
    async with stdio_server() as (read, write):
        await server.run(read, write, initialization_options=init_opts)

if __name__ == "__main__":
    asyncio.run(main())