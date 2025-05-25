from typing import Dict, List, Any, Optional
from ai_client import AIClient
from question_validator import QuestionValidator
from models import Question, CompetencyProfile
from config import SYSTEM_PROMPTS, GENERATION
from logger import logger
import difflib


class QuestionGenerator:
    """Генератор адаптивных вопросов"""
    
    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client
        self.validator = QuestionValidator()

    def _is_similar_question(self, new_question: str, existing_questions: List[str], 
                           similarity_threshold: float = 0.7) -> bool:
        """
        Проверяет, является ли новый вопрос похожим на уже существующие
        
        Args:
            new_question: Новый вопрос для проверки
            existing_questions: Список уже заданных вопросов
            similarity_threshold: Порог схожести (0.0-1.0)
        
        Returns:
            True если вопрос слишком похож на существующий
        """
        if not existing_questions:
            return False
        
        # Нормализуем вопрос для сравнения
        normalized_new = self._normalize_question(new_question)
        
        for existing in existing_questions:
            normalized_existing = self._normalize_question(existing)
            
            # Проверяем точное совпадение
            if normalized_new == normalized_existing:
                return True
            
            # Проверяем схожесть с помощью difflib
            similarity = difflib.SequenceMatcher(None, normalized_new, normalized_existing).ratio()
            if similarity >= similarity_threshold:
                logger.info(f"Найден похожий вопрос (схожесть: {similarity:.2f}): '{new_question}' ~ '{existing}'")
                return True
        
        return False

    def _normalize_question(self, question: str) -> str:
        """Нормализует вопрос для сравнения"""
        # Убираем знаки препинания и приводим к нижнему регистру
        import re
        normalized = re.sub(r'[^\w\s]', '', question.lower())
        # Убираем лишние пробелы
        normalized = ' '.join(normalized.split())
        return normalized

    def _filter_duplicate_questions(self, questions: List[Question], 
                                  existing_questions: List[str]) -> List[Question]:
        """
        Фильтрует дубликаты из списка вопросов
        
        Args:
            questions: Список новых вопросов
            existing_questions: Список уже заданных вопросов
        
        Returns:
            Отфильтрованный список уникальных вопросов
        """
        unique_questions = []
        all_questions = existing_questions.copy()  # Копируем для отслеживания в рамках текущего списка
        
        for question in questions:
            if not self._is_similar_question(question.text, all_questions):
                unique_questions.append(question)
                all_questions.append(question.text)  # Добавляем в локальный список для проверки следующих
            else:
                logger.info(f"Исключен дубликат вопроса: '{question.text}'")
        
        return unique_questions

    def _regenerate_unique_questions(self, user_idea: str, competency_profile: CompetencyProfile,
                                   context_questions: List[str], existing_questions: List[str],
                                   needed_count: int) -> List[Question]:
        """
        Генерирует дополнительные уникальные вопросы если исходных недостаточно
        """
        if needed_count <= 0:
            return []
        
        domain = competency_profile.domain
        overall_level = competency_profile.overall_level.value
        
        # Формируем список уже заданных вопросов для промпта
        existing_questions_text = "\n".join([f"- {q}" for q in existing_questions[-10:]])  # Последние 10
        
        prompt = f"""
Пользователь описал идею: "{user_idea}"
Уровень компетенций: {overall_level} в области "{domain}"

УЖЕ ЗАДАННЫЕ ВОПРОСЫ (НЕ ПОВТОРЯТЬ):
{existing_questions_text}

Сгенерируй {needed_count} НОВЫХ уникальных вопросов в закрытой форме (да/нет), которые:
1. НЕ ПОВТОРЯЮТ уже заданные вопросы
2. НЕ ПОХОЖИ на уже заданные вопросы
3. Раскрывают ДРУГИЕ аспекты идеи
4. Соответствуют уровню {overall_level}

КАЖДЫЙ ВОПРОС ДОЛЖЕН:
- Требовать ответа ТОЛЬКО "Да" или "Нет"
- Начинаться со слов: "Это", "Планируете", "Требуется", "Нужно", "Хотите", "Будет", "Есть"
- НЕ ПОВТОРЯТЬ и НЕ БЫТЬ ПОХОЖИМИ на уже заданные вопросы
- Раскрывать НОВЫЕ аспекты идеи

Формат ответа:
1. [новый уникальный вопрос]?
2. [новый уникальный вопрос]?
...
"""

        response = self.ai_client.make_request(
            prompt,
            SYSTEM_PROMPTS["questions"],
            GENERATION.max_tokens_questions,
            GENERATION.temperature_questions
        )
        
        questions_text = self.validator.extract_questions_from_text(response)
        new_questions = []
        
        for question_text in questions_text:
            if len(new_questions) >= needed_count:
                break
                
            if self.validator.is_closed_form_question(question_text):
                # Проверяем уникальность
                if not self._is_similar_question(question_text, existing_questions + [q.text for q in new_questions]):
                    new_questions.append(Question(
                        text=question_text,
                        adapted_for=f'Дополнительный для уровня {overall_level}'
                    ))
        
        return new_questions

    def generate_clarifying_questions(self, user_idea: str, existing_questions: List[str] = None) -> List[Question]:
        """Генерация базовых уточняющих вопросов"""
        if existing_questions is None:
            existing_questions = []
            
        # Формируем список уже заданных вопросов для промпта
        existing_questions_text = ""
        if existing_questions:
            existing_questions_text = f"""
УЖЕ ЗАДАННЫЕ ВОПРОСЫ (НЕ ПОВТОРЯТЬ):
{chr(10).join([f"- {q}" for q in existing_questions[-10:]])}

"""

        prompt = f"""
Пользователь описал свою идею: "{user_idea}"

{existing_questions_text}Сгенерируй ровно {GENERATION.questions_count} уточняющих вопросов в СТРОГО ЗАКРЫТОЙ ФОРМЕ (только да/нет ответы).

КРИТИЧЕСКИ ВАЖНО - КАЖДЫЙ ВОПРОС ДОЛЖЕН:
- Требовать ответа ТОЛЬКО "Да" или "Нет" 
- НЕ содержать слова: "или", "либо", "какой", "что", "как", "где", "когда", "почему", "сколько"
- НЕ предлагать выбор между вариантами
- Начинаться со слов: "Это", "Планируете", "Требуется", "Нужно", "Хотите", "Будет", "Есть", "Согласны"
- НЕ ПОВТОРЯТЬ и НЕ БЫТЬ ПОХОЖИМИ на уже заданные вопросы

ПРАВИЛЬНЫЕ примеры:
- Это долгосрочный проект?
- Планируете привлекать инвестиции?
- Требуется создание команды разработчиков?
- Нужна интеграция с существующими системами?

Формат ответа:
1. [вопрос]?
2. [вопрос]?
...
"""

        response = self.ai_client.make_request(
            prompt,
            SYSTEM_PROMPTS["questions"],
            GENERATION.max_tokens_questions,
            GENERATION.temperature_questions
        )
        
        questions_text = self.validator.extract_questions_from_text(response)
        validated_questions = []
        
        for question_text in questions_text:
            if self.validator.is_closed_form_question(question_text):
                validated_questions.append(Question(text=question_text))
            else:
                # Перегенерируем некорректный вопрос
                regenerated = self._regenerate_question(user_idea, question_text)
                validated_questions.append(Question(text=regenerated))
        
        # Фильтруем дубликаты
        unique_questions = self._filter_duplicate_questions(validated_questions, existing_questions)
        
        # Если уникальных вопросов недостаточно, генерируем дополнительные
        if len(unique_questions) < GENERATION.questions_count:
            needed_count = GENERATION.questions_count - len(unique_questions)
            logger.info(f"Недостаточно уникальных вопросов ({len(unique_questions)}/{GENERATION.questions_count}), генерируем {needed_count} дополнительных")
            
            # Создаем базовый профиль для генерации дополнительных вопросов
            from config import CompetencyLevel
            basic_profile = CompetencyProfile(
                domain="Общая",
                overall_level=CompetencyLevel.BASIC
            )
            
            additional_questions = self._regenerate_unique_questions(
                user_idea, basic_profile, [], 
                existing_questions + [q.text for q in unique_questions], 
                needed_count
            )
            unique_questions.extend(additional_questions)
        
        return unique_questions[:GENERATION.questions_count]

    def generate_adaptive_questions(self, user_idea: str, 
                                  competency_profile: CompetencyProfile,
                                  context_questions: List[str],
                                  existing_questions: List[str] = None) -> List[Question]:
        """Генерация адаптивных вопросов на основе профиля компетенций"""
        
        if existing_questions is None:
            existing_questions = []
        
        domain = competency_profile.domain
        overall_level = competency_profile.overall_level.value
        question_strategy = competency_profile.question_strategy
        strengths = competency_profile.strengths
        gaps = competency_profile.gaps
        
        complexity_level = question_strategy.get('complexity_level', 'средние')
        terminology_usage = question_strategy.get('terminology_usage', 'базовая')
        explanation_needed = question_strategy.get('explanation_needed', True)
        examples_needed = question_strategy.get('examples_needed', True)
        
        context_questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(context_questions)])
        strengths_text = ", ".join(strengths)
        gaps_text = ", ".join(gaps)
        
        # Формируем список уже заданных вопросов для промпта
        existing_questions_text = ""
        if existing_questions:
            existing_questions_text = f"""
УЖЕ ЗАДАННЫЕ ВОПРОСЫ (НЕ ПОВТОРЯТЬ):
{chr(10).join([f"- {q}" for q in existing_questions[-15:]])}

"""
        
        prompt = f"""
Пользователь написал: "{user_idea}"

{existing_questions_text}ПРОФИЛЬ КОМПЕТЕНЦИЙ ПОЛЬЗОВАТЕЛЯ:
- Область: {domain}
- Общий уровень: {overall_level}
- Сильные стороны: {strengths_text}
- Пробелы в знаниях: {gaps_text}

СТРАТЕГИЯ ВОПРОСОВ:
- Сложность: {complexity_level}
- Терминология: {terminology_usage}
- Нужны пояснения: {explanation_needed}
- Нужны примеры: {examples_needed}

КОНТЕКСТНЫЕ ВОПРОСЫ (для справки):
{context_questions_text}

Сгенерируй 6-7 адаптивных вопросов в СТРОГО ЗАКРЫТОЙ ФОРМЕ (да/нет), учитывая:

1. Уровень пользователя ({overall_level})
2. Его сильные стороны и пробелы
3. Стратегию взаимодействия
4. Контекст исходного запроса

ПРАВИЛА АДАПТАЦИИ:

ДЛЯ НОВИЧКОВ/БАЗОВОГО УРОВНЯ:
- Простые, понятные формулировки
- Избегать специализированной терминологии
- Фокус на базовых аспектах
- Обязательные пояснения и примеры

ДЛЯ СРЕДНЕГО УРОВНЯ:
- Умеренная сложность
- Базовая терминология с пояснениями
- Баланс между простотой и профессиональностью

ДЛЯ ПРОДВИНУТОГО/ЭКСПЕРТНОГО:
- Профессиональная терминология
- Сложные аспекты и детали
- Краткие формулировки

КАЖДЫЙ ВОПРОС ДОЛЖЕН:
- Требовать ответа ТОЛЬКО "Да" или "Нет"
- Начинаться со слов: "Это", "Планируете", "Требуется", "Нужно", "Хотите", "Будет", "Есть"

ФОРМАТ ОТВЕТА (JSON):
[
  {{
    "text": "Это будет направлено на широкую аудиторию?",
    "explanation": {"Пояснение что означает широкая vs узкая аудитория" if explanation_needed else ""},
    "examples": {["Примеры широкой и узкой аудитории"] if examples_needed else []},
    "adapted_for": "Адаптировано под уровень {overall_level}"
  }},
  ...
]
"""

        response = self.ai_client.make_request(
            prompt,
            SYSTEM_PROMPTS["questions"],
            GENERATION.max_tokens_questions,
            GENERATION.temperature_questions
        )
        
        try:
            data = self.ai_client.parse_json_response(response)
            if not data or not isinstance(data, list):
                raise ValueError("Ответ не является массивом JSON")
        except Exception as e:
            logger.warning(f"Ошибка парсинга ответа при генерации адаптивных вопросов: {e}")
            # Fallback: генерируем простые вопросы
            simple_questions = self.generate_clarifying_questions(user_idea)
            return [Question(
                text=q.text,
                explanation='Базовый вопрос' if explanation_needed else '',
                examples=['Пример ответа'] if examples_needed else [],
                adapted_for=f'Fallback для уровня {overall_level}'
            ) for q in simple_questions[:6]]
        
        validated_questions = []
        for item in data:
            if isinstance(item, dict) and 'text' in item:
                question_text = item['text']
                if self.validator.is_closed_form_question(question_text):
                    validated_questions.append(Question(
                        text=question_text,
                        explanation=item.get('explanation', ''),
                        examples=item.get('examples', []),
                        adapted_for=item.get('adapted_for', f'Уровень {overall_level}')
                    ))
                else:
                    # Перегенерируем некорректный вопрос
                    regenerated = self._regenerate_question(user_idea, question_text)
                    validated_questions.append(Question(
                        text=regenerated,
                        explanation=item.get('explanation', ''),
                        examples=item.get('examples', []),
                        adapted_for=f'Исправлен для уровня {overall_level}'
                    ))
        
        # Фильтруем дубликаты
        unique_questions = self._filter_duplicate_questions(validated_questions, existing_questions)
        
        # Если уникальных вопросов недостаточно, генерируем дополнительные
        target_count = 7
        if len(unique_questions) < target_count:
            needed_count = target_count - len(unique_questions)
            logger.info(f"Недостаточно уникальных адаптивных вопросов ({len(unique_questions)}/{target_count}), генерируем {needed_count} дополнительных")
            
            additional_questions = self._regenerate_unique_questions(
                user_idea, competency_profile, context_questions,
                existing_questions + [q.text for q in unique_questions], 
                needed_count
            )
            unique_questions.extend(additional_questions)
        
        return unique_questions[:7]

    def reformulate_unclear_questions(self, user_idea: str, unclear_questions: List[Dict], 
                                    competency_profile: CompetencyProfile) -> List[Dict[str, Any]]:
        """Переформулировка непонятных вопросов"""
        overall_level = competency_profile.overall_level.value
        is_beginner = overall_level in ['новичок', 'базовый']
        
        reformulated_results = []
        
        for item in unclear_questions:
            original_question = item['original_question']
            answer_type = item['answer']
            user_comment = item.get('comment', '')
            
            if answer_type == "Не знаю":
                prompt = f"""
Пользователь не понял вопрос: "{original_question}"
Его комментарий: "{user_comment}"
Идея пользователя: "{user_idea}"
Уровень пользователя: {"новичок" if is_beginner else "средний/продвинутый"}

Переформулируй вопрос более понятно для данного уровня пользователя.

ТРЕБОВАНИЯ:
- Сделай вопрос максимально простым и понятным
- Избегай специализированной терминологии если пользователь новичок
- Добавь контекст и пояснение
- Сохрани закрытую форму (да/нет)
- Учти комментарий пользователя

ФОРМАТ ОТВЕТА (JSON):
{{
  "reformulated_question": "Переформулированный вопрос?",
  "explanation": "Подробное объяснение что означает этот вопрос",
  "original_answer": "Не знаю"
}}
"""
                
            else:  # "Без разницы"
                prompt = f"""
Пользователь ответил "Без разницы" на вопрос: "{original_question}"
Его комментарий: "{user_comment}"
Идея пользователя: "{user_idea}"

Предложи 2-3 конкретных варианта с объяснением преимуществ каждого.

ФОРМАТ ОТВЕТА (JSON):
{{
  "reformulated_question": "Какой вариант предпочтительнее для вашего проекта?",
  "explanation": "Объяснение важности этого выбора",
  "options": [
    {{
      "title": "Вариант 1",
      "description": "Описание и преимущества варианта 1"
    }},
    {{
      "title": "Вариант 2", 
      "description": "Описание и преимущества варианта 2"
    }}
  ],
  "original_answer": "Без разницы"
}}
"""
            
            response = self.ai_client.make_request(
                prompt,
                SYSTEM_PROMPTS["questions"],
                GENERATION.max_tokens_questions,
                GENERATION.temperature_refined
            )
            
            try:
                data = self.ai_client.parse_json_response(response)
                if data and isinstance(data, dict):
                    data['original_question'] = original_question
                    reformulated_results.append(data)
                else:
                    raise ValueError("Ответ не является объектом JSON")
            except Exception as e:
                logger.warning(f"Ошибка парсинга ответа при переформулировке: {e}")
                # Fallback
                # Fallback
                fallback_result = {
                    'original_question': original_question,
                    'reformulated_question': f"Уточните: {original_question}",
                    'explanation': "Пожалуйста, ответьте на этот вопрос более конкретно",
                    'original_answer': answer_type
                }
                if answer_type == "Без разницы":
                    fallback_result['options'] = [
                        {'title': 'Да', 'description': 'Включить эту функцию'},
                        {'title': 'Нет', 'description': 'Не включать эту функцию'}
                    ]
                reformulated_results.append(fallback_result)
        
        return reformulated_results

    def _regenerate_question(self, user_idea: str, invalid_question: str) -> str:
        """Перегенерация некорректного вопроса"""
        prompt = f"""
Идея пользователя: "{user_idea}"
Некорректный вопрос: "{invalid_question}"

Этот вопрос НЕ является закрытым (да/нет). Перефразируй его в СТРОГО закрытую форму.

ТРЕБОВАНИЯ к новому вопросу:
- Ответ только "Да" или "Нет"
- НЕ использовать слова: "или", "либо", "какой", "что", "как", "где", "когда", "почему", "сколько"
- Начинать со слов: "Это", "Планируете", "Требуется", "Нужно", "Хотите", "Будет", "Есть", "Согласны"

Примеры правильной перефразировки:
- "Какую платформу выберете?" → "Планируете разрабатывать для мобильных устройств?"
- "Мобильное или веб-приложение?" → "Это будет мобильное приложение?"
- "Сколько времени займет разработка?" → "Планируете завершить разработку в течение года?"

Ответь только переформулированным вопросом, без объяснений.
"""
        
        response = self.ai_client.make_request(
            prompt,
            SYSTEM_PROMPTS["questions"],
            GENERATION.max_tokens_questions,
            GENERATION.temperature_refined
        )
        
        regenerated = response.strip().rstrip('?') + '?'
        
        # Проверяем, что перегенерированный вопрос валиден
        if self.validator.is_closed_form_question(regenerated):
            return regenerated
        else:
            # Если все еще невалиден, возвращаем простой fallback
            return f"Это важно для вашего проекта?" 