import json
import re
from typing import Optional, Dict, Any, Union, List
from logger import logger


def robust_json_parse(text: str) -> Optional[Union[Dict[str, Any], List[Any]]]:
    """
    Надежный парсинг JSON с множественными стратегиями очистки
    """
    if not text or not text.strip():
        return None
    
    # Стратегия 1: Прямой парсинг
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    
    # Стратегия 2: Очистка от markdown обрамлений
    cleaned = clean_markdown_json(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # Стратегия 3: Извлечение первого валидного JSON
    extracted = extract_first_json(text)
    if extracted:
        try:
            return json.loads(extracted)
        except json.JSONDecodeError:
            pass
    
    # Стратегия 4: Попытка исправить распространенные ошибки
    fixed = fix_common_json_errors(text)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass
    
    logger.error(f"Не удалось распарсить JSON после всех попыток: {text[:200]}...")
    return None


def clean_markdown_json(text: str) -> str:
    """Очистка JSON от markdown обрамлений"""
    text = text.strip()
    
    # Убираем тройные ```
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1])
    
    # Убираем префикс json после ```
    text = re.sub(r"^```\s*json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```\s*$", "", text)
    
    return text.strip()


def extract_first_json(text: str) -> Optional[str]:
    """Извлечение первого валидного JSON объекта или массива"""
    # Ищем JSON объект
    obj_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, flags=re.DOTALL)
    # Ищем JSON массив
    arr_match = re.search(r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]', text, flags=re.DOTALL)
    
    candidates = []
    if obj_match:
        candidates.append((obj_match.start(), obj_match.group(0)))
    if arr_match:
        candidates.append((arr_match.start(), arr_match.group(0)))
    
    # Возвращаем тот, что начинается раньше
    if candidates:
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]
    
    return None


def fix_common_json_errors(text: str) -> str:
    """Исправление распространенных ошибок в JSON"""
    # Убираем лишние запятые перед закрывающими скобками
    text = re.sub(r',\s*([}\]])', r'\1', text)
    
    # Исправляем одинарные кавычки на двойные
    text = re.sub(r"'([^']*)':", r'"\1":', text)
    text = re.sub(r":\s*'([^']*)'", r': "\1"', text)
    
    # Убираем trailing commas
    text = re.sub(r',(\s*[}\]])', r'\1', text)
    
    # Исправляем ошибки с лишними словами в массивах (например: "текст", и "другой текст")
    text = re.sub(r'",\s+и\s+"', '", "', text)
    text = re.sub(r'",\s+и\s+\'', '", \'', text)
    
    # Убираем лишние слова между элементами массива
    text = re.sub(r'",\s+\w+\s+"', '", "', text)
    
    return text


def validate_json_structure(data: Union[Dict, List], expected_type: str = "auto") -> bool:
    """
    Валидация структуры JSON
    expected_type: "object", "array", "auto"
    """
    if expected_type == "object":
        return isinstance(data, dict)
    elif expected_type == "array":
        return isinstance(data, list)
    else:  # auto
        return isinstance(data, (dict, list)) 