"""
Beauty Service - Servicio avanzado para generación de paletas de colores
"""

import colorsys
import random
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from models.beauty_model import BeautyProfile, ColorPalette


class BeautyService:
    def __init__(self):
        """Inicializar servicio de belleza"""
        self.color_theory = ColorTheoryEngine()
        self.palette_generator = PaletteGenerator(self.color_theory)
        self.trend_analyzer = TrendAnalyzer()
        self.eventos = ["casual", "formal", "fiesta", "trabajo", "cita", "deporte", "viaje"]

    def interpret_natural_command(self, text: str) -> Optional[str]:
            """
            Convierte una frase en lenguaje natural en un comando interno (/palette, /beauty, etc.)
            """
            text = text.lower()

            # Crear perfil
            if "crear perfil" in text or "nuevo perfil" in text:
                return "/beauty create_profile"

            # Ver perfil
            if "ver perfil" in text or "mostrar perfil" in text:
                user_id = self._extraer_usuario(text)
                return f"/beauty profile {user_id}"

            # Historial
            if "historial" in text or "paletas anteriores" in text:
                user_id = self._extraer_usuario(text)
                return f"/beauty history {user_id}"

            # Listar perfiles
            if "listar perfiles" in text or "todos los perfiles" in text:
                return "/beauty list_profiles"

            # Paletas
            if "paleta" in text or "colores" in text:
                user_id = self._extraer_usuario(text)
                evento = self._extraer_evento(text)

                if "maquillaje" in text:
                    return f"/palette maquillaje {user_id} {evento}"
                elif "ropa" in text:
                    return f"/palette ropa {user_id} {evento}"
                elif "accesorio" in text or "accesorios" in text:
                    return f"/palette accesorios {user_id} {evento}"
                else:
                    return f"/palette quick ropa {evento}"

            return None  # No entendió

    # --- Helpers ---
    def _extraer_usuario(self, text: str) -> str:
        """Busca un user_id en el texto (ej: maria_123)"""
        match = re.search(r"\b[a-zA-Z0-9_]{3,}\b", text)
        return match.group(0) if match else "default_user"

    def _extraer_evento(self, text: str) -> str:
        """Busca un evento conocido en el texto"""
        for evento in self.eventos:
            if evento in text:
                return evento
        return "casual"
    
    async def generate_advanced_palette(self, profile: BeautyProfile, palette_type: str, 
                                      event_type: str, preferences: Dict = None) -> ColorPalette:
        """
        Generar paleta avanzada basada en perfil y preferencias
        
        Args:
            profile: Perfil de belleza del usuario
            palette_type: Tipo de paleta (ropa, maquillaje, accesorios)
            event_type: Tipo de evento
            preferences: Preferencias adicionales
            
        Returns:
            Paleta de colores generada
        """
        # Generar ID único para la paleta
        palette_id = f"{profile.user_id}_{palette_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Determinar estación si no se especifica
        season = preferences.get('season') if preferences else self._determine_season()
        
        # Generar colores base según el perfil
        base_colors = self.color_theory.get_base_colors_for_profile(profile)
        
        # Generar colores específicos según tipo de paleta
        if palette_type == "ropa":
            colors = self.palette_generator.generate_clothing_palette(
                profile, event_type, season, base_colors, preferences
            )
        elif palette_type == "maquillaje":
            colors = self.palette_generator.generate_makeup_palette(
                profile, event_type, season, base_colors, preferences
            )
        elif palette_type == "accesorios":
            colors = self.palette_generator.generate_accessories_palette(
                profile, event_type, season, base_colors, preferences
            )
        else:
            raise ValueError(f"Tipo de paleta no soportado: {palette_type}")
        
        # Generar recomendaciones específicas
        recommendations = self._generate_recommendations(
            profile, palette_type, event_type, colors, preferences
        )
        
        # Crear objeto de paleta
        palette = ColorPalette(
            palette_id=palette_id,
            user_id=profile.user_id,
            palette_type=palette_type,
            event_type=event_type,
            season=season,
            colors=colors,
            recommendations=recommendations,
            created_at=datetime.now().isoformat()
        )
        
        return palette
    
    def _determine_season(self) -> str:
        """Determinar estación actual"""
        month = datetime.now().month
        if month in [3, 4, 5]:
            return "primavera"
        elif month in [6, 7, 8]:
            return "verano"
        elif month in [9, 10, 11]:
            return "otono"
        else:
            return "invierno"
    
    def _generate_recommendations(self, profile: BeautyProfile, palette_type: str, 
                                event_type: str, colors: List[Dict], 
                                preferences: Dict = None) -> Dict[str, Any]:
        """Generar recomendaciones específicas"""
        recommendations = {
            "primary_combinations": [],
            "alternative_options": [],
            "styling_tips": [],
            "color_harmony_analysis": "",
            "seasonal_adjustments": []
        }
        
        # Combinaciones primarias
        if palette_type == "ropa":
            recommendations["primary_combinations"] = self._generate_clothing_combinations(colors)
            recommendations["styling_tips"] = self._generate_styling_tips(profile, event_type)
        elif palette_type == "maquillaje":
            recommendations["primary_combinations"] = self._generate_makeup_combinations(colors)
            recommendations["application_tips"] = self._generate_makeup_tips(profile, event_type)
        elif palette_type == "accesorios":
            recommendations["primary_combinations"] = self._generate_accessory_combinations(colors)
            recommendations["coordination_tips"] = self._generate_coordination_tips(profile)
        
        # Análisis de armonía de colores
        recommendations["color_harmony_analysis"] = self.color_theory.analyze_harmony(colors)
        
        # Ajustes estacionales
        season = preferences.get('season') if preferences else self._determine_season()
        recommendations["seasonal_adjustments"] = self._generate_seasonal_adjustments(colors, season)
        
        return recommendations
    
    def _generate_clothing_combinations(self, colors: List[Dict]) -> List[str]:
        """Generar combinaciones de ropa"""
        combinations = []
        
        # Obtener colores por categoría
        tops = [c for c in colors if c.get('category') == 'superior']
        bottoms = [c for c in colors if c.get('category') == 'inferior']
        accents = [c for c in colors if c.get('category') == 'acento']
        
        # Generar combinaciones lógicas
        for top in tops[:2]:  # Máximo 2 tops
            for bottom in bottoms[:2]:  # Máximo 2 bottoms
                combination = f"{top['name']} + {bottom['name']}"
                if accents:
                    combination += f" + {accents[0]['name']} (acento)"
                combinations.append(combination)
        
        return combinations[:5]  # Máximo 5 combinaciones
    
    def _generate_makeup_combinations(self, colors: List[Dict]) -> List[str]:
        """Generar combinaciones de maquillaje"""
        combinations = []
        
        # Obtener colores por categoría
        eyes = [c for c in colors if c.get('category') == 'ojos']
        lips = [c for c in colors if c.get('category') == 'labios']
        cheeks = [c for c in colors if c.get('category') == 'mejillas']
        
        # Generar looks completos
        for i in range(min(3, len(eyes))):
            look = f"Look {i+1}: "
            if eyes:
                look += f"Ojos en {eyes[i]['name']}"
            if lips:
                look += f", labios en {lips[i % len(lips)]['name']}"
            if cheeks:
                look += f", mejillas en {cheeks[i % len(cheeks)]['name']}"
            combinations.append(look)
        
        return combinations
    
    def _generate_accessory_combinations(self, colors: List[Dict]) -> List[str]:
        """Generar combinaciones de accesorios"""
        combinations = []
        
        # Agrupar por tipo
        jewelry = [c for c in colors if c.get('category') == 'joyeria']
        bags = [c for c in colors if c.get('category') == 'bolsos']
        shoes = [c for c in colors if c.get('category') == 'calzado']
        
        # Generar sets coordinados
        for i in range(3):
            combo = f"Set {i+1}: "
            if jewelry:
                combo += f"Joyería en {jewelry[i % len(jewelry)]['name']}"
            if bags:
                combo += f", bolso en {bags[i % len(bags)]['name']}"
            if shoes:
                combo += f", calzado en {shoes[i % len(shoes)]['name']}"
            combinations.append(combo)
        
        return combinations
    
    def _generate_styling_tips(self, profile: BeautyProfile, event_type: str) -> List[str]:
        """Generar consejos de estilo"""
        tips = []
        
        # Consejos según tipo de evento
        if event_type == "formal":
            tips.append("Opta por líneas limpias y colores sólidos")
            tips.append("Evita estampados muy llamativos")
        elif event_type == "casual":
            tips.append("Puedes experimentar con texturas y capas")
            tips.append("Los accesorios pueden ser más relajados")
        elif event_type == "fiesta":
            tips.append("Es momento de brillar con colores vibrantes")
            tips.append("Considera telas con textura o brillo")
        
        # Consejos según estilo personal
        if profile.style_preference == "minimalista":
            tips.append("Mantén la paleta simple con 2-3 colores máximo")
        elif profile.style_preference == "bohemio":
            tips.append("Mezcla texturas naturales y colores tierra")
        
        return tips
    
    def _generate_makeup_tips(self, profile: BeautyProfile, event_type: str) -> List[str]:
        """Generar consejos de maquillaje"""
        tips = []
        
        # Consejos según color de ojos
        if profile.eye_color == "azul":
            tips.append("Los tonos naranjas y cobres realzan los ojos azules")
        elif profile.eye_color == "verde":
            tips.append("Los tonos rojizos y púrpuras hacen resaltar los ojos verdes")
        elif profile.eye_color == "cafe":
            tips.append("Casi todos los colores funcionan con ojos café")
        
        # Consejos según evento
        if event_type == "trabajo":
            tips.append("Mantén el maquillaje profesional y sutil")
        elif event_type == "fiesta":
            tips.append("Puedes ser más atrevida con colores intensos")
        
        return tips
    
    def _generate_coordination_tips(self, profile: BeautyProfile) -> List[str]:
        """Generar consejos de coordinación"""
        tips = []
        
        # Consejos según subtono
        if profile.undertone == "calido":
            tips.append("Elige metales dorados que complementen tu subtono")
        elif profile.undertone == "frio":
            tips.append("Los metales plateados realzarán tu subtono frío")
        else:
            tips.append("Puedes mezclar metales dorados y plateados")
        
        tips.append("Coordina bolso y zapatos en tonos complementarios")
        tips.append("Un accesorio statement puede ser el centro de atención")
        
        return tips
    
    def _generate_seasonal_adjustments(self, colors: List[Dict], season: str) -> List[str]:
        """Generar ajustes estacionales"""
        adjustments = []
        
        if season == "verano":
            adjustments.append("Considera versiones más claras de estos colores")
            adjustments.append("Agrega blancos y pasteles para frescura")
        elif season == "invierno":
            adjustments.append("Profundiza estos tonos para la estación")
            adjustments.append("Incorpora texturas ricas y colores intensos")
        elif season == "primavera":
            adjustments.append("Ilumina la paleta con tonos más vibrantes")
            adjustments.append("Agrega toques de colores frescos")
        elif season == "otono":
            adjustments.append("Añade tonos tierra y especias")
            adjustments.append("Considera versiones más cálidas de estos colores")
        
        return adjustments


