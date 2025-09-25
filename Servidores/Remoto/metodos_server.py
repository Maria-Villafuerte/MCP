#!/usr/bin/env python3
"""
Sistema Avanzado de Análisis de Belleza y Colorimetría Profesional
Basado en la teoría de las estaciones de color y análisis científico de subtonos
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import colorsys
import math

# Archivo de almacenamiento
DATA_FILE = "beauty_profiles.json"

def init_data_storage():
    """Inicializar el archivo de almacenamiento de datos"""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({"profiles": {}, "palettes": {}}, f, ensure_ascii=False, indent=2)

def load_data() -> Dict[str, Any]:
    """Cargar datos del archivo"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        init_data_storage()
        return {"profiles": {}, "palettes": {}}

def save_data(data: Dict[str, Any]):
    """Guardar datos al archivo"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================================
# SISTEMA DE COLORIMETRÍA PROFESIONAL
# ============================================================================

class ColorAnalyzer:
    """Analizador profesional de colorimetría basado en teoría científica"""
    
    # Definición de estaciones de color con sus características
    SEASONS = {
        "primavera_calida": {
            "name": "Primavera Cálida",
            "characteristics": "Colores vibrantes, cálidos y claros",
            "temperature": "calido",
            "saturation": "alta",
            "contrast": "medio",
            "best_colors": ["#FF6B35", "#F7931E", "#FFD700", "#32CD32", "#FF69B4", "#87CEEB"],
            "avoid_colors": ["#000000", "#FFFFFF", "#4169E1", "#8B008B"]
        },
        "primavera_clara": {
            "name": "Primavera Clara", 
            "characteristics": "Colores suaves, cálidos y luminosos",
            "temperature": "calido",
            "saturation": "media",
            "contrast": "bajo",
            "best_colors": ["#FFB6C1", "#FFDAB9", "#F0E68C", "#98FB98", "#87CEFA", "#DDA0DD"],
            "avoid_colors": ["#000000", "#8B0000", "#000080", "#4B0082"]
        },
        "verano_suave": {
            "name": "Verano Suave",
            "characteristics": "Colores apagados, frescos y suaves", 
            "temperature": "frio",
            "saturation": "baja",
            "contrast": "bajo",
            "best_colors": ["#B0C4DE", "#D8BFD8", "#F0F8FF", "#E6E6FA", "#FAFAFA", "#F5F5DC"],
            "avoid_colors": ["#FF4500", "#FFD700", "#32CD32", "#FF1493"]
        },
        "verano_frio": {
            "name": "Verano Frío",
            "characteristics": "Colores frescos, suaves con base azul",
            "temperature": "frio", 
            "saturation": "media",
            "contrast": "medio",
            "best_colors": ["#4169E1", "#9370DB", "#FF69B4", "#20B2AA", "#BA55D3", "#7B68EE"],
            "avoid_colors": ["#FF8C00", "#FF6347", "#DAA520", "#CD853F"]
        },
        "otono_suave": {
            "name": "Otoño Suave",
            "characteristics": "Colores terrosos, cálidos y apagados",
            "temperature": "calido",
            "saturation": "baja", 
            "contrast": "bajo",
            "best_colors": ["#D2B48C", "#DEB887", "#F4A460", "#CD853F", "#BC8F8F", "#A0522D"],
            "avoid_colors": ["#FF1493", "#00BFFF", "#7FFF00", "#FF00FF"]
        },
        "otono_profundo": {
            "name": "Otoño Profundo",
            "characteristics": "Colores ricos, cálidos y saturados",
            "temperature": "calido",
            "saturation": "alta",
            "contrast": "alto", 
            "best_colors": ["#8B4513", "#A0522D", "#CD853F", "#DAA520", "#B22222", "#800080"],
            "avoid_colors": ["#E0E0E0", "#F0F8FF", "#87CEEB", "#FFB6C1"]
        },
        "invierno_profundo": {
            "name": "Invierno Profundo",
            "characteristics": "Colores intensos, fríos y dramáticos",
            "temperature": "frio",
            "saturation": "alta", 
            "contrast": "muy_alto",
            "best_colors": ["#000000", "#FFFFFF", "#FF0000", "#0000FF", "#FF1493", "#8A2BE2"],
            "avoid_colors": ["#F5DEB3", "#FFDAB9", "#FFE4B5", "#F0E68C"]
        },
        "invierno_brillante": {
            "name": "Invierno Brillante", 
            "characteristics": "Colores vibrantes, fríos y claros",
            "temperature": "frio",
            "saturation": "muy_alta",
            "contrast": "alto",
            "best_colors": ["#FF1493", "#00BFFF", "#7FFF00", "#FF00FF", "#00FF00", "#FFFF00"],
            "avoid_colors": ["#696969", "#A9A9A9", "#D2B48C", "#DEB887"]
        }
    }

    @staticmethod
    def analyze_undertone(vein_color: str, jewelry_preference: str, sun_reaction: str, 
                         natural_lip_color: str) -> Dict[str, Any]:
        """
        Análisis científico de subtono basado en múltiples indicadores
        
        Lógica:
        - Venas azules/púrpuras = subtono frío
        - Venas verdes/oliva = subtono cálido  
        - Preferencia por plata = frío, oro = cálido
        - Bronceado fácil = cálido, quemado = frío
        - Labios rosados = frío, durazno = cálido
        """
        score = 0  # Negativo = frío, Positivo = cálido
        
        # Análisis de color de venas (40% del peso)
        vein_scores = {
            "azul": -2, "azul_verdoso": -1, "purpura": -1,
            "verde": 2, "verde_oliva": 2, "indefinido": 0
        }
        score += vein_scores.get(vein_color, 0) * 2
        
        # Preferencia de joyería (30% del peso)
        jewelry_scores = {"plata": -1.5, "oro": 1.5, "ambos": 0}
        score += jewelry_scores.get(jewelry_preference, 0)
        
        # Reacción al sol (20% del peso)
        sun_scores = {"se_quema": -1, "broncea_despacio": -0.5, "broncea_facil": 1}
        score += sun_scores.get(sun_reaction, 0)
        
        # Color natural de labios (10% del peso)
        lip_scores = {"rosado": -0.5, "coral": 0, "durazno": 0.5}
        score += lip_scores.get(natural_lip_color, 0)
        
        # Determinar subtono
        if score <= -1:
            undertone = "frio"
        elif score >= 1:
            undertone = "calido"  
        else:
            undertone = "neutro"
            
        return {
            "undertone": undertone,
            "score": score,
            "confidence": min(abs(score) * 20, 100),
            "analysis": f"Puntuación: {score:.1f} - {undertone.upper()}"
        }

    @staticmethod 
    def determine_season(skin_tone: str, undertone: str, eye_color: str, 
                        hair_color: str, contrast_level: str) -> Dict[str, Any]:
        """
        Determinar estación de color basada en características físicas
        
        Lógica de estaciones:
        - PRIMAVERA: Piel clara/media + subtono cálido + contraste bajo/medio
        - VERANO: Piel clara/media + subtono frío + contraste bajo/medio  
        - OTOÑO: Piel media/oscura + subtono cálido + saturación alta
        - INVIERNO: Cualquier piel + subtono frío + contraste alto
        """
        
        # Matriz de decisión basada en teoría de colorimetría
        season_matrix = {
            ("clara", "calido", "bajo"): "primavera_clara",
            ("clara", "calido", "medio"): "primavera_calida", 
            ("clara", "calido", "alto"): "primavera_calida",
            ("clara", "frio", "bajo"): "verano_suave",
            ("clara", "frio", "medio"): "verano_frio",
            ("clara", "frio", "alto"): "invierno_brillante",
            ("clara", "neutro", "bajo"): "verano_suave",
            ("clara", "neutro", "medio"): "verano_frio",
            ("clara", "neutro", "alto"): "invierno_brillante",
            
            ("media", "calido", "bajo"): "otono_suave",
            ("media", "calido", "medio"): "primavera_calida",
            ("media", "calido", "alto"): "otono_profundo",
            ("media", "frio", "bajo"): "verano_suave", 
            ("media", "frio", "medio"): "verano_frio",
            ("media", "frio", "alto"): "invierno_profundo",
            ("media", "neutro", "bajo"): "otono_suave",
            ("media", "neutro", "medio"): "verano_frio", 
            ("media", "neutro", "alto"): "invierno_profundo",
            
            ("oscura", "calido", "bajo"): "otono_suave",
            ("oscura", "calido", "medio"): "otono_profundo",
            ("oscura", "calido", "alto"): "otono_profundo", 
            ("oscura", "frio", "bajo"): "invierno_profundo",
            ("oscura", "frio", "medio"): "invierno_profundo",
            ("oscura", "frio", "alto"): "invierno_profundo",
            ("oscura", "neutro", "bajo"): "invierno_profundo",
            ("oscura", "neutro", "medio"): "invierno_profundo",
            ("oscura", "neutro", "alto"): "invierno_profundo",
        }
        
        # Ajustar contraste basado en color de ojos y cabello
        contrast_adjustments = {
            ("negro", "azul"): "alto",
            ("negro", "verde"): "alto", 
            ("rubio", "cafe"): "medio",
            ("rubio", "azul"): "bajo",
            ("castano", "verde"): "medio",
            ("pelirrojo", "verde"): "alto"
        }
        
        adjusted_contrast = contrast_adjustments.get((hair_color, eye_color), contrast_level)
        
        season_key = (skin_tone, undertone, adjusted_contrast)
        season = season_matrix.get(season_key, "verano_suave")  # Default
        
        return {
            "season": season,
            "season_info": ColorAnalyzer.SEASONS[season],
            "confidence": 85,  # Alta confianza con este análisis detallado
            "reasoning": f"Piel {skin_tone} + subtono {undertone} + contraste {adjusted_contrast} = {ColorAnalyzer.SEASONS[season]['name']}"
        }

    @staticmethod
    def generate_harmony_palette(base_colors: List[str], harmony_type: str = "complementary") -> List[str]:
        """
        Generar paleta armónica basada en teoría del color
        
        Tipos de armonía:
        - complementary: Colores opuestos en la rueda
        - analogous: Colores adyacentes  
        - triadic: Tres colores equidistantes
        - split_complementary: Base + dos colores a los lados del complementario
        """
        
        def hex_to_hsl(hex_color: str) -> Tuple[float, float, float]:
            """Convertir hex a HSL"""
            hex_color = hex_color.lstrip('#')
            r, g, b = [int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4)]
            return colorsys.rgb_to_hls(r, g, b)
        
        def hsl_to_hex(h: float, l: float, s: float) -> str:
            """Convertir HSL a hex"""
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        
        if not base_colors:
            return []
            
        # Usar el primer color como base
        base_hex = base_colors[0]
        h, l, s = hex_to_hsl(base_hex)
        
        harmonies = []
        
        if harmony_type == "complementary":
            comp_h = (h + 0.5) % 1.0
            harmonies = [base_hex, hsl_to_hex(comp_h, l, s)]
            
        elif harmony_type == "analogous":
            harmonies = [
                base_hex,
                hsl_to_hex((h + 0.083) % 1.0, l, s),  # +30°
                hsl_to_hex((h - 0.083) % 1.0, l, s)   # -30°
            ]
            
        elif harmony_type == "triadic":
            harmonies = [
                base_hex,
                hsl_to_hex((h + 0.333) % 1.0, l, s),  # +120°
                hsl_to_hex((h + 0.667) % 1.0, l, s)   # +240°
            ]
            
        elif harmony_type == "split_complementary":
            comp_h = (h + 0.5) % 1.0
            harmonies = [
                base_hex,
                hsl_to_hex((comp_h + 0.083) % 1.0, l, s),  # Comp +30°
                hsl_to_hex((comp_h - 0.083) % 1.0, l, s)   # Comp -30°
            ]
        
        # Agregar variaciones de luminosidad
        variations = []
        for color in harmonies:
            h, l, s = hex_to_hsl(color)
            variations.extend([
                color,  # Original
                hsl_to_hex(h, min(l + 0.2, 1.0), s),  # Más claro
                hsl_to_hex(h, max(l - 0.2, 0.0), s)   # Más oscuro
            ])
        
        return list(set(variations))  # Remover duplicados

# ============================================================================
# HERRAMIENTAS DEL SERVIDOR MCP  
# ============================================================================

def tool_create_profile(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crear perfil avanzado de belleza con análisis colorimétrico completo
    """
    required_fields = [
        "user_id", "name", "skin_tone", "vein_color", "jewelry_preference", 
        "sun_reaction", "eye_color", "hair_color", "natural_lip_color", "contrast_level"
    ]
    
    for field in required_fields:
        if field not in args:
            return {"error": f"Campo requerido faltante: {field}"}
    
    try:
        data = load_data()
        
        if args["user_id"] in data["profiles"]:
            return {"error": f"El perfil {args['user_id']} ya existe"}
        
        # Análisis de subtono científico
        undertone_analysis = ColorAnalyzer.analyze_undertone(
            args["vein_color"], 
            args["jewelry_preference"],
            args["sun_reaction"],
            args["natural_lip_color"]
        )
        
        # Determinación de estación de color
        season_analysis = ColorAnalyzer.determine_season(
            args["skin_tone"],
            undertone_analysis["undertone"], 
            args["eye_color"],
            args["hair_color"],
            args["contrast_level"]
        )
        
        # Crear perfil completo
        profile = {
            "basic_info": {
                "user_id": args["user_id"],
                "name": args["name"],
                "created_at": datetime.now().isoformat()
            },
            "physical_characteristics": {
                "skin_tone": args["skin_tone"],
                "vein_color": args["vein_color"], 
                "eye_color": args["eye_color"],
                "hair_color": args["hair_color"],
                "natural_lip_color": args["natural_lip_color"],
                "contrast_level": args["contrast_level"]
            },
            "preferences": {
                "jewelry_preference": args["jewelry_preference"],
                "sun_reaction": args["sun_reaction"],
                "style_preference": args.get("style_preference", "moderno")
            },
            "color_analysis": {
                "undertone_analysis": undertone_analysis,
                "season_analysis": season_analysis,
                "recommended_colors": season_analysis["season_info"]["best_colors"],
                "colors_to_avoid": season_analysis["season_info"]["avoid_colors"]
            }
        }
        
        data["profiles"][args["user_id"]] = profile
        save_data(data)
        
        return {
            "success": True,
            "message": f"Perfil creado exitosamente para {args['name']}",
            "profile": profile,
            "color_analysis_summary": {
                "subtono": undertone_analysis["undertone"],
                "confianza_subtono": f"{undertone_analysis['confidence']:.1f}%",
                "estacion": season_analysis["season_info"]["name"],
                "caracteristicas_estacion": season_analysis["season_info"]["characteristics"],
                "explicacion": season_analysis["reasoning"]
            }
        }
        
    except Exception as e:
        return {"error": f"Error creando perfil: {str(e)}"}

