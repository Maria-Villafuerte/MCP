#sleep_coach_dataclases.py
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

# Modelos de datos
class Chronotype(Enum):
    MORNING_LARK = "morning_lark"  # Alondra matutina
    NIGHT_OWL = "night_owl"       # Búho nocturno
    INTERMEDIATE = "intermediate"  # Intermedio

class SleepGoal(Enum):
    BETTER_QUALITY = "better_quality"
    MORE_ENERGY = "more_energy"
    WEIGHT_LOSS = "weight_loss"
    STRESS_REDUCTION = "stress_reduction"
    ATHLETIC_PERFORMANCE = "athletic_performance"
    COGNITIVE_PERFORMANCE = "cognitive_performance"

@dataclass
class UserProfile:
    name: str
    age: int | None = None
    chronotype: Chronotype | None = None
    current_bedtime: str | None = None
    current_wake_time: str | None = None
    sleep_duration_hours: float | None = None
    goals: List[SleepGoal] = None
    work_schedule: str | None = None
    exercise_time: str | None = None
    caffeine_cutoff: str | None = None
    screen_time_before_bed: int | None = None
    stress_level: int | None = None
    sleep_quality_rating: int | None = None

@dataclass
class SleepRecommendation:
    category: str
    recommendation: str
    priority: int  # 1 = alta, 2 = media, 3 = baja
    timeframe: str
    expected_benefit: str