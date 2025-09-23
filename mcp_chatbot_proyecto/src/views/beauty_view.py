"""
Beauty View - Vista específica para el sistema de belleza
"""

from typing import Dict, List, Optional, Any
from models.beauty_model import BeautyProfile, ColorPalette


class BeautyView:
    def __init__(self):
        """Inicializar vista de belleza"""
        self.colors = {
            'header': '\033[95m',
            'blue': '\033[94m',
            'cyan': '\033[96m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'red': '\033[91m',
            'magenta': '\033[95m',
            'end': '\033[0m',
            'bold': '\033[1m',
            'underline': '\033[4m'
        }
    
    def show_beauty_help(self) -> str:
        """Mostrar ayuda completa del sistema de belleza"""
        help_text = f"""{self.colors['bold']}{self.colors['magenta']} SISTEMA DE BELLEZA - AYUDA COMPLETA{self.colors['end']}

{self.colors['cyan']} GESTIÓN DE PERFILES:{self.colors['end']}
{self.colors['blue']}  /beauty create_profile{self.colors['end']}          - Crear perfil personalizado interactivo
{self.colors['blue']}  /beauty profile <user_id>{self.colors['end']}       - Ver perfil específico
{self.colors['blue']}  /beauty list_profiles{self.colors['end']}           - Listar todos los perfiles
{self.colors['blue']}  /beauty update_profile <user_id>{self.colors['end']} - Actualizar perfil existente
{self.colors['blue']}  /beauty delete_profile <user_id>{self.colors['end']} - Eliminar perfil

{self.colors['cyan']} GENERACIÓN DE PALETAS:{self.colors['end']}
{self.colors['blue']}  /palette ropa <user_id> <evento>{self.colors['end']}     - Paleta de ropa
{self.colors['blue']}  /palette maquillaje <user_id> <evento>{self.colors['end']} - Paleta de maquillaje
{self.colors['blue']}  /palette accesorios <user_id> <evento>{self.colors['end']} - Paleta de accesorios
{self.colors['blue']}  /palette quick <tipo> <evento>{self.colors['end']}        - Paleta rápida sin perfil

{self.colors['cyan']} HISTORIAL Y GESTIÓN:{self.colors['end']}
{self.colors['blue']}  /beauty history <user_id>{self.colors['end']}       - Ver historial de paletas
{self.colors['blue']}  /beauty stats <user_id>{self.colors['end']}         - Estadísticas de uso
{self.colors['blue']}  /beauty export <user_id>{self.colors['end']}        - Exportar datos de usuario

{self.colors['cyan']} TIPOS DE EVENTO:{self.colors['end']}
{self.colors['green']}  casual, formal, fiesta, trabajo, cita, deporte, viaje{self.colors['end']}

{self.colors['cyan']} EJEMPLOS DE USO:{self.colors['end']}
{self.colors['green']}  /beauty create_profile{self.colors['end']}
{self.colors['green']}  /palette ropa maria_123 formal{self.colors['end']}
{self.colors['green']}  /palette maquillaje maria_123 fiesta{self.colors['end']}
{self.colors['green']}  /palette quick ropa casual{self.colors['end']}

{self.colors['yellow']} El sistema usa teoría del color y tu perfil personal para recomendaciones precisas{self.colors['end']}"""
        
        return help_text
    
    def collect_profile_data(self) -> Optional[Dict[str, str]]:
        """Recopilar datos para crear perfil de forma interactiva"""
        print(f"\n{self.colors['bold']}{self.colors['magenta']} CREACIÓN DE PERFIL DE BELLEZA{self.colors['end']}")
        print(f"{self.colors['cyan']}{'='*50}{self.colors['end']}")
        
        try:
            # Información básica
            user_id = self._prompt_input(" ID de usuario (único)", required=True)
            name = self._prompt_input(" Nombre completo", required=True)
            
            # Características físicas
            print(f"\n{self.colors['yellow']} CARACTERÍSTICAS FÍSICAS:{self.colors['end']}")
            
            skin_tone = self._prompt_choice(
                " Tono de piel",
                ["clara", "media", "oscura"],
                descriptions=["Piel clara/pálida", "Piel media/morena", "Piel oscura/negra"]
            )
            
            undertone = self._prompt_choice(
                "Subtono de piel",
                ["frio", "calido", "neutro"],
                descriptions=["Venas azules, mejor en plata", "Venas verdes, mejor en oro", "Difícil determinar"]
            )
            
            eye_color = self._prompt_choice(
                " Color de ojos",
                ["azul", "verde", "cafe", "gris", "negro"],
                descriptions=["Ojos azules", "Ojos verdes", "Ojos café/marrones", "Ojos grises", "Ojos negros"]
            )
            
            hair_color = self._prompt_choice(
                " Color de cabello",
                ["rubio", "castano", "negro", "rojo", "gris"],
                descriptions=["Cabello rubio", "Cabello castaño", "Cabello negro", "Cabello rojo/pelirrojo", "Cabello gris/canoso"]
            )
            
            hair_type = self._prompt_choice(
                " Tipo de cabello",
                ["liso", "ondulado", "rizado"],
                descriptions=["Cabello liso", "Cabello ondulado", "Cabello rizado"]
            )
            
            # Preferencias de estilo
            print(f"\n{self.colors['yellow']} PREFERENCIAS DE ESTILO:{self.colors['end']}")
            
            style_preference = self._prompt_choice(
                " Estilo preferido",
                ["clasico", "moderno", "bohemio", "minimalista", "romantico", "edgy"],
                descriptions=[
                    "Clásico/elegante", "Moderno/contemporáneo", "Bohemio/libre", 
                    "Minimalista/simple", "Romántico/femenino", "Edgy/atrevido"
                ]
            )
            
            # Información adicional opcional
            print(f"\n{self.colors['yellow']} INFORMACIÓN ADICIONAL (opcional):{self.colors['end']}")
            
            age_range = self._prompt_choice(
                " Rango de edad",
                ["15-20", "21-30", "31-40", "41-50", "51+"],
                required=False
            )
            
            profession = self._prompt_input(" Profesión/Estilo de vida", required=False)
            
            # Compilar datos
            profile_data = {
                "user_id": user_id,
                "name": name,
                "skin_tone": skin_tone,
                "undertone": undertone,
                "eye_color": eye_color,
                "hair_color": hair_color,
                "hair_type": hair_type,
                "style_preference": style_preference
            }
            
            # Agregar datos opcionales
            if age_range:
                profile_data["age_range"] = age_range
            if profession:
                profile_data["profession"] = profession
            
            # Confirmación
            print(f"\n{self.colors['green']} PERFIL CREADO:{self.colors['end']}")
            self._show_profile_summary(profile_data)
            
            confirm = self._prompt_input("\n¿Guardar este perfil? (s/n)", required=True)
            if confirm.lower() in ['s', 'si', 'yes', 'y']:
                return profile_data
            else:
                print(f"{self.colors['yellow']} Perfil cancelado{self.colors['end']}")
                return None
                
        except KeyboardInterrupt:
            print(f"\n{self.colors['yellow']} Creación de perfil cancelada{self.colors['end']}")
            return None
    
    def _prompt_input(self, prompt: str, required: bool = False) -> Optional[str]:
        """Solicitar entrada de texto"""
        while True:
            try:
                response = input(f"{self.colors['blue']}{prompt}:{self.colors['end']} ").strip()
                
                if response or not required:
                    return response if response else None
                else:
                    print(f"{self.colors['red']} Este campo es obligatorio{self.colors['end']}")
                    
            except (KeyboardInterrupt, EOFError):
                return None
    
    def _prompt_choice(self, prompt: str, options: List[str], descriptions: List[str] = None, required: bool = True) -> Optional[str]:
        """Solicitar selección de opciones"""
        print(f"\n{self.colors['cyan']}{prompt}:{self.colors['end']}")
        
        for i, option in enumerate(options, 1):
            desc = f" - {descriptions[i-1]}" if descriptions else ""
            print(f"  {i}. {option}{desc}")
        
        while True:
            try:
                choice = input(f"\n{self.colors['blue']}Selección (1-{len(options)}){self.colors['end']}: ").strip()
                
                if not choice and not required:
                    return None
                
                if not choice:
                    print(f"{self.colors['red']} Selección requerida{self.colors['end']}")
                    continue
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(options):
                    return options[choice_num - 1]
                else:
                    print(f"{self.colors['red']} Selecciona un número entre 1 y {len(options)}{self.colors['end']}")
                    
            except ValueError:
                print(f"{self.colors['red']} Ingresa un número válido{self.colors['end']}")
            except (KeyboardInterrupt, EOFError):
                return None if not required else options[0]
    
    def _show_profile_summary(self, profile_data: Dict[str, str]) -> None:
        """Mostrar resumen del perfil"""
        print(f"   Nombre: {profile_data['name']}")
        print(f"   ID: {profile_data['user_id']}")
        print(f"   Tono de piel: {profile_data['skin_tone']} ({profile_data['undertone']})")
        print(f"   Ojos: {profile_data['eye_color']}")
        print(f"   Cabello: {profile_data['hair_color']} ({profile_data['hair_type']})")
        print(f"   Estilo: {profile_data['style_preference']}")
    
    def show_profile(self, profile: BeautyProfile) -> str:
        """Mostrar perfil de belleza formateado"""
        profile_text = f"""{self.colors['bold']}{self.colors['magenta']} PERFIL DE BELLEZA{self.colors['end']}

{self.colors['cyan']} INFORMACIÓN BÁSICA:{self.colors['end']}
   Nombre: {profile.name}
   ID: {profile.user_id}
   Creado: {profile.created_at[:19].replace('T', ' ')}
   Actualizado: {profile.updated_at[:19].replace('T', ' ')}

{self.colors['cyan']} CARACTERÍSTICAS FÍSICAS:{self.colors['end']}
   Tono de piel: {profile.skin_tone.title()}
  Subtono: {profile.undertone.title()}
   Color de ojos: {profile.eye_color.title()}
   Color de cabello: {profile.hair_color.title()}
   Tipo de cabello: {profile.hair_type.title()}

{self.colors['cyan']} ESTILO:{self.colors['end']}
   Preferencia: {profile.style_preference.title()}

{self.colors['green']} Perfil listo para generar paletas personalizadas{self.colors['end']}"""
        
        return profile_text
    
    def show_palette(self, palette: ColorPalette) -> str:
        """Mostrar paleta de colores formateada"""
        palette_text = f"""{self.colors['bold']}{self.colors['magenta']} PALETA DE COLORES{self.colors['end']}

{self.colors['cyan']} INFORMACIÓN GENERAL:{self.colors['end']}
   Tipo: {palette.palette_type.title()}
   Evento: {palette.event_type.title()}
   Estación: {palette.season.title()}
   Usuario: {palette.user_id}
   Creada: {palette.created_at[:19].replace('T', ' ')}

{self.colors['cyan']} COLORES RECOMENDADOS:{self.colors['end']}"""
        
        # Agrupar colores por categoría
        categories = {}
        for color in palette.colors:
            category = color.get('category', 'general')
            if category not in categories:
                categories[category] = []
            categories[category].append(color)
        
        for category, colors in categories.items():
            palette_text += f"\n{self.colors['yellow']}   {category.title()}:{self.colors['end']}"
            for color in colors:
                palette_text += f"\n    • {color['name']}: {color['hex']}"
        
        # Mostrar recomendaciones específicas
        if palette.recommendations:
            palette_text += f"\n\n{self.colors['cyan']} RECOMENDACIONES ESPECÍFICAS:{self.colors['end']}"
            for key, value in palette.recommendations.items():
                if isinstance(value, list):
                    palette_text += f"\n  {key.replace('_', ' ').title()}:"
                    for item in value[:3]:  # Mostrar solo los primeros 3
                        palette_text += f"\n    • {item}"
                else:
                    palette_text += f"\n  {key.replace('_', ' ').title()}: {value}"
        
        return palette_text
    
    def show_palette_history(self, palettes: List[ColorPalette], user_id: str) -> str:
        """Mostrar historial de paletas"""
        if not palettes:
            return f"{self.colors['yellow']} No hay paletas guardadas para {user_id}{self.colors['end']}"
        
        history_text = f"""{self.colors['bold']}{self.colors['magenta']} HISTORIAL DE PALETAS - {user_id.upper()}{self.colors['end']}

{self.colors['cyan']}Total de paletas: {len(palettes)}{self.colors['end']}

"""
        
        for i, palette in enumerate(palettes[:10], 1):  # Mostrar últimas 10
            date = palette.created_at[:10]  # Solo fecha
            history_text += f"{self.colors['green']}{i:2d}.{self.colors['end']} {date} | {palette.palette_type.title():12} | {palette.event_type.title():10} | {len(palette.colors)} colores\n"
        
        if len(palettes) > 10:
            history_text += f"\n{self.colors['yellow']}... y {len(palettes) - 10} paletas más{self.colors['end']}"
        
        return history_text
    
    def show_profile_list(self, profiles: List[str]) -> str:
        """Mostrar lista de perfiles disponibles"""
        if not profiles:
            return f"{self.colors['yellow']} No hay perfiles guardados{self.colors['end']}"
        
        list_text = f"""{self.colors['bold']}{self.colors['magenta']}👥 PERFILES DISPONIBLES{self.colors['end']}

{self.colors['cyan']}Total de perfiles: {len(profiles)}{self.colors['end']}

"""
        
        for i, profile_id in enumerate(profiles, 1):
            list_text += f"{self.colors['green']}{i:2d}.{self.colors['end']} {profile_id}\n"
        
        return list_text
    
    def format_color_sample(self, hex_color: str, name: str) -> str:
        """Formatear muestra de color (limitado en terminal)"""
        # En un terminal real, esto podría mostrar el color de fondo
        return f"  ■ {name}: {hex_color}"
    
    def collect_palette_preferences(self, palette_type: str, event_type: str) -> Dict[str, Any]:
        """Recopilar preferencias específicas para generación de paleta"""
        print(f"\n{self.colors['yellow']} PREFERENCIAS PARA PALETA DE {palette_type.upper()}{self.colors['end']}")
        print(f"{self.colors['yellow']}   Evento: {event_type.title()}{self.colors['end']}")
        
        preferences = {
            "palette_type": palette_type,
            "event_type": event_type
        }
        
        # Preferencias según tipo de paleta
        if palette_type == "ropa":
            preferences.update(self._collect_clothing_preferences())
        elif palette_type == "maquillaje":
            preferences.update(self._collect_makeup_preferences())
        elif palette_type == "accesorios":
            preferences.update(self._collect_accessories_preferences())
        
        return preferences
    
    def _collect_clothing_preferences(self) -> Dict[str, Any]:
        """Recopilar preferencias específicas de ropa"""
        prefs = {}
        
        season = self._prompt_choice(
            " Estación del año",
            ["primavera", "verano", "otono", "invierno"],
            required=False
        )
        if season:
            prefs["season"] = season
        
        intensity = self._prompt_choice(
            " Intensidad de colores",
            ["suave", "medio", "vibrante"],
            descriptions=["Colores pastel/suaves", "Colores equilibrados", "Colores vibrantes/intensos"],
            required=False
        )
        if intensity:
            prefs["color_intensity"] = intensity
        
        return prefs
    
    def _collect_makeup_preferences(self) -> Dict[str, Any]:
        """Recopilar preferencias específicas de maquillaje"""
        prefs = {}
        
        look_intensity = self._prompt_choice(
            " Intensidad del look",
            ["natural", "medio", "dramatico"],
            descriptions=["Look natural/día", "Look equilibrado", "Look dramático/noche"],
            required=False
        )
        if look_intensity:
            prefs["look_intensity"] = look_intensity
        
        focus_area = self._prompt_choice(
            " Área de enfoque",
            ["ojos", "labios", "equilibrado"],
            descriptions=["Enfoque en ojos", "Enfoque en labios", "Look equilibrado"],
            required=False
        )
        if focus_area:
            prefs["focus_area"] = focus_area
        
        return prefs
    
    def _collect_accessories_preferences(self) -> Dict[str, Any]:
        """Recopilar preferencias específicas de accesorios"""
        prefs = {}
        
        metal_preference = self._prompt_choice(
            " Preferencia de metales",
            ["oro", "plata", "oro_rosa", "mixto"],
            descriptions=["Tonos dorados", "Tonos plateados", "Oro rosado", "Combinación"],
            required=False
        )
        if metal_preference:
            prefs["metal_preference"] = metal_preference
        
        return prefs


# Testing de la vista de belleza
if __name__ == "__main__":
    beauty_view = BeautyView()
    
    print(" Testing Beauty View...")
    
    # Mostrar ayuda
    help_msg = beauty_view.show_beauty_help()
    print(help_msg[:300] + "...")
    
    # Crear datos de prueba
    from models.beauty_model import BeautyProfile, ColorPalette
    
    # Perfil de prueba
    test_profile = BeautyProfile(
        user_id="test_user",
        name="María Test",
        skin_tone="media",
        undertone="calido",
        eye_color="cafe",
        hair_color="castano",
        hair_type="ondulado",
        style_preference="moderno",
        created_at="2024-01-01T10:00:00",
        updated_at="2024-01-01T10:00:00"
    )
    
    # Mostrar perfil
    profile_display = beauty_view.show_profile(test_profile)
    print(f"\n{profile_display[:200]}...")
    
    print(" Beauty View funcionando correctamente")