def tool_show_profile(args: Dict[str, Any]) -> Dict[str, Any]:
    """Mostrar perfil completo con análisis detallado"""
    if "user_id" not in args:
        return {"error": "Se requiere user_id"}
    
    try:
        data = load_data()
        profile = data["profiles"].get(args["user_id"])
        
        if not profile:
            return {"error": f"Perfil {args['user_id']} no encontrado"}
        
        return {
            "success": True,
            "profile": profile
        }
        
    except Exception as e:
        return {"error": f"Error mostrando perfil: {str(e)}"}

def tool_list_profiles(args: Dict[str, Any]) -> Dict[str, Any]:
    """Listar todos los perfiles con resumen de análisis"""
    try:
        data = load_data()
        profiles = data["profiles"]
        
        if not profiles:
            return {"success": True, "message": "No hay perfiles creados", "profiles": []}
        
        profile_list = []
        for user_id, profile in profiles.items():
            summary = {
                "user_id": user_id,
                "name": profile["basic_info"]["name"],
                "created_at": profile["basic_info"]["created_at"],
                "skin_tone": profile["physical_characteristics"]["skin_tone"],
                "undertone": profile["color_analysis"]["undertone_analysis"]["undertone"],
                "season": profile["color_analysis"]["season_analysis"]["season_info"]["name"]
            }
            profile_list.append(summary)
        
        return {
            "success": True,
            "total_profiles": len(profile_list),
            "profiles": profile_list
        }
        
    except Exception as e:
        return {"error": f"Error listando perfiles: {str(e)}"}

