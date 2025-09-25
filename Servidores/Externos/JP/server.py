import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

from mcp.server import Server
from mcp.types import Tool, TextContent, ServerCapabilities, ToolsCapability
from mcp.server.stdio import stdio_server

from Tools.tools import (
    init_data,
    tool_game_info,
    tool_count_games_by_genre,
    tool_best_publisher_by_sales,
    tool_top_games_by_sales,
    tool_publisher_leaderboard,
    tool_top_genres_by_platform,
    tool_top_sales_by_platform,
    tool_publisher_genre_breakdown,
    tool_top_games_by_region
)

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "videogames.csv"

server = Server("game_server")
STATE = {"df": None}

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="game_info",
            description="Return all available information (sales + metadata) for a specific game.",
            inputSchema={
                "type": "object",
                "properties": {"name": {"type": "string", "description": "Exact game name"}},
                "required": ["name"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="count_games_by_genre",
            description="Count how many games exist per genre, optionally filtered by a platform.",
            inputSchema={
                "type": "object",
                "properties": {"platform": {"type": "string"}},
                "additionalProperties": False,
            },
        ),
        Tool(
            name="best_publisher_by_sales",
            description="Find the publisher with the highest total global sales (optional year range).",
            inputSchema={
                "type": "object",
                "properties": {
                    "year_min": {"type": "integer"},
                    "year_max": {"type": "integer"},
                },
                "additionalProperties": False,
            },
        ),

        Tool(
            name="top_games_by_sales",
            description=(
                "Return a global ranking of the top-selling games by Global_Sales, "
                "regardless of platform. You can filter optionally by year range, genre, "
                "or publisher. Example: 'top 20 RPG games released after 2010'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10},
                    "year_min": {"type": "integer"},
                    "year_max": {"type": "integer"},
                    "genre": {"type": "string"},
                    "publisher": {"type": "string"},
                },
                "additionalProperties": False,
            },
        ),



        Tool(
            name="publisher_leaderboard",
            description="Publishers ranked by summed Global_Sales (optional year/genre filters).",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10},
                    "year_min": {"type": "integer"},
                    "year_max": {"type": "integer"},
                    "genre": {"type": "string"},
                },
                "additionalProperties": False,
            },
        ),
        Tool(
            name="top_genres_by_platform",
            description="Top genres on a given platform by Global_Sales.",
            inputSchema={
                "type": "object",
                "properties": {
                    "platform": {"type": "string"},
                    "limit": {"type": "integer", "default": 5},
                },
                "required": ["platform"],
                "additionalProperties": False,
            },
        ),

        Tool(
            name="top_sales_by_platform",
            description=(
                "Return a ranking of the best-selling games within a specific platform "
                "(e.g., Wii, PS2, DS). The results are ordered by Global_Sales. "
                "Optional filters include year range and genre."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "platform": {"type": "string"},  
                    "limit": {"type": "integer", "default": 10},
                    "year_min": {"type": "integer"},
                    "year_max": {"type": "integer"},
                    "genre": {"type": "string"},
                },
                "required": ["platform"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="publisher_genre_breakdown",
            description="Show how a publisher's sales are distributed across genres. Example: 'Electronic Arts by genre'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "publisher": {"type": "string"},
                    "year_min": {"type": "integer"},
                    "year_max": {"type": "integer"},
                },
                "required": ["publisher"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="top_games_by_region",
            description="Top-selling games in a specific region (NA, EU, JP, Other). Optional filters: year range, platform, genre, publisher.",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {"type": "string"},
                    "limit": {"type": "integer", "default": 10},
                    "year_min": {"type": "integer"},
                    "year_max": {"type": "integer"},
                    "platform": {"type": "string"},
                    "genre": {"type": "string"},
                    "publisher": {"type": "string"},
                },
                "required": ["region"],
                "additionalProperties": False,
            },
        ),

    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if STATE["df"] is None:
        init_data(DATA_PATH, STATE)

    try:
        if name == "game_info":
            result = tool_game_info(STATE["df"], arguments)
        elif name == "count_games_by_genre":
            result = tool_count_games_by_genre(STATE["df"], arguments)
        elif name == "best_publisher_by_sales":
            result = tool_best_publisher_by_sales(STATE["df"], arguments)
        elif name == "top_games_by_sales":
            result = tool_top_games_by_sales(STATE["df"], arguments)
        elif name == "publisher_leaderboard":
            result = tool_publisher_leaderboard(STATE["df"], arguments)
        elif name == "top_genres_by_platform":
            result = tool_top_genres_by_platform(STATE["df"], arguments)
        elif name == "top_sales_by_platform":
            result = tool_top_sales_by_platform(STATE["df"], arguments)
        elif name == "publisher_genre_breakdown":
            result = tool_publisher_genre_breakdown(STATE["df"], arguments)
        elif name == "top_games_by_region":
            result = tool_top_games_by_region(STATE["df"], arguments)


        else:
            result = {"error": f"Unknown tool: {name}"}
    except Exception as e:
        result = {"error": str(e), "args": arguments}

    return [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]

async def _amain():
    caps = ServerCapabilities(tools=ToolsCapability())
    init_opts = SimpleNamespace(
        server_name="game_server",
        server_version="1.0.0",
        description="MCP server for analyzing a videogames dataset",
        instructions=(
            "Use: game_info, count_games_by_genre, best_publisher_by_sales, "
            "top_games_by_sales, publisher_leaderboard, top_genres_by_platform, "
            "top_sales_by_platform, publisher_genre_breakdown, top_games_by_region."
        ),
        capabilities=caps,
    )

    print(" MCP server running...")
    async with stdio_server() as (read, write):
        await server.run(read, write, initialization_options=init_opts)

if __name__ == "__main__":
    asyncio.run(_amain())