class ColorTheoryEngine:
    """Motor de teoría del color para análisis avanzado"""
    
    def __init__(self):
        self.color_relationships = {
            "complementary": 180,
            "analogous": 30,
            "triadic": 120,
            "split_complementary": [150, 210],
            "tetradic": [60, 180, 240]
        }
    
    def hex_to_hsl(self, hex_color: str) -> Tuple[float, float, float]:
        """Convertir hex a HSL"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        return colorsys.rgb_to_hls(*rgb)
    
    def hsl_to_hex(self, h: float, s: float, l: float) -> str:
        """Convertir HSL a hex"""
        rgb = colorsys.hls_to_rgb(h, l, s)
        return "#{:02x}{:02x}{:02x}".format(
            int(rgb[0] * 255),
            int(rgb[1] * 255),
            int(rgb[2] * 255)
        )
    
    def get_base_colors_for_profile(self, profile: BeautyProfile) -> List[Dict[str, str]]:
        """Obtener colores base según perfil"""
        base_colors = []
        
        # Base de datos de colores según características
        skin_tone_colors = {
            "clara": ["#F5E6D3", "#FFB6C1", "#87CEEB", "#DDA0DD"],
            "media": ["#D4B896", "#FF6347", "#32CD32", "#4169E1"],
            "oscura": ["#8B5A3C", "#FF4500", "#9400D3", "#FFD700"]
        }
        
        undertone_colors = {
            "frio": ["#4169E1", "#9370DB", "#C71585", "#00CED1"],
            "calido": ["#FF6347", "#DAA520", "#D2691E", "#CD853F"],
            "neutro": ["#708090", "#BC8F8F", "#F0E68C", "#DEB887"]
        }
        
        # Obtener colores según tono de piel
        if profile.skin_tone in skin_tone_colors:
            for color in skin_tone_colors[profile.skin_tone][:2]:
                base_colors.append({"hex": color, "source": "skin_tone"})
        
        # Obtener colores según subtono
        if profile.undertone in undertone_colors:
            for color in undertone_colors[profile.undertone][:2]:
                base_colors.append({"hex": color, "source": "undertone"})
        
        return base_colors
    
    def generate_complementary_colors(self, base_hex: str, count: int = 3) -> List[str]:
        """Generar colores complementarios"""
        h, s, l = self.hex_to_hsl(base_hex)
        colors = []
        
        for i in range(count):
            # Rotar matiz para obtener complementarios
            new_h = (h + (self.color_relationships["complementary"] + i * 30) / 360) % 1
            new_color = self.hsl_to_hex(new_h, s * 0.8, l * 0.9)
            colors.append(new_color)
        
        return colors
    
    def analyze_harmony(self, colors: List[Dict]) -> str:
        """Analizar armonía entre colores"""
        if len(colors) < 2:
            return "Insuficientes colores para análisis"
        
        # Convertir colores a HSL
        hsl_colors = []
        for color in colors:
            if 'hex' in color:
                hsl_colors.append(self.hex_to_hsl(color['hex']))
        
        if len(hsl_colors) < 2:
            return "Colores no válidos para análisis"
        
        # Analizar diferencias de matiz
        hue_differences = []
        for i in range(len(hsl_colors) - 1):
            h1, h2 = hsl_colors[i][0], hsl_colors[i + 1][0]
            diff = abs(h1 - h2) * 360
            hue_differences.append(diff)
        
        avg_diff = sum(hue_differences) / len(hue_differences)
        
        if avg_diff < 60:
            return "Paleta análoga - Colores armoniosos y tranquilos"
        elif 150 < avg_diff < 210:
            return "Paleta complementaria - Colores contrastantes y vibrantes"
        elif 90 < avg_diff < 150:
            return "Paleta triádica - Colores equilibrados y dinámicos"
        else:
            return "Paleta variada - Buena diversidad de tonos"


class PaletteGenerator:
    """Generador específico de paletas por categoría"""
    
    def __init__(self, color_theory: ColorTheoryEngine):
        self.color_theory = color_theory
    
    def generate_clothing_palette(self, profile: BeautyProfile, event_type: str, 
                                season: str, base_colors: List[Dict], 
                                preferences: Dict = None) -> List[Dict[str, str]]:
        """Generar paleta específica para ropa"""
        colors = []
        
        # Colores para prendas superiores
        superior_colors = self._get_event_colors(event_type, "superior")
        for i, color_hex in enumerate(superior_colors[:3]):
            colors.append({
                "hex": color_hex,
                "name": f"Blusa/Camisa {i+1}",
                "category": "superior",
                "usage": "Prenda principal superior"
            })
        
        # Colores para prendas inferiores
        inferior_colors = self._get_neutral_colors(3)
        for i, color_hex in enumerate(inferior_colors):
            colors.append({
                "hex": color_hex,
                "name": f"Pantalón/Falda {i+1}",
                "category": "inferior",
                "usage": "Prenda principal inferior"
            })
        
        # Colores de acento
        accent_colors = self._get_accent_colors(base_colors, 2)
        for i, color_hex in enumerate(accent_colors):
            colors.append({
                "hex": color_hex,
                "name": f"Acento {i+1}",
                "category": "acento",
                "usage": "Detalles y accesorios"
            })
        
        return colors
    
    def generate_makeup_palette(self, profile: BeautyProfile, event_type: str, 
                               season: str, base_colors: List[Dict], 
                               preferences: Dict = None) -> List[Dict[str, str]]:
        """Generar paleta específica para maquillaje"""
        colors = []
        
        # Colores para ojos
        eye_colors = self._get_eye_makeup_colors(profile.eye_color, event_type)
        for i, color_hex in enumerate(eye_colors):
            colors.append({
                "hex": color_hex,
                "name": f"Sombra {i+1}",
                "category": "ojos",
                "usage": "Maquillaje de ojos"
            })
        
        # Colores para labios
        lip_colors = self._get_lip_colors(profile.skin_tone, event_type)
        for i, color_hex in enumerate(lip_colors):
            colors.append({
                "hex": color_hex,
                "name": f"Labial {i+1}",
                "category": "labios",
                "usage": "Color de labios"
            })
        
        # Colores para mejillas
        cheek_colors = self._get_cheek_colors(profile.skin_tone)
        for i, color_hex in enumerate(cheek_colors):
            colors.append({
                "hex": color_hex,
                "name": f"Rubor {i+1}",
                "category": "mejillas",
                "usage": "Color de mejillas"
            })
        
        return colors
    
    def generate_accessories_palette(self, profile: BeautyProfile, event_type: str, 
                                   season: str, base_colors: List[Dict], 
                                   preferences: Dict = None) -> List[Dict[str, str]]:
        """Generar paleta específica para accesorios"""
        colors = []
        
        # Colores para joyería
        metal_preference = preferences.get('metal_preference') if preferences else profile.undertone
        jewelry_colors = self._get_jewelry_colors(metal_preference)
        for i, color_hex in enumerate(jewelry_colors):
            colors.append({
                "hex": color_hex,
                "name": f"Joyería {i+1}",
                "category": "joyeria",
                "usage": "Collares, aretes, pulseras"
            })
        
        # Colores para bolsos
        bag_colors = self._get_accessory_colors(event_type, "bags")
        for i, color_hex in enumerate(bag_colors):
            colors.append({
                "hex": color_hex,
                "name": f"Bolso {i+1}",
                "category": "bolsos",
                "usage": "Bolsos y carteras"
            })
        
        # Colores para calzado
        shoe_colors = self._get_accessory_colors(event_type, "shoes")
        for i, color_hex in enumerate(shoe_colors):
            colors.append({
                "hex": color_hex,
                "name": f"Calzado {i+1}",
                "category": "calzado",
                "usage": "Zapatos y botas"
            })
        
        return colors
    
    def _get_event_colors(self, event_type: str, category: str) -> List[str]:
        """Obtener colores según tipo de evento"""
        event_palettes = {
            "casual": ["#3B82F6", "#10B981", "#F59E0B", "#EF4444"],
            "formal": ["#1F2937", "#374151", "#6B7280", "#1E40AF"],
            "fiesta": ["#EC4899", "#8B5CF6", "#06B6D4", "#F59E0B"],
            "trabajo": ["#1E40AF", "#7C2D12", "#064E3B", "#92400E"],
            "cita": ["#EC4899", "#F59E0B", "#8B5CF6", "#EF4444"],
            "deporte": ["#10B981", "#3B82F6", "#6B7280", "#F59E0B"]
        }
        
        return event_palettes.get(event_type, event_palettes["casual"])
    
    def _get_neutral_colors(self, count: int) -> List[str]:
        """Obtener colores neutros"""
        neutrals = ["#1F2937", "#374151", "#6B7280", "#9CA3AF", "#2D3748", "#4A5568"]
        return neutrals[:count]
    
    def _get_accent_colors(self, base_colors: List[Dict], count: int) -> List[str]:
        """Generar colores de acento"""
        if base_colors:
            base_hex = base_colors[0]["hex"]
            return self.color_theory.generate_complementary_colors(base_hex, count)
        else:
            return ["#EF4444", "#F59E0B"][:count]
    
    def _get_eye_makeup_colors(self, eye_color: str, event_type: str) -> List[str]:
        """Obtener colores de maquillaje para ojos"""
        eye_palettes = {
            "azul": ["#D2691E", "#CD853F", "#F4A460"],
            "verde": ["#8B0000", "#9370DB", "#B8860B"],
            "cafe": ["#2F4F4F", "#8B4513", "#DAA520"],
            "gris": ["#4B0082", "#FF6347", "#20B2AA"],
            "negro": ["#B8860B", "#8B4513", "#CD853F"]
        }
        
        base_colors = eye_palettes.get(eye_color, eye_palettes["cafe"])
        
        # Ajustar intensidad según evento
        if event_type in ["fiesta", "cita"]:
            return base_colors  # Colores más intensos
        else:
            # Colores más suaves para trabajo/casual
            return ["#D2B48C", "#F5DEB3", "#DDD2C0"]
    
    def _get_lip_colors(self, skin_tone: str, event_type: str) -> List[str]:
        """Obtener colores para labios"""
        lip_palettes = {
            "clara": ["#FF69B4", "#DC143C", "#FF6B8A"],
            "media": ["#B22222", "#FF4500", "#D2691E"],
            "oscura": ["#8B0000", "#FF6347", "#CD5C5C"]
        }
        
        base_colors = lip_palettes.get(skin_tone, lip_palettes["media"])
        
        if event_type == "trabajo":
            return ["#CD5C5C", "#BC8F8F", "#F08080"]  # Colores más profesionales
        else:
            return base_colors
    
    def _get_cheek_colors(self, skin_tone: str) -> List[str]:
        """Obtener colores para mejillas"""
        cheek_palettes = {
            "clara": ["#FFB6C1", "#FFC0CB", "#F08080"],
            "media": ["#CD5C5C", "#F08080", "#E9967A"],
            "oscura": ["#A0522D", "#CD853F", "#D2691E"]
        }
        
        return cheek_palettes.get(skin_tone, cheek_palettes["media"])
    
    def _get_jewelry_colors(self, undertone: str) -> List[str]:
        """Obtener colores de joyería"""
        if undertone in ["calido", "oro"]:
            return ["#FFD700", "#B8860B", "#DAA520"]  # Dorados
        elif undertone in ["frio", "plata"]:
            return ["#C0C0C0", "#708090", "#B0C4DE"]  # Plateados
        else:
            return ["#CD7F32", "#F4A460", "#DDA0DD"]  # Oro rosa/mixto
    
    def _get_accessory_colors(self, event_type: str, accessory_type: str) -> List[str]:
        """Obtener colores para accesorios específicos"""
        if accessory_type == "bags":
            if event_type == "formal":
                return ["#000000", "#2F4F4F", "#8B4513"]
            else:
                return ["#8B4513", "#2F4F4F", "#A0522D"]
        else:  # shoes
            if event_type == "formal":
                return ["#000000", "#2F4F4F", "#654321"]
            else:
                return ["#8B4513", "#A0522D", "#2F4F4F"]


class TrendAnalyzer:
    """Analizador de tendencias de color"""
    
    def __init__(self):
        self.current_trends = {
            "2024": {
                "primary": ["#FF6B35", "#F7931E", "#FFD23F", "#06FFA5"],
                "neutral": ["#F5F5DC", "#E6E6FA", "#F0F8FF"],
                "accent": ["#FF1493", "#00CED1", "#9370DB"]
            }
        }
    
    def get_trending_colors(self, category: str = "primary") -> List[str]:
        """Obtener colores en tendencia"""
        current_year = str(datetime.now().year)
        return self.current_trends.get(current_year, {}).get(category, [])
    
    def analyze_color_trend_compatibility(self, colors: List[str]) -> Dict[str, Any]:
        """Analizar compatibilidad con tendencias actuales"""
        trending = self.get_trending_colors("primary")
        
        compatibility_score = 0
        for color in colors:
            if color in trending:
                compatibility_score += 1
        
        return {
            "score": compatibility_score / len(colors) if colors else 0,
            "trending_alternatives": trending[:3],
            "recommendation": "Alta" if compatibility_score > len(colors) / 2 else "Media"
        }


# Testing del servicio
if __name__ == "__main__":
    import asyncio
    from models.beauty_model import BeautyProfile
    
    async def test_beauty_service():
        print("Testing Beauty Service...")
        
        # Crear perfil de prueba
        profile = BeautyProfile(
            user_id="test_user",
            name="Test User",
            skin_tone="media",
            undertone="calido",
            eye_color="cafe",
            hair_color="castano",
            hair_type="ondulado",
            style_preference="moderno",
            created_at="2024-01-01T10:00:00",
            updated_at="2024-01-01T10:00:00"
        )
        
        # Inicializar servicio
        service = BeautyService()
        
        # Generar paleta de ropa
        palette = await service.generate_advanced_palette(
            profile, "ropa", "trabajo", {"season": "verano"}
        )
        
        print(f"Paleta generada: {palette.palette_id}")
        print(f"Colores: {len(palette.colors)}")
        print(f"Recomendaciones: {len(palette.recommendations)}")
        
        # Mostrar algunos colores
        for color in palette.colors[:3]:
            print(f"  {color['name']}: {color['hex']} ({color['category']})")
        
        print("Beauty Service funcionando correctamente")
    
    asyncio.run(test_beauty_service())