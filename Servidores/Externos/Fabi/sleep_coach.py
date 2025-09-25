# sleep_coach.py
"""
Servidor MCP Sleep Coach - Recomendador de rutinas de sueño personalizado

Funcionalidades:
- Análisis personalizado de patrones de sueño
- Recomendaciones basadas en cronotipos
- Rutinas de higiene del sueño
- Planificación de horarios optimizados
- Seguimiento de hábitos
"""

import asyncio
import mcp.types as types
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server

from sleep_coach_engine import SleepCoachEngine
from sleep_coach_dataClasses import Chronotype, SleepGoal, UserProfile

# Servidor MCP
app = Server("sleep-coach")
engine = SleepCoachEngine()

@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Lista todas las herramientas disponibles"""
    return [
        types.Tool(
            name="create_user_profile",
            description="Crea un perfil personalizado de usuario con sus hábitos de sueño actuales",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID único del usuario"},
                    "name": {"type": "string", "description": "Nombre del usuario"},
                    "age": {"type": "integer", "description": "Edad del usuario"},
                    "chronotype": {"type": "string", "enum": ["morning_lark", "night_owl", "intermediate"]},
                    "current_bedtime": {"type": "string", "pattern": "^[0-2][0-9]:[0-5][0-9]$"},
                    "current_wake_time": {"type": "string", "pattern": "^[0-2][0-9]:[0-5][0-9]$"},
                    "sleep_duration_hours": {"type": "number", "minimum": 4, "maximum": 12},
                    "goals": {"type": "array", "items": {"type": "string","enum": ["better_quality","more_energy","weight_loss","stress_reduction","athletic_performance","cognitive_performance"]},"minItems": 1, "uniqueItems": True},
                    "work_schedule": {"type": "string"},
                    "exercise_time": {"type": "string", "description": "Horario de ejercicio opcional"},
                    "screen_time_before_bed": {"type": "integer", "minimum": 0},
                    "stress_level": {"type": "integer", "minimum": 1, "maximum": 10},
                    "sleep_quality_rating": {"type": "integer", "minimum": 1, "maximum": 10}
                },
                "required": ["user_id", "name", "age", "chronotype", "current_bedtime", "current_wake_time", "sleep_duration_hours", "goals", "work_schedule"]
            }
        ),
        types.Tool(
            name="update_user_profile",
            description="Actualiza uno o más campos del perfil de usuario",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "fields": {
                        "type": "object",
                        "description": "Campos a actualizar en el perfil",
                        "properties": {
                            "age": {"type": "integer", "description": "Edad del usuario"},
                            "chronotype": {"type": "string", "enum": ["morning_lark", "night_owl", "intermediate"]},
                            "current_bedtime": {"type": "string", "pattern": "^[0-2][0-9]:[0-5][0-9]$"},
                            "current_wake_time": {"type": "string", "pattern": "^[0-2][0-9]:[0-5][0-9]$"},
                            "sleep_duration_hours": {"type": "number", "minimum": 4, "maximum": 12},
                            "goals": {"type": "array", "items": {"type": "string","enum": ["better_quality","more_energy","weight_loss","stress_reduction","athletic_performance","cognitive_performance"]},"minItems": 1, "uniqueItems": True},
                            "work_schedule": {"type": "string"},
                            "exercise_time": {"type": "string", "description": "Horario de ejercicio opcional"},
                            "screen_time_before_bed": {"type": "integer", "minimum": 0},
                            "stress_level": {"type": "integer", "minimum": 1, "maximum": 10},
                            "sleep_quality_rating": {"type": "integer", "minimum": 1, "maximum": 10}
                        }
                    },
                    "additionalProperties": False 
                },
                "required": ["user_id", "fields"]
            }
        ),
        types.Tool(
            name="analyze_sleep_pattern",
            description="Analiza el patrón de sueño actual del usuario y detecta problemas",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID del usuario"}
                },
                "required": ["user_id"]
            }
        ),
        types.Tool(
            name="get_personalized_recommendations",
            description="Genera recomendaciones personalizadas basadas en el perfil del usuario",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID del usuario"}
                },
                "required": ["user_id"]
            }
        ),
        types.Tool(
            name="create_weekly_schedule",
            description="Crea un horario semanal optimizado con rutinas personalizadas",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "ID del usuario"}
                },
                "required": ["user_id"]
            }
        ),
        types.Tool(
            name="quick_sleep_advice",
            description="Proporciona consejos rápidos basados en una consulta específica",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Consulta específica sobre sueño"},
                    "user_context": {"type": "string", "description": "Contexto adicional del usuario (opcional)"}
                },
                "required": ["query"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Maneja las llamadas a herramientas"""

    if name == "ping":
        return [types.TextContent(type="text", text=f"pong! recibí: {arguments['msg']}")]
    
    if name == "create_user_profile":
        try:
            # Convertir goals de strings a enums
            goals = [SleepGoal(goal) for goal in arguments["goals"]]
            chronotype = Chronotype(arguments["chronotype"])
            
            profile = UserProfile(
                name=arguments["name"],
                age=arguments["age"],
                chronotype=chronotype,
                current_bedtime=arguments["current_bedtime"],
                current_wake_time=arguments["current_wake_time"],
                sleep_duration_hours=arguments["sleep_duration_hours"],
                goals=goals,
                work_schedule=arguments["work_schedule"],
                exercise_time=arguments.get("exercise_time"),
                screen_time_before_bed=arguments.get("screen_time_before_bed", 60),
                stress_level=arguments.get("stress_level", 5),
                sleep_quality_rating=arguments.get("sleep_quality_rating", 6)
            )
            
            engine.user_profiles[arguments["user_id"]] = profile
            
            return [types.TextContent(
                type="text",
                text=f"Perfil creado para {arguments['name']} ({arguments['user_id']})"
            )]

        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error creando perfil: {str(e)}"
            )]
        
    elif name == "update_user_profile":
        try:
            user_id = arguments["user_id"]
            if user_id not in engine.user_profiles:
                return [types.TextContent(type="text", text="Usuario no encontrado")]

            profile = engine.user_profiles[user_id]
            for field, value in arguments["fields"].items():
                if field == "chronotype":
                    value = Chronotype(value)
                elif field == "goals":
                    value = [SleepGoal(g) for g in value]
                setattr(profile, field, value)

            return [types.TextContent(
                type="text",
                text=f"Perfil actualizado para {profile.name} ({user_id}): {', '.join(arguments['fields'].keys())}"
            )]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error actualizando perfil: {str(e)}")]
    
    elif name == "analyze_sleep_pattern":
        try:
            analysis = engine.analyze_sleep_pattern(arguments["user_id"])
            
            if "error" in analysis:
                return [types.TextContent(type="text", text=f"{analysis['error']}")]
            
            result = "**ANÁLISIS DE PATRÓN DE SUEÑO**\n\n"
            
            # Análisis de duración
            duration_status = analysis["duration"]
            if duration_status == "insufficient":
                result += f"**Duración:** Insuficiente (faltan {analysis['duration_gap']:.1f} horas)\n"
            elif duration_status == "excessive":
                result += f"**Duración:** Excesiva (sobran {analysis['duration_gap']:.1f} horas)\n"
            else:
                result += "**Duración:** Óptima\n"
            
            # Alineación con cronotipos
            alignment = analysis["chronotype_alignment"]
            if alignment["aligned"]:
                result += "**Cronotipos:** Bien alineado\n"
            else:
                result += "**Cronotipos:** Desalineado\n"
                if not alignment["bedtime_aligned"]:
                    result += "  - Hora de dormir no óptima\n"
                if not alignment["wake_aligned"]:
                    result += "  - Hora de despertar no óptima\n"
            
            # Problemas de calidad
            if analysis["quality_issues"]:
                result += "\n**Problemas detectados:**\n"
                for issue in analysis["quality_issues"]:
                    result += f"  - {issue}\n"
            else:
                result += "\n**Calidad:** No se detectaron problemas mayores\n"
            
            return [types.TextContent(type="text", text=result)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error en análisis: {str(e)}")]
    
    elif name == "get_personalized_recommendations":
        try:
            recommendations = engine.generate_personalized_recommendations(arguments["user_id"])
            
            if not recommendations:
                return [types.TextContent(type="text", text="Usuario no encontrado")]
            
            result = "**RECOMENDACIONES PERSONALIZADAS**\n\n"
            
            # Agrupar por prioridad
            high_priority = [r for r in recommendations if r.priority == 1]
            medium_priority = [r for r in recommendations if r.priority == 2]
            low_priority = [r for r in recommendations if r.priority == 3]
            
            if high_priority:
                result += "**PRIORIDAD ALTA**\n"
                for rec in high_priority:
                    result += f"**{rec.category}:** {rec.recommendation}\n"
                    result += f"   ⏱️ Tiempo: {rec.timeframe} | 🎁 Beneficio: {rec.expected_benefit}\n\n"
            
            if medium_priority:
                result += "**PRIORIDAD MEDIA**\n"
                for rec in medium_priority:
                    result += f"**{rec.category}:** {rec.recommendation}\n"
                    result += f"   ⏱️ Tiempo: {rec.timeframe} | 🎁 Beneficio: {rec.expected_benefit}\n\n"
            
            if low_priority:
                result += "**RECOMENDACIONES ADICIONALES**\n"
                for rec in low_priority:
                    result += f"**{rec.category}:** {rec.recommendation}\n"
                    result += f"   ⏱️ Tiempo: {rec.timeframe} | 🎁 Beneficio: {rec.expected_benefit}\n\n"
            
            return [types.TextContent(type="text", text=result)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error generando recomendaciones: {str(e)}")]
    
    elif name == "create_weekly_schedule":
        try:
            schedule = engine.create_weekly_schedule(arguments["user_id"])
            
            if "error" in schedule:
                return [types.TextContent(type="text", text=f"{schedule['error']}")]
            
            result = "**HORARIO SEMANAL OPTIMIZADO**\n\n"
            
            # Horario por día
            for day, times in schedule["weekly_schedule"].items():
                result += f"**{day.upper()}**\n"
                result += f"   Dormir: {times['bedtime']}\n"
                result += f"   Despertar: {times['wake_time']}\n"
                result += f"   ⏱️ Duración: {times['sleep_duration']}\n\n"
            
            # Rutina de la noche
            result += "**RUTINA NOCTURNA**\n"
            for step in schedule["bedtime_routine"]:
                result += f"   {step['time']}: {step['activity']}\n"
            
            result += "\n**RUTINA MATUTINA**\n"
            for step in schedule["wake_routine"]:
                result += f"   {step['time']}: {step['activity']}\n"
            
            return [types.TextContent(type="text", text=result)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error creando horario: {str(e)}")]
    
    elif name == "quick_sleep_advice":
        try:
            query = arguments["query"].lower()
            user_context = arguments.get("user_context", "")
            
            # Base de consejos rápidos
            quick_advice = {
                "insomnio": [
                    "Levántate de la cama si no puedes dormir en 20 minutos",
                    "Prueba la técnica de respiración 4-7-8: inhala 4, mantén 7, exhala 8",
                    "Lee algo aburrido con luz tenue hasta sentir sueño",
                    "Evita mirar el reloj, aumenta la ansiedad"
                ],
                "despertar": [
                    "Usa un despertador de luz gradual",
                    "Bebe agua inmediatamente al despertar",
                    "Evita el botón snooze, fragmenta el sueño REM",
                    "Haz 5 minutos de ejercicio ligero"
                ],
                "sueño": [
                    "Mantén la habitación entre 18-20°C",
                    "Usa modo nocturno o filtros de luz azul",
                    "Prueba té de manzanilla o valeriana",
                    "Toma una ducha tibia 1-2 horas antes de dormir"
                ],
                "energia": [
                    "Consume cafeína solo en las primeras 6 horas del día",
                    "Exposición a luz natural en la mañana",
                    "Siesta de máximo 20 minutos antes de las 3 PM",
                    "Ejercicio regular mejora la calidad del sueño"
                ],
                "estres": [
                    "Escribe tus preocupaciones antes de dormir",
                    "Meditación mindfulness de 10 minutos",
                    "Música relajante o sonidos de la naturaleza",
                    "Relajación muscular progresiva"
                ]
            }
            
            advice_list = []
            
            # Buscar consejos relevantes
            for keyword, tips in quick_advice.items():
                if keyword in query:
                    advice_list.extend(tips)
            
            # Consejos generales si no hay match específico
            if not advice_list:
                advice_list = [
                    "Mantén horarios consistentes todos los días",
                    "Apaga pantallas 1 hora antes de dormir",
                    "Evita comidas pesadas 3 horas antes de acostarte",
                    "Limita la cafeína después de las 2 PM"
                ]
            
            result = "💡 **CONSEJOS RÁPIDOS PARA TU CONSULTA**\n\n"
            for tip in advice_list[:4]:  # Máximo 4 consejos
                result += f"{tip}\n"
            
            result += f"\n **Tu consulta:** {arguments['query']}\n"
            if user_context:
                result += f"**Contexto:** {user_context}\n"
            
            result += "\n Para recomendaciones más personalizadas, crea un perfil de usuario completo."
            
            return [types.TextContent(type="text", text=result)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error proporcionando consejo: {str(e)}")]
    
    else:
        return [types.TextContent(type="text", text=f"Herramienta desconocida: {name}")]

async def main():
    """Función principal del servidor"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream, 
            write_stream, 
            InitializationOptions(
                server_name="sleep-coach",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())