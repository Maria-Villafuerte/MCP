import asyncio
import json
from types import SimpleNamespace

from mcp.server import Server
from mcp.types import Tool, TextContent, ServerCapabilities, ToolsCapability
from mcp.server.stdio import stdio_server

from metodos_server import (
    init_data_storage,
    tool_create_profile,
    tool_show_profile,
    tool_list_profiles,
    tool_delete_profile,
    tool_generate_palette,
    tool_quick_palette,
    tool_export_data
)

server = Server("beauty_server_professional")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="create_profile",
            description="Crear un perfil avanzado de belleza con análisis colorimétrico profesional basado en múltiples indicadores físicos para determinar la estación de color personal.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string", 
                        "description": "ID único del usuario"
                    },
                    "name": {
                        "type": "string", 
                        "description": "Nombre completo del usuario"
                    },
                    "skin_tone": {
                        "type": "string", 
                        "enum": ["clara", "media", "oscura"],
                        "description": "Tono general de piel: clara (se quema fácil), media (broncea moderadamente), oscura (broncea fácilmente)"
                    },
                    "vein_color": {
                        "type": "string", 
                        "enum": ["azul", "azul_verdoso", "purpura", "verde", "verde_oliva", "indefinido"],
                        "description": "Color de las venas en la muñeca bajo luz natural - CRÍTICO para determinar subtono"
                    },
                    "jewelry_preference": {
                        "type": "string", 
                        "enum": ["plata", "oro", "ambos"],
                        "description": "¿Qué metal te favorece más? Plata (subtono frío), oro (subtono cálido)"
                    },
                    "sun_reaction": {
                        "type": "string", 
                        "enum": ["se_quema", "broncea_despacio", "broncea_facil"],
                        "description": "Reacción de la piel al sol: se_quema (frío), broncea_despacio (neutro), broncea_facil (cálido)"
                    },
                    "eye_color": {
                        "type": "string", 
                        "enum": ["azul", "verde", "cafe", "gris", "avellana", "negro", "miel", "azul_gris", "verde_gris"],
                        "description": "Color específico de ojos - importante para determinar contraste"
                    },
                    "hair_color": {
                        "type": "string", 
                        "enum": ["rubio_platino", "rubio", "rubio_cenizo", "castano_claro", "castano", "castano_oscuro", "negro", "pelirrojo_claro", "pelirrojo", "pelirrojo_oscuro", "gris", "blanco", "castaño_dorado", "rubio_dorado"],
                        "description": "Color natural del cabello - afecta el nivel de contraste personal"
                    },
                    "natural_lip_color": {
                        "type": "string", 
                        "enum": ["rosado", "coral", "durazno", "cafe_rosado", "rojo_natural"],
                        "description": "Color natural de los labios sin maquillaje - indicador de subtono"
                    },
                    "contrast_level": {
                        "type": "string", 
                        "enum": ["bajo", "medio", "alto"],
                        "description": "Contraste entre cabello, ojos y piel: bajo (colores similares), medio (diferencia moderada), alto (gran diferencia)"
                    },
                    "hair_type": {
                        "type": "string", 
                        "enum": ["liso", "ondulado", "rizado", "crespo"],
                        "description": "Tipo de textura del cabello (opcional para recomendaciones de estilo)"
                    },
                    "style_preference": {
                        "type": "string", 
                        "enum": ["clasico", "moderno", "bohemio", "minimalista", "glamoroso", "dramatico", "romantico", "casual_chic"],
                        "description": "Preferencia de estilo personal para personalizar recomendaciones"
                    }
                },
                "required": ["user_id", "name", "skin_tone", "vein_color", "jewelry_preference", "sun_reaction", "eye_color", "hair_color", "natural_lip_color", "contrast_level"],
                "additionalProperties": False,
            },
        ),
        
        Tool(
            name="show_profile",
            description="Mostrar el análisis colorimétrico completo de un perfil de usuario específico, incluyendo estación de color, subtono y recomendaciones detalladas.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string", 
                        "description": "ID del usuario del cual mostrar el perfil completo"
                    }
                },
                "required": ["user_id"],
                "additionalProperties": False,
            },
        ),
        
        Tool(
            name="list_profiles",
            description="Listar todos los perfiles de belleza con resumen de su análisis colorimétrico (subtono y estación de color).",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        ),
        
        Tool(
            name="delete_profile",
            description="Eliminar completamente un perfil de usuario y todos sus análisis asociados del sistema.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string", 
                        "description": "ID del usuario cuyo perfil se eliminará"
                    }
                },
                "required": ["user_id"],
                "additionalProperties": False,
            },
        ),
        
        Tool(
            name="generate_palette",
            description="Generar una paleta de colores profesional personalizada basada en el análisis colorimétrico completo del usuario, usando teoría de armonías de color.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string", 
                        "description": "ID del usuario para quien generar la paleta personalizada"
                    },
                    "palette_type": {
                        "type": "string", 
                        "enum": ["ropa", "maquillaje", "accesorios"],
                        "description": "Tipo específico de paleta a generar"
                    },
                    "event_type": {
                        "type": "string", 
                        "enum": ["casual", "formal", "fiesta", "trabajo", "playa", "noche"],
                        "description": "Tipo de evento u ocasión para personalizar la paleta"
                    }
                },
                "required": ["user_id", "palette_type"],
                "additionalProperties": False,
            },
        ),
        
        Tool(
            name="quick_palette",
            description="Generar una paleta de colores rápida usando características básicas sin necesidad de un perfil completo. Ideal para consultas rápidas.",
            inputSchema={
                "type": "object",
                "properties": {
                    "palette_type": {
                        "type": "string", 
                        "enum": ["ropa", "maquillaje", "accesorios"],
                        "description": "Tipo de paleta a generar"
                    },
                    "event_type": {
                        "type": "string", 
                        "enum": ["casual", "formal", "fiesta", "trabajo", "playa", "noche"],
                        "description": "Tipo de evento u ocasión"
                    },
                    "skin_tone": {
                        "type": "string", 
                        "enum": ["clara", "media", "oscura"],
                        "description": "Tono de piel (opcional, por defecto: media)"
                    },
                    "undertone": {
                        "type": "string", 
                        "enum": ["frio", "calido", "neutro"],
                        "description": "Subtono de piel (opcional, por defecto: neutro)"
                    }
                },
                "required": ["palette_type"],
                "additionalProperties": False,
            },
        ),
        
        Tool(
            name="export_data",
            description="Exportar todos los datos de un usuario incluyendo perfil completo, análisis colorimétrico y todas las paletas generadas.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string", 
                        "description": "ID del usuario cuyos datos se exportarán"
                    }
                },
                "required": ["user_id"],
                "additionalProperties": False,
            },
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Ejecutar herramientas del servidor con manejo robusto de errores"""
    try:
        if name == "create_profile":
            result = tool_create_profile(arguments)
        elif name == "show_profile":
            result = tool_show_profile(arguments)
        elif name == "list_profiles":
            result = tool_list_profiles(arguments)
        elif name == "delete_profile":
            result = tool_delete_profile(arguments)
        elif name == "generate_palette":
            result = tool_generate_palette(arguments)
        elif name == "quick_palette":
            result = tool_quick_palette(arguments)
        elif name == "export_data":
            result = tool_export_data(arguments)
        else:
            result = {
                "error": f"Herramienta desconocida: {name}",
                "available_tools": ["create_profile", "show_profile", "list_profiles", "delete_profile", "generate_palette", "quick_palette", "export_data"]
            }
    
    except Exception as e:
        result = {
            "error": f"Error ejecutando {name}: {str(e)}",
            "arguments_received": arguments,
            "suggestion": "Verifica que todos los campos requeridos estén presentes y sean válidos"
        }

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

async def _amain():
    """Función principal del servidor MCP"""
    # Inicializar almacenamiento de datos
    print("Inicializando sistema avanzado de colorimetría...")
    init_data_storage()
    
    caps = ServerCapabilities(tools=ToolsCapability())
    init_opts = SimpleNamespace(
        server_name="beauty_server_professional",
        server_version="2.0.0",
        description=(
            "Servidor MCP profesional para análisis de belleza y colorimetría avanzada. "
            "Incluye análisis científico de subtono basado en múltiples indicadores, "
            "determinación de estación de color personal, y generación de paletas usando "
            "teoría profesional de armonías cromáticas."
        ),
        instructions=(
            "Sistema de colorimetría profesional con 8 estaciones de color. "
            "Herramientas: create_profile (análisis completo), show_profile (mostrar análisis), "
            "list_profiles (listar usuarios), delete_profile (eliminar), generate_palette (paleta personalizada), "
            "quick_palette (paleta rápida), export_data (exportar datos completos). "
            "Para crear perfil se requiere: color de venas, preferencia de joyería, reacción al sol, "
            "color natural de labios y nivel de contraste para análisis científico preciso."
        ),
        capabilities=caps,
    )

    print("Servidor MCP de Colorimetría Profesional ejecutándose...")
    print("Estaciones disponibles: Primavera Cálida/Clara, Verano Suave/Frío, Otoño Suave/Profundo, Invierno Profundo/Brillante")
    print("Análisis basado en: color de venas, reacción al sol, preferencia de metales, contraste natural")
    
    async with stdio_server() as (read, write):
        await server.run(read, write, initialization_options=init_opts)

if __name__ == "__main__":
    asyncio.run(_amain())