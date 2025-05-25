"""Утилиты для AI-агента брифинга"""

import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

def clean_text(text: str) -> str:
    """Очистка текста от лишних символов"""
    if not text:
        return ""
    
    # Убираем лишние пробелы и переносы
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Убираем специальные символы в начале/конце
    text = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', text)
    
    return text

def extract_questions_from_text(text: str) -> List[str]:
    """Извлечение вопросов из текста"""
    if not text:
        return []
    
    # Паттерны для поиска вопросов
    patterns = [
        r'^\d+\.\s*(.+\?)\s*$',  # 1. Вопрос?
        r'^-\s*(.+\?)\s*$',      # - Вопрос?
        r'^•\s*(.+\?)\s*$',      # • Вопрос?
        r'^(.+\?)\s*$'           # Просто вопрос?
    ]
    
    questions = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        for pattern in patterns:
            match = re.match(pattern, line, re.MULTILINE)
            if match:
                question = clean_text(match.group(1))
                if question and question not in questions:
                    questions.append(question)
                break
    
    return questions

def validate_json_structure(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """Валидация структуры JSON"""
    errors = []
    
    for field in required_fields:
        if field not in data:
            errors.append(f"Отсутствует обязательное поле: {field}")
        elif not data[field]:
            errors.append(f"Поле {field} не может быть пустым")
    
    return errors

def format_time_ago(dt: datetime) -> str:
    """Форматирование времени в формате 'X минут назад'"""
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} дн. назад"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} ч. назад"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} мин. назад"
    else:
        return "только что"

def truncate_text(text: str, max_length: int = 100) -> str:
    """Обрезка текста с добавлением многоточия"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."

def safe_json_loads(text: str) -> Optional[Dict[str, Any]]:
    """Безопасная загрузка JSON с обработкой ошибок"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None

def ensure_directory(path: str) -> Path:
    """Создание директории если она не существует"""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def count_words(text: str) -> int:
    """Подсчет количества слов в тексте"""
    if not text:
        return 0
    return len(text.split())

def is_question(text: str) -> bool:
    """Проверка является ли текст вопросом"""
    if not text:
        return False
    
    text = text.strip()
    
    # Заканчивается на вопросительный знак
    if text.endswith('?'):
        return True
    
    # Начинается с вопросительных слов
    question_words = ['как', 'что', 'где', 'когда', 'почему', 'какой', 'какая', 'какие', 'сколько', 'кто', 'чем', 'зачем']
    first_word = text.lower().split()[0] if text.split() else ""
    
    return first_word in question_words

def generate_session_id() -> str:
    """Генерация уникального ID сессии"""
    from uuid import uuid4
    return str(uuid4())[:8]

def sanitize_filename(filename: str) -> str:
    """Очистка имени файла от недопустимых символов"""
    # Убираем недопустимые символы
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Ограничиваем длину
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename 