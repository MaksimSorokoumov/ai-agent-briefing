from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

class CompetencyLevel(Enum):
    """Уровни компетенций пользователя"""
    NOVICE = "новичок"
    BASIC = "базовый"
    INTERMEDIATE = "средний"
    ADVANCED = "продвинутый"
    EXPERT = "эксперт"

class QuestionComplexity(Enum):
    """Сложность вопросов"""
    SIMPLE = "простые"
    MEDIUM = "средние"
    COMPLEX = "сложные"

class SessionStep(Enum):
    """Этапы сессии"""
    INPUT_IDEA = "input_idea"
    COMPETENCY_ANALYSIS = "competency_analysis"
    GENERATE_QUESTIONS = "generate_questions"
    ANSWER_QUESTIONS = "answer_questions"
    REFORMULATE_QUESTIONS = "reformulate_questions"
    GENERATE_REFINED = "generate_refined"
    VALIDATE_IDEA = "validate_idea"
    COMPLETED = "completed"

@dataclass
class LMStudioConfig:
    """Конфигурация LM Studio"""
    base_url: str = "http://localhost:1234/v1"
    timeout: int = 180
    max_retries: int = 3
    default_model: str = "local-model"

@dataclass
class GenerationConfig:
    """Настройки генерации"""
    questions_count: int = 7
    competency_questions_count: int = 5
    max_tokens_questions: int = 8192
    max_tokens_refined: int = 8192
    max_tokens_final: int = 8192
    temperature_questions: float = 0.8
    temperature_refined: float = 0.6
    temperature_final: float = 0.5

@dataclass
class UIConfig:
    """Настройки интерфейса"""
    page_title: str = "AI-Агент Брифинга"
    page_icon: str = "🤖"
    layout: str = "wide"
    max_sessions_display: int = 10

@dataclass
class ValidationConfig:
    """Настройки валидации вопросов"""
    open_keywords: List[str] = None
    choice_patterns: List[str] = None
    valid_closed_patterns: List[str] = None
    
    def __post_init__(self):
        if self.open_keywords is None:
            self.open_keywords = ['как', 'что', 'где', 'когда', 'почему', 'какой', 'какая', 'какие', 'сколько', 'кто', 'чем', 'зачем']
        
        if self.choice_patterns is None:
            self.choice_patterns = [r'\sили\s', r'\sлибо\s', r'\sили\b', r'\bили\s']
        
        if self.valid_closed_patterns is None:
            self.valid_closed_patterns = [
                r'^(это|является|будет|требует|нужно|нужна|планируете|хотите|можете|есть|имеется|существует)',
                r'(ли\s)',
                r'^(согласны|готовы|хотели\s+бы|планируете|собираетесь)',
                r'^(предполагается|ожидается|планируется)',
                r'\bнужн[аоы]\b'
            ]

# Системные промпты
SYSTEM_PROMPTS = {
    "main": "Ты - AI-ассистент для проведения брифингов. Отвечай только на русском языке. Будь точным и конкретным.",
    "questions": "Ты специализируешься на создании уточняющих вопросов в закрытой форме (да/нет).",
    "competency": "Ты анализируешь компетенции пользователя и адаптируешь вопросы под его уровень.",
    "refinement": "Ты помогаешь уточнять и детализировать идеи на основе полученной информации.",
    "final": "Ты создаешь итоговые отчеты и рекомендации по результатам брифинга."
}

# Глобальные настройки
LM_STUDIO = LMStudioConfig()
GENERATION = GenerationConfig()
UI = UIConfig()
VALIDATION = ValidationConfig()

# Домены знаний
KNOWLEDGE_DOMAINS = [
    "Технологии/IT",
    "Медицина/Здравоохранение", 
    "Образование",
    "Бизнес/Предпринимательство",
    "Наука/Исследования",
    "Искусство/Творчество",
    "Спорт/Фитнес",
    "Финансы/Инвестиции",
    "Производство/Инженерия",
    "Социальные науки",
    "Экология/Природа",
    "Кулинария",
    "Общая"
] 