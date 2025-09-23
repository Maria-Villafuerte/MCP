"""
Beauty Model - Modelo de datos para sistema de belleza y paletas
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class BeautyProfile:
    """Perfil de belleza del usuario"""
    user_id: str
    name: str
    skin_tone: str  # clara, media, oscura
    undertone: str  # frio, calido, neutro
    eye_color: str  # azul, verde, cafe, gris, negro
    hair_color: str  # rubio, castano, negro, rojo, gris
    hair_type: str  # liso, ondulado, rizado
    style_preference: str  # clasico, moderno, bohemio, minimalista
    created_at: str
    updated_at: str


@dataclass
class ColorPalette:
    """Paleta de colores generada"""
    palette_id: str
    user_id: str
    palette_type: str  # ropa, maquillaje, accesorios
    event_type: str  # casual, formal, fiesta, trabajo
    season: str  # primavera, verano, otono, invierno
    colors: List[Dict[str, str]]  # [{"hex": "#...", "name": "...", "category": "..."}]
    recommendations: Dict[str, Any]
    created_at: str


class BeautyModel:
    def __init__(self):
        """Inicializar modelo de belleza"""
        # Directorios de datos
        self.data_dir = "beauty_data"
        self.profiles_dir = os.path.join(self.data_dir, "profiles")
        self.palettes_dir = os.path.join(self.data_dir, "palettes")
        
        # Crear directorios
        os.makedirs(self.profiles_dir, exist_ok=True)
        os.makedirs(self.palettes_dir, exist_ok=True)
        
        # Cargar base de datos de colores
        self.color_database = self._load_color_database()
    
    def _load_color_database(self) -> Dict[str, Any]:
        """Cargar base de datos de colores"""
        return {
            "skin_tones": {
                "clara": {
                    "base_colors": ["#F5E6D3", "#E8D4C2", "#F2E7D5"],
                    "avoid_colors": ["#000000", "#8B0000"],
                    "best_colors": ["#FFB6C1", "#87CEEB", "#DDA0DD"]
                },
                "media": {
                    "base_colors": ["#D4B896", "#C1A882", "#B8956A"],
                    "avoid_colors": ["#FFFF00", "#00FF00"],
                    "best_colors": ["#FF6347", "#32CD32", "#4169E1"]
                },
                "oscura": {
                    "base_colors": ["#8B5A3C", "#6B4423", "#4A2C17"],
                    "avoid_colors": ["#FFFFE0", "#F0F8FF"],
                    "best_colors": ["#FF4500", "#9400D3", "#FFD700"]
                }
            },
            "undertones": {
                "frio": {
                    "colors": ["#4169E1", "#9370DB", "#C71585", "#00CED1"],
                    "metals": ["plata", "platino", "oro_blanco"]
                },
                "calido": {
                    "colors": ["#FF6347", "#DAA520", "#D2691E", "#CD853F"],
                    "metals": ["oro", "cobre", "bronce"]
                },
                "neutro": {
                    "colors": ["#708090", "#BC8F8F", "#F0E68C", "#DEB887"],
                    "metals": ["oro_rosa", "acero", "oro_amarillo"]
                }
            },
            "eye_colors": {
                "azul": ["#4A90E2", "#2E5BBA", "#1E3A8A", "#87CEEB"],
                "verde": ["#10B981", "#059669", "#047857", "#32CD32"],
                "cafe": ["#92400E", "#B45309", "#D97706", "#8B4513"],
                "gris": ["#6B7280", "#4B5563", "#374151", "#708090"],
                "negro": ["#1F2937", "#111827", "#000000", "#2F4F4F"]
            },
            "hair_colors": {
                "rubio": ["#F59E0B", "#EAB308", "#CA8A04", "#FFD700"],
                "castano": ["#92400E", "#B45309", "#D97706", "#8B4513"],
                "negro": ["#1F2937", "#111827", "#000000", "#2F4F4F"],
                "rojo": ["#DC2626", "#B91C1C", "#991B1B", "#FF6347"],
                "gris": ["#6B7280", "#9CA3AF", "#D1D5DB", "#C0C0C0"]
            },
            "event_palettes": {
                "casual": {
                    "primary": ["#3B82F6", "#10B981", "#F59E0B", "#EF4444"],
                    "secondary": ["#93C5FD", "#6EE7B7", "#FCD34D", "#FCA5A5"],
                    "neutral": ["#F3F4F6", "#E5E7EB", "#D1D5DB"]
                },
                "formal": {
                    "primary": ["#1F2937", "#374151", "#6B7280", "#111827"],
                    "secondary": ["#9CA3AF", "#D1D5DB", "#F3F4F6"],
                    "accent": ["#1E40AF", "#7C2D12", "#064E3B"]
                },
                "fiesta": {
                    "primary": ["#EC4899", "#8B5CF6", "#06B6D4", "#F59E0B"],
                    "secondary": ["#F9A8D4", "#C4B5FD", "#67E8F9", "#FCD34D"],
                    "metallic": ["#FFD700", "#C0C0C0", "#B87333"]
                },
                "trabajo": {
                    "primary": ["#1E40AF", "#7C2D12", "#064E3B", "#92400E"],
                    "secondary": ["#DBEAFE", "#FEF3C7", "#D1FAE5", "#FED7AA"],
                    "neutral": ["#F8FAFC", "#F1F5F9", "#E2E8F0"]
                }
            },
            "makeup_categories": {
                "base": ["foundation", "concealer", "powder"],
                "ojos": ["eyeshadow", "eyeliner", "mascara", "eyebrow"],
                "labios": ["lipstick", "lip_gloss", "lip_liner"],
                "mejillas": ["blush", "bronzer", "highlighter"]
            },
            "clothing_categories": {
                "superior": ["blusa", "camisa", "sueter", "chaqueta"],
                "inferior": ["pantalon", "falda", "short", "vestido"],
                "calzado": ["zapatos", "botas", "sandalias", "tenis"],
                "accesorios": ["bolso", "collar", "aretes", "pulsera"]
            }
        }
    
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
            style_preference=profile_data.get("style_preference", "clasico"),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Guardar perfil
        self.save_profile(profile)
        return profile
    
    def save_profile(self, profile: BeautyProfile) -> bool:
        """Guardar perfil en archivo"""
        try:
            filename = f"profile_{profile.user_id}.json"
            filepath = os.path.join(self.profiles_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(asdict(profile), f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f" Error guardando perfil: {str(e)}")
            return False
    
    def load_profile(self, user_id: str) -> Optional[BeautyProfile]:
        """Cargar perfil por user_id"""
        try:
            filename = f"profile_{user_id}.json"
            filepath = os.path.join(self.profiles_dir, filename)
            
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return BeautyProfile(**data)
        except Exception as e:
            print(f" Error cargando perfil: {str(e)}")
            return None
    
    def save_palette(self, palette: ColorPalette) -> bool:
        """Guardar paleta generada"""
        try:
            filename = f"palette_{palette.palette_id}.json"
            filepath = os.path.join(self.palettes_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(asdict(palette), f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f" Error guardando paleta: {str(e)}")
            return False
    
    def load_user_palettes(self, user_id: str) -> List[ColorPalette]:
        """Cargar todas las paletas de un usuario"""
        palettes = []
        try:
            for filename in os.listdir(self.palettes_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.palettes_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if data.get('user_id') == user_id:
                        palettes.append(ColorPalette(**data))
        except Exception as e:
            print(f" Error cargando paletas: {str(e)}")
        
        # Ordenar por fecha de creación (más recientes primero)
        return sorted(palettes, key=lambda p: p.created_at, reverse=True)
    
    def list_profiles(self) -> List[str]:
        """Listar todos los perfiles disponibles"""
        profiles = []
        try:
            for filename in os.listdir(self.profiles_dir):
                if filename.startswith('profile_') and filename.endswith('.json'):
                    user_id = filename[8:-5]  # Extraer user_id del nombre
                    profiles.append(user_id)
        except Exception as e:
            print(f" Error listando perfiles: {str(e)}")
        
        return sorted(profiles)
    
    def get_color_recommendations(self, profile: BeautyProfile, palette_type: str, event_type: str) -> Dict[str, Any]:
        """Obtener recomendaciones de colores basadas en el perfil"""
        recommendations = {
            "primary_colors": [],
            "secondary_colors": [],
            "avoid_colors": [],
            "best_combinations": []
        }
        
        # Colores base según tono de piel
        if profile.skin_tone in self.color_database["skin_tones"]:
            skin_data = self.color_database["skin_tones"][profile.skin_tone]
            recommendations["primary_colors"].extend(skin_data["best_colors"])
            recommendations["avoid_colors"].extend(skin_data["avoid_colors"])
        
        # Colores según subtono
        if profile.undertone in self.color_database["undertones"]:
            undertone_data = self.color_database["undertones"][profile.undertone]
            recommendations["secondary_colors"].extend(undertone_data["colors"])
        
        # Colores según ojos
        if profile.eye_color in self.color_database["eye_colors"]:
            recommendations["primary_colors"].extend(
                self.color_database["eye_colors"][profile.eye_color][:2]
            )
        
        # Colores según evento
        if event_type in self.color_database["event_palettes"]:
            event_colors = self.color_database["event_palettes"][event_type]
            recommendations["secondary_colors"].extend(event_colors.get("primary", []))
        
        return recommendations
    
    def delete_profile(self, user_id: str) -> bool:
        """Eliminar perfil"""
        try:
            filename = f"profile_{user_id}.json"
            filepath = os.path.join(self.profiles_dir, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            print(f" Error eliminando perfil: {str(e)}")
            return False


# Testing del modelo
if __name__ == "__main__":
    beauty = BeautyModel()
    
    print(" Testing Beauty Model...")
    
    # Crear perfil de prueba
    profile_data = {
        "user_id": "maria_123",
        "name": "María",
        "skin_tone": "media",
        "undertone": "calido",
        "eye_color": "cafe",
        "hair_color": "castano",
        "style_preference": "moderno"
    }
    
    profile = beauty.create_profile(profile_data)
    print(f" Perfil creado: {profile.name}")
    
    # Cargar perfil
    loaded_profile = beauty.load_profile("maria_123")
    print(f" Perfil cargado: {loaded_profile.name if loaded_profile else 'No encontrado'}")
    
    # Obtener recomendaciones
    recommendations = beauty.get_color_recommendations(profile, "ropa", "casual")
    print(f" Recomendaciones: {len(recommendations['primary_colors'])} colores primarios")
    
    print(" Beauty Model funcionando correctamente")