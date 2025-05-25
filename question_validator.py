import re
from typing import List
from config import VALIDATION


class QuestionValidator:
    """Валидатор вопросов для проверки закрытой формы"""
    
    def __init__(self):
        self.open_keywords = VALIDATION.open_keywords
        self.choice_patterns = VALIDATION.choice_patterns
        self.valid_closed_patterns = VALIDATION.valid_closed_patterns

    def is_closed_form_question(self, question: str) -> bool:
        """Проверка, является ли вопрос закрытым (да/нет)"""
        question_lower = question.lower()
        
        # 1. Проверяем на открытые ключевые слова
        for keyword in self.open_keywords:
            if keyword in question_lower:
                return False
        
        # 2. Проверяем на вопросы с выбором (или/либо)
        for pattern in self.choice_patterns:
            if re.search(pattern, question_lower):
                return False
        
        # 3. Проверяем на вопросы, требующие развернутого ответа
        complex_patterns = [
            r'какую?\s+(сумму|количество|цену|стоимость)',
            r'сколько\s+(времени|денег|людей)',
            r'в\s+каком\s+(формате|виде|размере)',
            r'для\s+каких?\s+(целей|задач)',
            r'на\s+какой\s+(платформе|основе)',
        ]
        
        for pattern in complex_patterns:
            if re.search(pattern, question_lower):
                return False
        
        # 4. Проверяем правильную структуру закрытых вопросов
        for pattern in self.valid_closed_patterns:
            if re.search(pattern, question_lower):
                return True
        
        # 5. Если вопрос не начинается с правильных слов - считаем открытым
        if not re.search(r'^(это|является|будет|требует|нужно|нужна|планируете|хотите|можете|есть|имеется|существует|согласны|готовы)', question_lower) and not re.search(r'\bнужн[аоы]\b', question_lower):
            return False
        
        return True

    def extract_questions_from_text(self, text: str) -> List[str]:
        """Извлечение вопросов из текста"""
        questions = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Ищем строки, начинающиеся с цифры и точки
            if re.match(r'^\d+\.', line):
                question = re.sub(r'^\d+\.\s*', '', line).strip()
                if question and question.endswith('?'):
                    questions.append(question)
        
        return questions

    def validate_questions_list(self, questions: List[str]) -> List[str]:
        """Валидация списка вопросов, возвращает только валидные"""
        return [q for q in questions if self.is_closed_form_question(q)]

    def get_validation_errors(self, question: str) -> List[str]:
        """Получение списка ошибок валидации для вопроса"""
        errors = []
        question_lower = question.lower()
        
        # Проверяем на открытые слова
        found_open_keywords = [kw for kw in self.open_keywords if kw in question_lower]
        if found_open_keywords:
            errors.append(f"Содержит открытые слова: {', '.join(found_open_keywords)}")
        
        # Проверяем на выбор
        for pattern in self.choice_patterns:
            if re.search(pattern, question_lower):
                errors.append("Содержит варианты выбора (или/либо)")
                break
        
        # Проверяем структуру
        has_valid_structure = any(re.search(pattern, question_lower) for pattern in self.valid_closed_patterns)
        if not has_valid_structure:
            errors.append("Неправильная структура для закрытого вопроса")
        
        return errors 