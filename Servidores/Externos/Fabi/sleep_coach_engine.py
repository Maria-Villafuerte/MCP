#sleep_coach_engine.py
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sleep_coach_dataClasses import Chronotype, SleepGoal, UserProfile, SleepRecommendation

class SleepCoachEngine:
    """Motor principal de recomendaciones de sueño"""
    
    def __init__(self):
        self.user_profiles: Dict[str, UserProfile] = {}
        self.sleep_data = self._load_sleep_knowledge()
    
    def _load_sleep_knowledge(self) -> Dict:
        """Base de conocimientos sobre sueño"""
        return {
            "optimal_sleep_duration": {
                "18-25": (7, 9),
                "26-64": (7, 9),
                "65+": (7, 8)
            },
            "chronotype_patterns": {
                Chronotype.MORNING_LARK: {
                    "optimal_bedtime": "21:30-22:30",
                    "optimal_wake": "06:00-07:00",
                    "energy_peak": "10:00-12:00",
                    "afternoon_dip": "13:00-15:00"
                },
                Chronotype.NIGHT_OWL: {
                    "optimal_bedtime": "23:30-00:30",
                    "optimal_wake": "07:30-08:30",
                    "energy_peak": "18:00-22:00",
                    "afternoon_dip": "14:00-16:00"
                },
                Chronotype.INTERMEDIATE: {
                    "optimal_bedtime": "22:30-23:30",
                    "optimal_wake": "06:30-07:30",
                    "energy_peak": "10:00-14:00",
                    "afternoon_dip": "13:00-15:00"
                }
            },
            "sleep_hygiene_rules": [
                "Mantener horarios consistentes todos los días",
                "Evitar cafeína 6-8 horas antes de dormir",
                "No usar pantallas 1-2 horas antes de dormir",
                "Mantener el dormitorio fresco (18-20°C)",
                "Ejercitarse regularmente, pero no 3 horas antes de dormir",
                "Evitar comidas pesadas 3 horas antes de dormir",
                "Crear un ritual de relajación pre-sueño",
                "Usar la cama solo para dormir y actividad íntima"
            ]
        }
    
    def analyze_sleep_pattern(self, user_id: str) -> Dict[str, str]:
        """Analiza el patrón de sueño del usuario con la información disponible"""
        if user_id not in self.user_profiles:
            raise ValueError(f"No profile found for user_id: {user_id}")

        profile = self.user_profiles[user_id]
        analysis = {}

        # Duración del sueño
        if profile.sleep_duration_hours is not None and profile.age is not None:
            optimal_min, optimal_max = self._get_optimal_duration(profile.age)
            if profile.sleep_duration_hours < optimal_min:
                analysis["duration"] = "short"
            elif profile.sleep_duration_hours > optimal_max:
                analysis["duration"] = "long"
            else:
                analysis["duration"] = "optimal"
        else:
            analysis["duration"] = "unknown"

        # Cronotipo
        if profile.chronotype and profile.current_wake_time:
            analysis["chronotype_alignment"] = self._analyze_chronotype_alignment(
                profile.chronotype, profile.current_wake_time
            )

        # Higiene del sueño
        if profile.screen_time_before_bed is not None:
            if profile.screen_time_before_bed > 60:
                analysis["screen_time"] = "excessive"
            else:
                analysis["screen_time"] = "healthy"

        if profile.caffeine_cutoff:
            analysis["caffeine_cutoff"] = profile.caffeine_cutoff

        if profile.exercise_time:
            analysis["exercise_time"] = profile.exercise_time

        if profile.stress_level is not None:
            analysis["stress"] = (
                "high" if profile.stress_level > 7 else "moderate" if profile.stress_level > 4 else "low"
            )

        return analysis

    def generate_personalized_recommendations(self, user_id: str) -> List[SleepRecommendation]:
        """Genera recomendaciones personalizadas basadas en el análisis del sueño"""
        if user_id not in self.user_profiles:
            raise ValueError(f"No profile found for user_id: {user_id}")

        profile = self.user_profiles[user_id]
        analysis = self.analyze_sleep_pattern(user_id)
        recommendations: List[SleepRecommendation] = []

        # Recomendaciones según duración
        if analysis.get("duration") == "short":
            recommendations.append(
                SleepRecommendation(
                    type="duration",
                    message="Intenta extender tu tiempo de sueño. La mayoría de adultos necesita entre 7–9 horas.",
                    priority="high"
                )
            )
        elif analysis.get("duration") == "long":
            recommendations.append(
                SleepRecommendation(
                    type="duration",
                    message="Tu duración de sueño es mayor a lo recomendado. Revisa si te sientes descansado o si puede haber causas médicas.",
                    priority="medium"
                )
            )

        # Recomendaciones según cronotipo
        if profile.chronotype and analysis.get("chronotype_alignment"):
            recommendations.extend(
                self._get_schedule_recommendations(profile, analysis["chronotype_alignment"])
            )

        # Higiene del sueño
        recommendations.extend(self._get_hygiene_recommendations(profile, analysis))

        # Estrés
        if analysis.get("stress") == "high":
            recommendations.append(
                SleepRecommendation(
                    type="stress",
                    message="Tu nivel de estrés parece alto. Considera técnicas de relajación como meditación o respiración profunda.",
                    priority="high"
                )
            )

        return recommendations
    
    def create_weekly_schedule(self, user_id: str) -> Dict[str, Any]:
        """Crea un horario semanal optimizado"""
        if user_id not in self.user_profiles:
            return {"error": "Usuario no encontrado"}
        
        profile = self.user_profiles[user_id]
        chronotype_data = self.sleep_data["chronotype_patterns"][profile.chronotype]
        
        # Horario base optimizado
        optimal_bedtime = self._parse_time_range(chronotype_data["optimal_bedtime"])[0]
        optimal_wake = self._parse_time_range(chronotype_data["optimal_wake"])[0]
        
        schedule = {
            "bedtime_routine": self._create_bedtime_routine(profile),
            "weekly_schedule": {},
            "wake_routine": self._create_wake_routine(profile),
            "tips": []
        }
        
        # Crear horario para cada día
        days = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        for day in days:
            is_weekend = day in ["sábado", "domingo"]
            
            # Permitir 30-60 min más tarde en fines de semana
            bedtime_adj = 30 if is_weekend else 0
            wake_adj = 60 if is_weekend else 0
            
            bedtime = self._add_minutes_to_time(optimal_bedtime.strftime("%H:%M"), bedtime_adj)
            wake_time = self._add_minutes_to_time(optimal_wake.strftime("%H:%M"), wake_adj)
            
            schedule["weekly_schedule"][day] = {
                "bedtime": bedtime,
                "wake_time": wake_time,
                "sleep_duration": self._calculate_duration(bedtime, wake_time)
            }
        
        return schedule
    
    def _get_schedule_recommendations(self, profile: UserProfile, analysis: Dict) -> List[SleepRecommendation]:
        """Recomendaciones específicas de horarios"""
        recommendations = []
        
        if analysis.get("duration") == "insufficient":
            gap = analysis.get("duration_gap", 0)
            rec = SleepRecommendation(
                category="Horario",
                recommendation=f"Aumenta tu tiempo de sueño en {gap:.1f} horas. Considera acostarte {int(gap*60)} minutos más temprano.",
                priority=1,
                timeframe="1-2 semanas",
                expected_benefit="Mejor recuperación, más energía y mejor concentración"
            )
            recommendations.append(rec)
        
        if not analysis.get("chronotype_alignment", {}).get("aligned", True):
            chronotype_name = "madrugador" if profile.chronotype == Chronotype.MORNING_LARK else "nocturno" if profile.chronotype == Chronotype.NIGHT_OWL else "intermedio"
            rec = SleepRecommendation(
                category="Cronotipos",
                recommendation=f"Tu horario actual no está alineado con tu cronotipo {chronotype_name}. Ajusta gradualmente tus horarios de sueño.",
                priority=1,
                timeframe="2-4 semanas",
                expected_benefit="Mejor calidad de sueño y mayor energía durante el día"
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _get_hygiene_recommendations(self, profile: UserProfile) -> List[SleepRecommendation]:
        """Recomendaciones de higiene del sueño"""
        recommendations = []
        
        if profile.screen_time_before_bed > 60:
            rec = SleepRecommendation(
                category="Higiene del sueño",
                recommendation=f"Reduce el tiempo de pantalla antes de dormir de {profile.screen_time_before_bed} a máximo 30 minutos, idealmente cero.",
                priority=2,
                timeframe="1 semana",
                expected_benefit="Mejor producción de melatonina y conciliación más rápida"
            )
            recommendations.append(rec)
        
        if not profile.caffeine_cutoff:
            rec = SleepRecommendation(
                category="Higiene del sueño",
                recommendation="Establece un horario límite para el consumo de cafeína, idealmente 6-8 horas antes de dormir.",
                priority=2,
                timeframe="3-5 días",
                expected_benefit="Mejor conciliación del sueño y sueño más profundo"
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _get_goal_specific_recommendations(self, profile: UserProfile) -> List[SleepRecommendation]:
        """Recomendaciones específicas por objetivos"""
        recommendations = []
        
        for goal in profile.goals:
            if goal == SleepGoal.BETTER_QUALITY:
                rec = SleepRecommendation(
                    category="Calidad del sueño",
                    recommendation="Implementa una rutina de relajación 1 hora antes de dormir: lectura, meditación o estiramientos suaves.",
                    priority=2,
                    timeframe="2-3 semanas",
                    expected_benefit="Sueño más profundo y reparador"
                )
                recommendations.append(rec)
            
            elif goal == SleepGoal.MORE_ENERGY:
                rec = SleepRecommendation(
                    category="Energía",
                    recommendation="Exponte a luz natural en los primeros 30 minutos después de despertar para regular tu ritmo circadiano.",
                    priority=1,
                    timeframe="1-2 semanas",
                    expected_benefit="Mayor alerta matutina y mejor energía durante el día"
                )
                recommendations.append(rec)
            
            elif goal == SleepGoal.STRESS_REDUCTION:
                rec = SleepRecommendation(
                    category="Manejo del estrés",
                    recommendation="Practica técnicas de respiración profunda o meditación mindfulness antes de dormir.",
                    priority=2,
                    timeframe="2-4 semanas",
                    expected_benefit="Reducción del cortisol nocturno y mejor relajación"
                )
                recommendations.append(rec)
        
        return recommendations
    
    def _get_problem_specific_recommendations(self, profile: UserProfile, analysis: Dict) -> List[SleepRecommendation]:
        """Recomendaciones para problemas específicos detectados"""
        recommendations = []
        
        if profile.stress_level > 7:
            rec = SleepRecommendation(
                category="Manejo del estrés",
                recommendation="Dado tu alto nivel de estrés, considera técnicas de relajación progresiva muscular antes de dormir.",
                priority=1,
                timeframe="1-3 semanas",
                expected_benefit="Reducción de la tensión corporal y mejor conciliación"
            )
            recommendations.append(rec)
        
        if profile.sleep_quality_rating < 5:
            rec = SleepRecommendation(
                category="Calidad del sueño",
                recommendation="Evalúa tu ambiente de sueño: temperatura (18-20°C), oscuridad completa y silencio o ruido blanco.",
                priority=1,
                timeframe="Inmediato",
                expected_benefit="Mejor mantenimiento del sueño y menos despertares"
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _create_bedtime_routine(self, profile: UserProfile) -> List[Dict]:
        """Crea una rutina personalizada para antes de dormir"""
        routine = []
        
        # Rutina base adaptada al cronotipos
        if profile.chronotype == Chronotype.NIGHT_OWL:
            routine.extend([
                {"time": "-90 min", "activity": "Última comida ligera permitida"},
                {"time": "-60 min", "activity": "Apagar dispositivos electrónicos"},
                {"time": "-45 min", "activity": "Ducha tibia o baño relajante"},
                {"time": "-30 min", "activity": "Lectura o música suave"},
                {"time": "-15 min", "activity": "Técnicas de respiración o meditación"},
                {"time": "0 min", "activity": "Acostarse con luces apagadas"}
            ])
        else:
            routine.extend([
                {"time": "-75 min", "activity": "Última comida ligera permitida"},
                {"time": "-60 min", "activity": "Apagar pantallas y actividades estimulantes"},
                {"time": "-30 min", "activity": "Actividad relajante (lectura, estiramiento)"},
                {"time": "-10 min", "activity": "Preparar el ambiente (temperatura, oscuridad)"},
                {"time": "0 min", "activity": "Acostarse"}
            ])
        
        return routine
    
    def _create_wake_routine(self, profile: UserProfile) -> List[Dict]:
        """Crea una rutina matutina optimizada"""
        routine = [
            {"time": "0 min", "activity": "Despertar (evitar snooze)"},
            {"time": "+5 min", "activity": "Hidratarse con un vaso de agua"},
            {"time": "+10 min", "activity": "Exposición a luz natural (ventana o exterior)"},
            {"time": "+15 min", "activity": "Movimiento suave (estiramientos)"}
        ]
        
        if profile.chronotype == Chronotype.MORNING_LARK:
            routine.append({"time": "+30 min", "activity": "Ejercicio moderado (opcional)"})
        
        return routine
    
    # Métodos auxiliares
    def _get_optimal_duration(self, age: int) -> tuple:
        """Obtiene duración óptima de sueño por edad"""
        if age <= 25:
            return self.sleep_data["optimal_sleep_duration"]["18-25"]
        elif age <= 64:
            return self.sleep_data["optimal_sleep_duration"]["26-64"]
        else:
            return self.sleep_data["optimal_sleep_duration"]["65+"]
    
    def _check_chronotype_alignment(self, profile: UserProfile, chronotype_data: Dict) -> Dict:
        """Verifica alineación con cronotipos"""
        current_bed = datetime.strptime(profile.current_bedtime, "%H:%M").time()
        current_wake = datetime.strptime(profile.current_wake_time, "%H:%M").time()
        
        optimal_bed_range = self._parse_time_range(chronotype_data["optimal_bedtime"])
        optimal_wake_range = self._parse_time_range(chronotype_data["optimal_wake"])
        
        bed_aligned = optimal_bed_range[0] <= current_bed <= optimal_bed_range[1]
        wake_aligned = optimal_wake_range[0] <= current_wake <= optimal_wake_range[1]
        
        return {
            "aligned": bed_aligned and wake_aligned,
            "bedtime_aligned": bed_aligned,
            "wake_aligned": wake_aligned
        }
    
    def _parse_time_range(self, time_range: str) -> tuple:
        """Parsea rango de tiempo como '21:30-22:30'"""
        start, end = time_range.split("-")
        return (
            datetime.strptime(start, "%H:%M").time(),
            datetime.strptime(end, "%H:%M").time()
        )
    
    def _add_minutes_to_time(self, time_str: str, minutes: int) -> str:
        """Agrega minutos a un tiempo"""
        dt = datetime.strptime(time_str, "%H:%M")
        dt += timedelta(minutes=minutes)
        return dt.strftime("%H:%M")
    
    def _calculate_duration(self, bedtime: str, wake_time: str) -> str:
        """Calcula duración entre dos tiempos"""
        bed_dt = datetime.strptime(bedtime, "%H:%M")
        wake_dt = datetime.strptime(wake_time, "%H:%M")
        
        # Si wake_time es menor, es del día siguiente
        if wake_dt < bed_dt:
            wake_dt += timedelta(days=1)
        
        duration = wake_dt - bed_dt
        hours = duration.total_seconds() / 3600
        return f"{hours:.1f} horas"