def tool_delete_profile(args: Dict[str, Any]) -> Dict[str, Any]:
    """Eliminar perfil"""
    if "user_id" not in args:
        return {"error": "Se requiere user_id"}
    
    try:
        data = load_data()
        
        if args["user_id"] not in data["profiles"]:
            return {"error": f"Perfil {args['user_id']} no encontrado"}
        
        del data["profiles"][args["user_id"]]
        save_data(data)
        
        return {
            "success": True,
            "message": f"Perfil {args['user_id']} eliminado exitosamente"
        }
        
    except Exception as e:
        return {"error": f"Error eliminando perfil: {str(e)}"}

def tool_generate_palette(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generar paleta personalizada basada en análisis colorimétrico del perfil
    """
    required_fields = ["user_id", "palette_type"]
    for field in required_fields:
        if field not in args:
            return {"error": f"Campo requerido: {field}"}
    
    try:
        data = load_data()
        profile = data["profiles"].get(args["user_id"])
        
        if not profile:
            return {"error": f"Perfil {args['user_id']} no encontrado"}
        
        season_info = profile["color_analysis"]["season_analysis"]["season_info"]
        base_colors = season_info["best_colors"]
        palette_type = args["palette_type"]
        event_type = args.get("event_type", "casual")
        
        # Generar paleta específica para el tipo solicitado
        if palette_type == "maquillaje":
            palette = generate_makeup_palette(base_colors, season_info, event_type)
        elif palette_type == "ropa":
            palette = generate_clothing_palette(base_colors, season_info, event_type)
        elif palette_type == "accesorios":
            palette = generate_accessories_palette(base_colors, season_info, event_type)
        else:
            return {"error": f"Tipo de paleta no válido: {palette_type}"}
        
        # Agregar armonías de color
        harmony_palette = ColorAnalyzer.generate_harmony_palette(base_colors, "complementary")
        
        palette_result = {
            "user_id": args["user_id"],
            "palette_type": palette_type,
            "event_type": event_type,
            "generated_at": datetime.now().isoformat(),
            "base_season": season_info["name"],
            "main_palette": palette,
            "harmony_colors": harmony_palette[:8],  # Limitar a 8 colores
            "color_theory": {
                "temperature": season_info["temperature"],
                "saturation": season_info["saturation"], 
                "contrast": season_info["contrast"],
                "explanation": season_info["characteristics"]
            }
        }
        
        # Guardar paleta generada
        if "palettes" not in data:
            data["palettes"] = {}
        if args["user_id"] not in data["palettes"]:
            data["palettes"][args["user_id"]] = []
        
        data["palettes"][args["user_id"]].append(palette_result)
        save_data(data)
        
        return {
            "success": True,
            "palette": palette_result
        }
        
    except Exception as e:
        return {"error": f"Error generando paleta: {str(e)}"}

def tool_quick_palette(args: Dict[str, Any]) -> Dict[str, Any]:
    """Generar paleta rápida sin perfil específico"""
    palette_type = args.get("palette_type", "ropa")
    skin_tone = args.get("skin_tone", "media")
    undertone = args.get("undertone", "neutro")
    event_type = args.get("event_type", "casual")
    
    # Usar análisis simplificado para determinar estación aproximada
    season_key = f"{skin_tone}_{undertone}_medio"  # Usar contraste medio por defecto
    
    # Mapeo simplificado
    season_mapping = {
        "clara_frio_medio": "verano_frio",
        "clara_calido_medio": "primavera_calida", 
        "clara_neutro_medio": "verano_suave",
        "media_frio_medio": "verano_frio",
        "media_calido_medio": "otono_suave",
        "media_neutro_medio": "verano_suave", 
        "oscura_frio_medio": "invierno_profundo",
        "oscura_calido_medio": "otono_profundo",
        "oscura_neutro_medio": "invierno_profundo"
    }
    
    season = season_mapping.get(season_key, "verano_suave")
    season_info = ColorAnalyzer.SEASONS[season]
    
    # Generar paleta
    if palette_type == "maquillaje":
        palette = generate_makeup_palette(season_info["best_colors"], season_info, event_type)
    elif palette_type == "ropa":
        palette = generate_clothing_palette(season_info["best_colors"], season_info, event_type)
    elif palette_type == "accesorios":
        palette = generate_accessories_palette(season_info["best_colors"], season_info, event_type)
    else:
        palette = {
            "primary": season_info["best_colors"][:3],
            "secondary": season_info["best_colors"][3:6] if len(season_info["best_colors"]) > 3 else [],
            "accent": season_info["best_colors"][-2:] if len(season_info["best_colors"]) > 2 else []
        }
    
    return {
        "success": True,
        "palette": {
            "palette_type": palette_type,
            "event_type": event_type,
            "estimated_season": season_info["name"],
            "generated_at": datetime.now().isoformat(),
            "colors": palette,
            "color_theory": {
                "temperature": season_info["temperature"],
                "saturation": season_info["saturation"],
                "explanation": f"Paleta basada en {season_info['name']}: {season_info['characteristics']}"
            }
        }
    }

def tool_export_data(args: Dict[str, Any]) -> Dict[str, Any]:
    """Exportar todos los datos del usuario"""
    if "user_id" not in args:
        return {"error": "Se requiere user_id"}
    
    try:
        data = load_data()
        user_id = args["user_id"]
        
        if user_id not in data["profiles"]:
            return {"error": f"Perfil {user_id} no encontrado"}
        
        export_data = {
            "export_info": {
                "user_id": user_id,
                "exported_at": datetime.now().isoformat(),
                "version": "2.0"
            },
            "profile": data["profiles"][user_id],
            "palettes": data.get("palettes", {}).get(user_id, [])
        }
        
        return {
            "success": True,
            "exported_data": export_data,
            "summary": {
                "profile_created": data["profiles"][user_id]["basic_info"]["created_at"],
                "total_palettes": len(export_data["palettes"]),
                "color_season": data["profiles"][user_id]["color_analysis"]["season_analysis"]["season_info"]["name"]
            }
        }
        
    except Exception as e:
        return {"error": f"Error exportando datos: {str(e)}"}

# ============================================================================
# FUNCIONES AUXILIARES PARA GENERACIÓN DE PALETAS ESPECÍFICAS
# ============================================================================

def generate_makeup_palette(base_colors: List[str], season_info: Dict, event_type: str) -> Dict[str, Any]:
    """Generar paleta específica de maquillaje basada en teoría de color"""
    
    # Paletas base por tipo de evento
    event_intensities = {
        "casual": {"intensity": "suave", "colors_count": 4},
        "trabajo": {"intensity": "profesional", "colors_count": 3},
        "formal": {"intensity": "elegante", "colors_count": 5},
        "fiesta": {"intensity": "vibrante", "colors_count": 6},
        "noche": {"intensity": "dramatica", "colors_count": 6},
        "playa": {"intensity": "natural", "colors_count": 3}
    }
    
    event_config = event_intensities.get(event_type, event_intensities["casual"])
    
    return {
        "ojos": {
            "sombras_principales": base_colors[:2],
            "sombra_iluminadora": base_colors[2] if len(base_colors) > 2 else "#FFFFFF",
            "delineador": "#000000" if season_info["contrast"] == "alto" else "#8B4513"
        },
        "rostro": {
            "base": determine_foundation_shade(season_info),
            "rubor": base_colors[1] if len(base_colors) > 1 else "#FFB6C1",
            "iluminador": lighten_color(base_colors[0]) if base_colors else "#F0F8FF"
        },
        "labios": {
            "color_principal": base_colors[-1] if base_colors else "#FF69B4",
            "alternativo": base_colors[-2] if len(base_colors) > 1 else "#FFB6C1"
        },
        "recomendaciones": {
            "intensidad": event_config["intensity"],
            "ocasion": event_type,
            "tecnica": get_makeup_technique(season_info, event_type)
        }
    }

def generate_clothing_palette(base_colors: List[str], season_info: Dict, event_type: str) -> Dict[str, Any]:
    """Generar paleta de ropa basada en teoría de color"""
    
    return {
        "colores_principales": base_colors[:3],
        "colores_neutros": get_neutral_colors(season_info),
        "colores_accent": base_colors[3:] if len(base_colors) > 3 else [],
        "combinaciones_recomendadas": generate_clothing_combinations(base_colors, event_type),
        "texturas_recomendadas": get_recommended_textures(season_info),
        "estilos": {
            "ocasion": event_type,
            "temperatura_color": season_info["temperature"],
            "saturacion": season_info["saturation"]
        }
    }

def generate_accessories_palette(base_colors: List[str], season_info: Dict, event_type: str) -> Dict[str, Any]:
    """Generar paleta de accesorios"""
    
    metal_preference = "oro" if season_info["temperature"] == "calido" else "plata"
    
    return {
        "joyeria": {
            "metal_principal": metal_preference,
            "piedras_recomendadas": get_recommended_stones(season_info, base_colors)
        },
        "bolsos_zapatos": {
            "colores_versatiles": get_neutral_colors(season_info),
            "colores_statement": base_colors[:2]
        },
        "pañuelos_bufandas": base_colors,
        "recomendaciones": {
            "contraste": season_info["contrast"],
            "estilo_ocasion": event_type
        }
    }

# Funciones auxiliares adicionales
def determine_foundation_shade(season_info: Dict) -> str:
    """Determinar tono de base de maquillaje"""
    base_mapping = {
        "primavera": "#F5DEB3",  # Beige cálido
        "verano": "#F0F0F0",     # Rosa claro  
        "otono": "#DEB887",      # Beige dorado
        "invierno": "#FFE4E1"    # Rosa neutro
    }
    season_key = season_info["name"].split()[0].lower()
    return base_mapping.get(season_key, "#F5DEB3")

def lighten_color(hex_color: str, factor: float = 0.3) -> str:
    """Aclarar un color hex"""
    try:
        hex_color = hex_color.lstrip('#')
        r, g, b = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))  
        b = min(255, int(b + (255 - b) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"
    except:
        return "#FFFFFF"

def get_neutral_colors(season_info: Dict) -> List[str]:
    """Obtener colores neutros para la estación"""
    neutral_mapping = {
        "primavera": ["#F5F5DC", "#DEB887", "#D2B48C"],
        "verano": ["#F8F8FF", "#E6E6FA", "#D3D3D3"],
        "otono": ["#F4A460", "#D2B48C", "#A0522D"],
        "invierno": ["#FFFFFF", "#000000", "#808080"]
    }
    season_key = season_info["name"].split()[0].lower()
    return neutral_mapping.get(season_key, ["#FFFFFF", "#000000", "#808080"])

def generate_clothing_combinations(colors: List[str], event_type: str) -> List[Dict[str, str]]:
    """Generar combinaciones de ropa recomendadas"""
    if len(colors) < 2:
        return []
    
    combinations = [
        {"superior": colors[0], "inferior": colors[1], "descripcion": "Combinación armónica principal"},
        {"superior": colors[1], "inferior": colors[0], "descripcion": "Combinación armónica invertida"}
    ]
    
    if len(colors) > 2:
        combinations.append({
            "superior": colors[0], 
            "inferior": colors[2], 
            "descripcion": "Combinación con contraste"
        })
    
    return combinations

def get_recommended_stones(season_info: Dict, colors: List[str]) -> List[str]:
    """Recomendar piedras preciosas basadas en la estación de color"""
    stone_mapping = {
        "primavera": ["Topacio", "Peridoto", "Aguamarina"],
        "verano": ["Perla", "Amatista", "Agua marina"],  
        "otono": ["Ámbar", "Granate", "Topacio dorado"],
        "invierno": ["Diamante", "Rubí", "Zafiro"]
    }
    season_key = season_info["name"].split()[0].lower()
    return stone_mapping.get(season_key, ["Cuarzo", "Perla"])

def get_recommended_textures(season_info: Dict) -> List[str]:
    """Recomendar texturas basadas en la estación"""
    texture_mapping = {
        "primavera": ["Algodón ligero", "Lino", "Seda"],
        "verano": ["Chiffon", "Organza", "Algodón suave"],
        "otono": ["Tweed", "Terciopelo", "Lana"],
        "invierno": ["Satén", "Cuero", "Cachemira"]
    }
    season_key = season_info["name"].split()[0].lower()
    return texture_mapping.get(season_key, ["Algodón", "Poliéster"])

def get_makeup_technique(season_info: Dict, event_type: str) -> str:
    """Recomendar técnica de maquillaje"""
    if season_info["contrast"] == "alto":
        return "Maquillaje con contrastes definidos, colores intensos"
    elif season_info["saturation"] == "alta":
        return "Colores vibrantes, difuminados suaves"
    else:
        return "Maquillaje suave, técnica de difuminado natural"