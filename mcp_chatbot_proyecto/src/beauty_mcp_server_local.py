#!/usr/bin/env python3
"""
Beauty Palette MCP Server - Versión Local
Servidor MCP especializado en paletas de colores y sistema de belleza
Compatible con el protocolo MCP para uso local
"""

import asyncio
import json
import colorsys
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

import mcp.types as types
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server

@dataclass
class BeautyProfile:
    """Perfil de belleza del usuario"""
    user_id: str
    name: str
    skin_tone: str
    undertone: str
    eye_color: str
    hair_color: str
    hair_type: str
    style_preference: str
    created_at: str
    updated_at: str

@dataclass
class ColorPalette:
    """Paleta de colores generada"""
    palette_id: str
    user_id: str
    palette_type: str
    event_type: str
    season: str
    colors: List[Dict[str, str]]
    recommendations: Dict[str, Any]
    created_at: str

class BeautyPaletteMCPServer:
    def __init__(self):
        """Inicializar servidor MCP de paletas de belleza local"""
        self.server_name = "Beauty Palette MCP Server Local"
        self.version = "1.0.0"
        self.profiles = {}  # Almacenamiento en memoria para perfiles
        self.palettes = {}  # Almacenamiento en memoria para paletas
        self.color_database = self._load_color_database()
        self.quotes_database = self._load_beauty_quotes()
        
    def _load_color_database(self) -> Dict[str, Any]:
        """Base de datos completa de colores para belleza"""
        return {
            "skin_tones": {
                "clara": {
                    "base_colors": ["#F5E6D3", "#E8D4C2", "#F2E7D5", "#FDF2E9"],
                    "best_colors": ["#FFB6C1", "#87CEEB", "#DDA0DD", "#F0E68C", "#98FB98"],
                    "avoid_colors": ["#000000", "#8B0000", "#2F4F4F", "#4B0082"],
                    "recommendations": [
                        "Los pasteles y tonos suaves realzan tu piel clara",
                        "Evita colores muy oscuros o intensos",
                        "Los colores fríos como azules y rosas te favorecen"
                    ]
                },
                "media": {
                    "base_colors": ["#D4B896", "#C1A882", "#B8956A", "#DEB887"],
                    "best_colors": ["#FF6347", "#32CD32", "#4169E1", "#DAA520", "#FF69B4"],
                    "avoid_colors": ["#FFFF00", "#00FF00", "#FF00FF", "#00FFFF"],
                    "recommendations": [
                        "Tienes la versatilidad de usar muchos colores",
                        "Los tonos tierra y cálidos te sientan especialmente bien",
                        "Puedes experimentar con colores vibrantes"
                    ]
                },
                "oscura": {
                    "base_colors": ["#8B5A3C", "#6B4423", "#4A2C17", "#5D4037"],
                    "best_colors": ["#FF4500", "#9400D3", "#FFD700", "#DC143C", "#00CED1"],
                    "avoid_colors": ["#FFFFE0", "#F0F8FF", "#FFFAF0", "#F5F5DC"],
                    "recommendations": [
                        "Los colores ricos y vibrantes realzan tu belleza",
                        "Evita colores muy pálidos que pueden lavarte",
                        "Los metálicos como oro y cobre son perfectos"
                    ]
                }
            },
            "undertones": {
                "frio": {
                    "colors": ["#4169E1", "#9370DB", "#C71585", "#00CED1", "#4682B4"],
                    "metals": ["plata", "platino", "oro_blanco", "acero"],
                    "description": "Venas azules, mejor en tonos fríos y metales plateados"
                },
                "calido": {
                    "colors": ["#FF6347", "#DAA520", "#D2691E", "#CD853F", "#B22222"],
                    "metals": ["oro", "cobre", "bronce", "oro_rosa"],
                    "description": "Venas verdes, mejor en tonos cálidos y metales dorados"
                },
                "neutro": {
                    "colors": ["#708090", "#BC8F8F", "#F0E68C", "#DEB887", "#D2B48C"],
                    "metals": ["oro_rosa", "acero_inoxidable", "oro_amarillo", "plata_oxidada"],
                    "description": "Puedes usar tanto metales dorados como plateados"
                }
            },
            "event_palettes": {
                "trabajo": {
                    "primary": ["#1E40AF", "#374151", "#6B7280", "#1F2937"],
                    "secondary": ["#F8FAFC", "#F1F5F9", "#E2E8F0", "#CBD5E1"],
                    "accent": ["#3B82F6", "#6366F1", "#8B5CF6"],
                    "description": "Colores profesionales que inspiran confianza"
                },
                "casual": {
                    "primary": ["#3B82F6", "#10B981", "#F59E0B", "#EF4444"],
                    "secondary": ["#DBEAFE", "#D1FAE5", "#FEF3C7", "#FEE2E2"],
                    "accent": ["#1D4ED8", "#059669", "#D97706", "#DC2626"],
                    "description": "Colores relajados y versátiles para el día a día"
                },
                "fiesta": {
                    "primary": ["#EC4899", "#8B5CF6", "#06B6D4", "#F59E0B"],
                    "secondary": ["#F9A8D4", "#C4B5FD", "#67E8F9", "#FCD34D"],
                    "accent": ["#FFD700", "#C0C0C0", "#B87333"],
                    "metallic": ["#FFD700", "#C0C0C0", "#CD7F32", "#E6E6FA"],
                    "description": "Colores vibrantes y llamativos para destacar"
                },
                "formal": {
                    "primary": ["#1F2937", "#374151", "#6B7280", "#111827"],
                    "secondary": ["#9CA3AF", "#D1D5DB", "#F3F4F6", "#F9FAFB"],
                    "accent": ["#1E40AF", "#7C2D12", "#064E3B", "#92400E"],
                    "description": "Elegancia clásica para eventos importantes"
                },
                "cita": {
                    "primary": ["#EC4899", "#F59E0B", "#8B5CF6", "#EF4444"],
                    "secondary": ["#F9A8D4", "#FCD34D", "#C4B5FD", "#FCA5A5"],
                    "accent": ["#BE185D", "#D97706", "#6D28D9", "#B91C1C"],
                    "description": "Colores románticos y favorecedores"
                }
            }
        }
    
    def _load_beauty_quotes(self) -> List[Dict[str, str]]:
        """Base de datos de citas inspiracionales"""
        return [
            {
                "quote": "La belleza comienza en el momento en que decides ser tú misma",
                "author": "Coco Chanel",
                "category": "confianza"
            },
            {
                "quote": "El estilo es una manera de decir quién eres sin tener que hablar",
                "author": "Rachel Zoe",
                "category": "estilo"
            },
            {
                "quote": "La elegancia es la única belleza que nunca se desvanece",
                "author": "Audrey Hepburn",
                "category": "elegancia"
            },
            {
                "quote": "La confianza es el mejor accesorio que puedes usar",
                "author": "Anónimo",
                "category": "confianza"
            },
            {
                "quote": "La moda se desvanece, pero el estilo es eterno",
                "author": "Yves Saint Laurent",
                "category": "estilo"
            },
            {
                "quote": "Invierte en tu piel, es donde vas a vivir para siempre",
                "author": "Warren Buffett",
                "category": "cuidado"
            },
            {
                "quote": "La belleza real está en ser auténtica contigo misma",
                "author": "Lupita Nyong'o",
                "category": "autenticidad"
            },
            {
                "quote": "El maquillaje no es una máscara que cubre tu belleza; es un arte que celebra tu unicidad",
                "author": "Kevyn Aucoin",
                "category": "maquillaje"
            }
        ]
    
    def create_profile(self, profile_data: Dict[str, str]) -> BeautyProfile:
        """Crear nuevo perfil de belleza"""
        profile = BeautyProfile(
            user_id=profile_data["user_id"],
            name=profile_data["name"],
            skin_tone=profile_data["skin_tone"],
            undertone=profile_data.get("undertone", "neutro"),
            eye_color=profile_data["eye_color"],
            hair_color=profile_data["hair_color"],
            hair_type=profile_data.get("hair_type", "liso"),
            style_preference=profile_data.get("style_preference", "moderno"),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Guardar en memoria
        self.profiles[profile.user_id] = profile
        return profile
    
    def get_profile(self, user_id: str) -> Optional[BeautyProfile]:
        """Obtener perfil por user_id"""
        return self.profiles.get(user_id)
    
    def list_profiles(self) -> List[str]:
        """Listar todos los perfiles disponibles"""
        return list(self.profiles.keys())
    
    def generate_palette(self, profile: BeautyProfile, palette_type: str, 
                        event_type: str, preferences: Dict = None) -> ColorPalette:
        """Generar paleta personalizada"""
        palette_id = f"palette_{profile.user_id}_{palette_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Generar colores según tipo
        if palette_type == "ropa":
            colors = self._generate_clothing_palette(profile, event_type, preferences)
        elif palette_type == "maquillaje":
            colors = self._generate_makeup_palette(profile, event_type, preferences)
        elif palette_type == "accesorios":
            colors = self._generate_accessories_palette(profile, event_type, preferences)
        else:
            raise ValueError(f"Tipo de paleta no válido: {palette_type}")
        
        # Generar recomendaciones
        recommendations = self._generate_recommendations(profile, palette_type, event_type, colors)
        
        palette = ColorPalette(
            palette_id=palette_id,
            user_id=profile.user_id,
            palette_type=palette_type,
            event_type=event_type,
            season=preferences.get('season', 'verano') if preferences else 'verano',
            colors=colors,
            recommendations=recommendations,
            created_at=datetime.now().isoformat()
        )
        
        # Guardar en memoria
        if profile.user_id not in self.palettes:
            self.palettes[profile.user_id] = []
        self.palettes[profile.user_id].append(palette)
        
        return palette
    
    def _generate_clothing_palette(self, profile: BeautyProfile, event_type: str, preferences: Dict = None) -> List[Dict[str, str]]:
        """Generar paleta específica para ropa"""
        colors = []
        
        # Colores base del evento
        event_colors = self.color_database["event_palettes"].get(event_type, {}).get("primary", [])
        
        # Colores según tono de piel
        skin_colors = self.color_database["skin_tones"].get(profile.skin_tone, {}).get("best_colors", [])
        
        # Combinar colores
        all_colors = event_colors[:3] + skin_colors[:3]
        
        categories = ["superior", "inferior", "superior", "acento", "neutro", "complemento"]
        names = ["Blusa Principal", "Pantalón Base", "Chaqueta", "Accesorio Vibrante", "Neutro Elegante", "Complemento"]
        
        for i, color_hex in enumerate(all_colors[:6]):
            colors.append({
                "hex": color_hex,
                "name": names[i],
                "category": categories[i],
                "usage": f"Ideal para {categories[i]} en {event_type}"
            })
        
        return colors
    
    def _generate_makeup_palette(self, profile: BeautyProfile, event_type: str, preferences: Dict = None) -> List[Dict[str, str]]:
        """Generar paleta específica para maquillaje"""
        colors = []
        
        # Colores para ojos según su color
        eye_colors = {
            "azul": ["#D2691E", "#CD853F", "#B8860B"],
            "verde": ["#8B0000", "#9370DB", "#B22222"],
            "cafe": ["#4682B4", "#8B4513", "#DAA520"],
            "gris": ["#4B0082", "#FF6347", "#20B2AA"],
            "negro": ["#B8860B", "#8B4513", "#CD853F"]
        }
        
        eye_palette = eye_colors.get(profile.eye_color, eye_colors["cafe"])
        
        # Colores para labios según tono de piel
        lip_colors = {
            "clara": ["#FF69B4", "#DC143C", "#CD5C5C"],
            "media": ["#B22222", "#FF4500", "#D2691E"],
            "oscura": ["#8B0000", "#FF6347", "#DC143C"]
        }
        
        lip_palette = lip_colors.get(profile.skin_tone, lip_colors["media"])
        
        # Construir paleta completa
        items = [
            ("Sombra Principal", eye_palette[0], "ojos"),
            ("Sombra Complemento", eye_palette[1], "ojos"),
            ("Delineador", eye_palette[2], "ojos"),
            ("Labial Principal", lip_palette[0], "labios"),
            ("Labial Día", lip_palette[1], "labios"),
            ("Labial Noche", lip_palette[2], "labios"),
            ("Rubor Natural", "#F08080", "mejillas"),
            ("Bronceador", "#E9967A", "mejillas")
        ]
        
        for name, color_hex, category in items:
            colors.append({
                "hex": color_hex,
                "name": name,
                "category": category,
                "usage": f"Perfecto para {category} en {event_type}"
            })
        
        return colors
    
    def _generate_accessories_palette(self, profile: BeautyProfile, event_type: str, preferences: Dict = None) -> List[Dict[str, str]]:
        """Generar paleta específica para accesorios"""
        colors = []
        
        # Metales según subtono
        metal_colors = self.color_database["undertones"].get(profile.undertone, {}).get("colors", [])[:3]
        
        # Colores complementarios
        complement_colors = self.color_database["event_palettes"].get(event_type, {}).get("primary", [])[:3]
        
        items = [
            ("Joyería Principal", metal_colors[0] if metal_colors else "#FFD700", "joyeria"),
            ("Bolso Coordinado", complement_colors[0] if complement_colors else "#8B4513", "bolsos"),
            ("Calzado Elegante", complement_colors[1] if len(complement_colors) > 1 else "#2F4F4F", "calzado"),
            ("Metal Complementario", metal_colors[1] if len(metal_colors) > 1 else "#C0C0C0", "metales"),
            ("Textura Especial", metal_colors[2] if len(metal_colors) > 2 else "#B87333", "textiles"),
            ("Acento Final", complement_colors[2] if len(complement_colors) > 2 else "#4169E1", "varios")
        ]
        
        for name, color_hex, category in items:
            colors.append({
                "hex": color_hex,
                "name": name,
                "category": category,
                "usage": f"Ideal para {category} en eventos {event_type}"
            })
        
        return colors
    
    def _generate_recommendations(self, profile: BeautyProfile, palette_type: str, 
                                 event_type: str, colors: List[Dict]) -> Dict[str, Any]:
        """Generar recomendaciones personalizadas"""
        recommendations = {
            "styling_tips": [],
            "color_combinations": [],
            "personalized_advice": [],
            "harmony_analysis": self._analyze_color_harmony([c["hex"] for c in colors])
        }
        
        # Tips específicos del evento
        event_tips = {
            "trabajo": [
                "Mantén un look profesional con colores neutros como base",
                "Agrega un toque de color en accesorios para personalidad",
                "Evita colores demasiado vibrantes para el ambiente laboral"
            ],
            "fiesta": [
                "¡Es momento de brillar! Usa colores intensos y metálicos",
                "Combina texturas diferentes para crear interés visual",
                "Los acentos dorados o plateados añaden glamour"
            ],
            "casual": [
                "Juega con colores y experimenta combinaciones divertidas",
                "Los denim y neutros son perfectos como base",
                "Añade color con accesorios según tu estado de ánimo"
            ]
        }
        
        recommendations["styling_tips"] = event_tips.get(event_type, [
            "Experimenta con diferentes combinaciones",
            "Usa colores que te hagan sentir confiada",
            "No tengas miedo de expresar tu personalidad"
        ])
        
        # Consejos según tono de piel
        skin_advice = self.color_database["skin_tones"].get(profile.skin_tone, {}).get("recommendations", [])
        recommendations["personalized_advice"] = skin_advice
        
        # Combinaciones de colores
        if len(colors) >= 3:
            recommendations["color_combinations"] = [
                f"Combina {colors[0]['name']} con {colors[1]['name']} para un look equilibrado",
                f"{colors[2]['name']} funciona perfecto como acento",
                f"Para mayor impacto, usa {colors[0]['name']} como color dominante"
            ]
        
        return recommendations
    
    def _analyze_color_harmony(self, colors: List[str]) -> Dict[str, Any]:
        """Análisis básico de armonía de colores"""
        if len(colors) < 2:
            return {"harmony_score": 0, "analysis": "Se necesitan al menos 2 colores"}
        
        try:
            # Convertir a HSL para análisis básico
            hsl_colors = []
            for color_hex in colors:
                hex_clean = color_hex.lstrip('#')
                if len(hex_clean) == 6:
                    rgb = tuple(int(hex_clean[i:i+2], 16) / 255.0 for i in (0, 2, 4))
                    hsl = colorsys.rgb_to_hls(*rgb)
                    hsl_colors.append(hsl)
            
            if len(hsl_colors) < 2:
                return {"harmony_score": 50, "analysis": "Análisis parcial"}
            
            # Calcular diferencias de matiz
            hue_differences = []
            for i in range(len(hsl_colors) - 1):
                h1, h2 = hsl_colors[i][0], hsl_colors[i + 1][0]
                diff = abs(h1 - h2) * 360
                hue_differences.append(diff)
            
            avg_diff = sum(hue_differences) / len(hue_differences)
            
            # Determinar tipo de armonía
            if avg_diff < 60:
                harmony_type = "Análoga"
                score = 85
                description = "Colores vecinos que crean tranquilidad y cohesión"
            elif 150 < avg_diff < 210:
                harmony_type = "Complementaria"
                score = 90
                description = "Colores opuestos que crean contraste dinámico"
            elif 90 < avg_diff < 150:
                harmony_type = "Triádica"
                score = 80
                description = "Tres colores balanceados que ofrecen vitalidad"
            else:
                harmony_type = "Compleja"
                score = 70
                description = "Paleta diversa que requiere habilidad"
            
            return {
                "harmony_score": score,
                "harmony_type": harmony_type,
                "analysis": description,
                "average_hue_difference": round(avg_diff, 2)
            }
            
        except Exception as e:
            return {"harmony_score": 50, "analysis": f"Error en análisis: {str(e)}"}
    
    def get_inspirational_quote(self, category: str = None) -> Dict[str, str]:
        """Obtener cita inspiracional"""
        quotes = self.quotes_database
        
        if category:
            filtered_quotes = [q for q in quotes if q.get('category', '').lower() == category.lower()]
            quotes = filtered_quotes if filtered_quotes else quotes
        
        selected_quote = random.choice(quotes)
        selected_quote["timestamp"] = datetime.now().isoformat()
        
        return selected_quote
    
    def get_user_palettes(self, user_id: str) -> List[ColorPalette]:
        """Obtener todas las paletas de un usuario"""
        return self.palettes.get(user_id, [])

# Instancia del servidor
beauty_server = BeautyPaletteMCPServer()

# Configurar el servidor MCP
app = Server("beauty-palette-local")

@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Lista todas las herramientas MCP disponibles"""
    return [
        types.Tool(
            name="create_beauty_profile",
            description="Crear un perfil de belleza personalizado",
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
                    "style_preference": {"type": "string", "enum": ["moderno", "clasico", "bohemio", "minimalista", "romantico", "edgy"], "default": "moderno"}
                },
                "required": ["user_id", "name", "skin_tone", "eye_color", "hair_color"]
            }
        ),
        types.Tool(
            name="generate_color_palette",
            description="Generar paleta de colores personalizada",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID del usuario"},
                    "palette_type": {"type": "string", "enum": ["ropa", "maquillaje", "accesorios"]},
                    "event_type": {"type": "string", "enum": ["casual", "trabajo", "formal", "fiesta", "cita"]},
                    "season": {"type": "string", "enum": ["primavera", "verano", "otono", "invierno"], "default": "verano"}
                },
                "required": ["user_id", "palette_type", "event_type"]
            }
        ),
        types.Tool(
            name="get_beauty_profile",
            description="Obtener perfil de belleza de un usuario",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID del usuario"}
                },
                "required": ["user_id"]
            }
        ),
        types.Tool(
            name="list_beauty_profiles",
            description="Listar todos los perfiles disponibles",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="get_user_palette_history",
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
            name="get_inspirational_quote",
            description="Obtener cita inspiracional de belleza",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "enum": ["confianza", "estilo", "elegancia", "cuidado", "autenticidad", "maquillaje"], "description": "Categoría de la cita"}
                }
            }
        ),
        types.Tool(
            name="analyze_color_harmony",
            description="Analizar armonía entre colores",
            inputSchema={
                "type": "object",
                "properties": {
                    "colors": {"type": "array", "items": {"type": "string"}, "description": "Lista de colores en formato hex"}
                },
                "required": ["colors"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Manejar llamadas a herramientas MCP"""
    try:
        if name == "create_beauty_profile":
            profile = beauty_server.create_profile(arguments)
            result = f"✅ Perfil creado para {profile.name} (ID: {profile.user_id})\n"
            result += f" Tono de piel: {profile.skin_tone} ({profile.undertone})\n"
            result += f"👁️ Color de ojos: {profile.eye_color}\n"
            result += f"💇‍♀️ Cabello: {profile.hair_color} ({profile.hair_type})\n"
            result += f" Estilo: {profile.style_preference}\n"
            result += f"📅 Creado: {profile.created_at[:19].replace('T', ' ')}"
            
            return [types.TextContent(type="text", text=result)]
        
        elif name == "generate_color_palette":
            user_id = arguments["user_id"]
            profile = beauty_server.get_profile(user_id)
            
            if not profile:
                return [types.TextContent(type="text", text=f"❌ Perfil '{user_id}' no encontrado")]
            
            palette_type = arguments["palette_type"]
            event_type = arguments["event_type"]
            preferences = {"season": arguments.get("season", "verano")}
            
            palette = beauty_server.generate_palette(profile, palette_type, event_type, preferences)
            
            result = f" PALETA DE {palette_type.upper()} - {event_type.upper()}\n"
            result += f"👤 Usuario: {profile.name} ({user_id})\n"
            result += f"🗓️ Generada: {palette.created_at[:19].replace('T', ' ')}\n\n"
            
            result += " COLORES:\n"
            for i, color in enumerate(palette.colors, 1):
                result += f"{i:2d}. {color['name']:20} | {color['hex']} | {color['category']}\n"
            
            result += f"\n ANÁLISIS DE ARMONÍA:\n"
            harmony = palette.recommendations.get("harmony_analysis", {})
            result += f"Tipo: {harmony.get('harmony_type', 'N/A')}\n"
            result += f"Puntuación: {harmony.get('harmony_score', 0)}/100\n"
            result += f"Análisis: {harmony.get('analysis', 'N/A')}\n"
            
            result += f"\n💡 CONSEJOS DE ESTILO:\n"
            for tip in palette.recommendations.get("styling_tips", [])[:3]:
                result += f"• {tip}\n"
            
            return [types.TextContent(type="text", text=result)]
        
        elif name == "get_beauty_profile":
            user_id = arguments["user_id"]
            profile = beauty_server.get_profile(user_id)
            
            if not profile:
                return [types.TextContent(type="text", text=f"❌ Perfil '{user_id}' no encontrado")]
            
            result = f"👤 PERFIL DE BELLEZA: {profile.name.upper()}\n\n"
            result += f" ID: {profile.user_id}\n"
            result += f" Tono de piel: {profile.skin_tone.title()} ({profile.undertone.title()})\n"
            result += f"👁️ Color de ojos: {profile.eye_color.title()}\n"
            result += f"💇‍♀️ Cabello: {profile.hair_color.title()} ({profile.hair_type.title()})\n"
            result += f" Estilo: {profile.style_preference.title()}\n"
            result += f"📅 Creado: {profile.created_at[:19].replace('T', ' ')}\n"
            result += f"🔄 Actualizado: {profile.updated_at[:19].replace('T', ' ')}\n"
            
            # Agregar recomendaciones específicas
            skin_data = beauty_server.color_database["skin_tones"].get(profile.skin_tone, {})
            if skin_data:
                result += f"\n💡 RECOMENDACIONES PARA TU TONO DE PIEL:\n"
                for rec in skin_data.get("recommendations", [])[:3]:
                    result += f"• {rec}\n"
                
                result += f"\n MEJORES COLORES: {', '.join(skin_data.get('best_colors', [])[:5])}\n"
                result += f"❌ EVITAR: {', '.join(skin_data.get('avoid_colors', [])[:3])}\n"
            
            return [types.TextContent(type="text", text=result)]
        
        elif name == "list_beauty_profiles":
            profiles = beauty_server.list_profiles()
            
            if not profiles:
                return [types.TextContent(type="text", text=" No hay perfiles de belleza creados")]
            
            result = f"👥 PERFILES DE BELLEZA DISPONIBLES ({len(profiles)}):\n\n"
            for i, profile_id in enumerate(profiles, 1):
                profile = beauty_server.get_profile(profile_id)
                if profile:
                    result += f"{i:2d}. {profile.name:20} | {profile_id:15} | {profile.skin_tone}/{profile.undertone}\n"
            
            result += f"\n Total: {len(profiles)} perfiles registrados"
            
            return [types.TextContent(type="text", text=result)]
        
        elif name == "get_user_palette_history":
            user_id = arguments["user_id"]
            profile = beauty_server.get_profile(user_id)
            
            if not profile:
                return [types.TextContent(type="text", text=f"❌ Perfil '{user_id}' no encontrado")]
            
            palettes = beauty_server.get_user_palettes(user_id)
            
            if not palettes:
                return [types.TextContent(type="text", text=f" No hay historial de paletas para {profile.name}")]
            
            result = f"📈 HISTORIAL DE PALETAS - {profile.name.upper()}\n\n"
            for i, palette in enumerate(palettes[-10:], 1):  # Últimas 10
                date = palette.created_at[:10]
                result += f"{i:2d}. {date} | {palette.palette_type.title():12} | {palette.event_type.title():10} | {len(palette.colors)} colores\n"
            
            result += f"\n Total: {len(palettes)} paletas generadas"
            
            return [types.TextContent(type="text", text=result)]
        
        elif name == "get_inspirational_quote":
            category = arguments.get("category")
            quote = beauty_server.get_inspirational_quote(category)
            
            result = f" CITA INSPIRACIONAL\n\n"
            result += f'"{quote["quote"]}"\n\n'
            result += f"— {quote['author']}\n"
            result += f"📝 Categoría: {quote['category'].title()}\n"
            result += f"⏰ Generada: {quote['timestamp'][:19].replace('T', ' ')}"
            
            return [types.TextContent(type="text", text=result)]
        
        elif name == "analyze_color_harmony":
            colors = arguments["colors"]
            
            if len(colors) < 2:
                return [types.TextContent(type="text", text="❌ Se requieren al menos 2 colores para análisis")]
            
            analysis = beauty_server._analyze_color_harmony(colors)
            
            result = f" ANÁLISIS DE ARMONÍA DE COLORES\n\n"
            result += f" Colores analizados: {len(colors)}\n"
            result += f" Puntuación de armonía: {analysis.get('harmony_score', 0)}/100\n"
            result += f"🔄 Tipo de armonía: {analysis.get('harmony_type', 'N/A')}\n"
            result += f"📝 Análisis: {analysis.get('analysis', 'N/A')}\n"
            
            if 'average_hue_difference' in analysis:
                result += f"📐 Diferencia promedio de matiz: {analysis['average_hue_difference']}°\n"
            
            result += f"\n COLORES ANALIZADOS:\n"
            for i, color in enumerate(colors, 1):
                result += f"{i}. {color}\n"
            
            return [types.TextContent(type="text", text=result)]
        
        else:
            return [types.TextContent(type="text", text=f"❌ Herramienta desconocida: {name}")]
    
    except Exception as e:
        return [types.TextContent(type="text", text=f"❌ Error ejecutando {name}: {str(e)}")]

async def main():
    """Función principal del servidor MCP"""
    print(" Iniciando Beauty Palette MCP Server Local...")
    print(f"📍 Servidor: {beauty_server.server_name}")
    print(f"🔢 Versión: {beauty_server.version}")
    print("🔧 Herramientas disponibles:")
    print("   • create_beauty_profile - Crear perfil personalizado")
    print("   • generate_color_palette - Generar paleta de colores")
    print("   • get_beauty_profile - Obtener perfil existente")
    print("   • list_beauty_profiles - Listar todos los perfiles")
    print("   • get_user_palette_history - Ver historial de paletas")
    print("   • get_inspirational_quote - Obtener cita inspiracional")
    print("   • analyze_color_harmony - Analizar armonía de colores")
    print("\n✅ Servidor MCP listo para conexiones...\n")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream, 
            write_stream, 
            InitializationOptions(
                server_name="beauty-palette-local",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())