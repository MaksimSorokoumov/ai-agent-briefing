from typing import Dict, List, Any
from ai_client import AIClient
from config import SYSTEM_PROMPTS, GENERATION


class IdeaProcessor:
    """Процессор для обработки и уточнения идей"""
    
    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client

    def generate_refined_idea(self, user_idea: str, answers: Dict[str, str], 
                            comments: Dict[str, str] = None) -> str:
        """Генерация уточненной идеи на основе ответов"""
        answers_text = "\n".join([f"- {q}: {a}" for q, a in answers.items()])
        
        comments_text = ""
        if comments:
            comments_text = "\n\nДополнительные комментарии пользователя:\n" + \
                          "\n".join([f"- К вопросу '{q}': {c}" for q, c in comments.items()])
        
        prompt = f"""
Исходная идея пользователя: "{user_idea}"

Ответы на уточняющие вопросы:
{answers_text}{comments_text}

На основе исходной идеи, ответов и комментариев сформулируй УТОЧНЕННУЮ и ДЕТАЛИЗИРОВАННУЮ версию идеи.

Требования:
- Сохрани суть исходной идеи
- Учти все ответы пользователя
- Обязательно учти комментарии пользователя - они содержат важные уточнения
- Добавь конкретики и деталей
- Структурируй ответ логично
- Объем: 3-5 предложений

Начни ответ с фразы "Уточненная идея:"
"""

        return self.ai_client.make_request(
            prompt,
            SYSTEM_PROMPTS["refinement"],
            GENERATION.max_tokens_refined,
            GENERATION.temperature_refined
        )

    def process_feedback_and_regenerate(self, user_idea: str, current_refined_idea: str, 
                                      feedback_type: str, comments: str = "") -> str:
        """Обработка обратной связи и перегенерация идеи"""
        if feedback_type == "correct":
            return current_refined_idea
        
        elif feedback_type == "mostly_correct":
            prompt = f"""
Исходная идея: "{user_idea}"
Текущая уточненная идея: "{current_refined_idea}"
Дополнительные комментарии пользователя: "{comments}"

Пользователь считает идею в целом верной, но хочет добавить детали.
Доработай уточненную идею, включив комментарии пользователя.

Начни ответ с фразы "Доработанная идея:"
"""
        
        elif feedback_type == "mostly_incorrect":
            prompt = f"""
Исходная идея: "{user_idea}"
Неудачная попытка уточнения: "{current_refined_idea}"
Комментарии пользователя о том, что неверно: "{comments}"

Пользователь считает уточнение по большей части неверным.
Создай НОВУЮ уточненную идею, учитывая исходную идею и комментарии пользователя.

Начни ответ с фразы "Переработанная идея:"
"""
        else:
            return current_refined_idea
        
        return self.ai_client.make_request(
            prompt,
            SYSTEM_PROMPTS["refinement"],
            GENERATION.max_tokens_refined,
            GENERATION.temperature_refined
        )

    def generate_final_result(self, user_idea: str, refined_idea: str, 
                            all_iterations: List[Dict], iteration_count: int) -> str:
        """Генерация финального результата брифинга"""
        prompt = f"""
БРИФИНГ ЗАВЕРШЕН

Исходная идея пользователя: "{user_idea}"
Финальная уточненная идея: "{refined_idea}"
Количество итераций уточнения: {iteration_count}

Создай ИТОГОВЫЙ ОТЧЕТ по брифингу, который включает:

1. **Исходная идея**: краткое изложение того, с чего начинал пользователь
2. **Ключевые уточнения**: что удалось выяснить в процессе брифинга
3. **Финальная формулировка**: четкая и детальная версия идеи
4. **Рекомендации**: 2-3 конкретных шага для реализации

Структурируй ответ с заголовками и сделай его информативным и полезным.
"""

        return self.ai_client.make_request(
            prompt,
            SYSTEM_PROMPTS["final"],
            GENERATION.max_tokens_final,
            GENERATION.temperature_final
        )

    def analyze_idea_complexity(self, user_idea: str) -> Dict[str, Any]:
        """Анализ сложности идеи"""
        prompt = f"""
Проанализируй сложность идеи: "{user_idea}"

Оцени по следующим критериям:
- Техническая сложность (1-5)
- Требуемые ресурсы (1-5)
- Время реализации (1-5)
- Необходимые знания (1-5)

ФОРМАТ ОТВЕТА (JSON):
{{
  "technical_complexity": 3,
  "required_resources": 2,
  "implementation_time": 4,
  "required_knowledge": 3,
  "overall_complexity": "средняя",
  "complexity_description": "Краткое описание сложности",
  "main_challenges": ["Вызов 1", "Вызов 2"],
  "recommended_approach": "Рекомендуемый подход к реализации"
}}
"""

        response = self.ai_client.make_request(
            prompt,
            SYSTEM_PROMPTS["main"],
            GENERATION.max_tokens_questions,
            GENERATION.temperature_refined
        )
        
        data = self.ai_client.parse_json_response(response)
        return data if data else {
            "technical_complexity": 3,
            "required_resources": 3,
            "implementation_time": 3,
            "required_knowledge": 3,
            "overall_complexity": "средняя",
            "complexity_description": "Требуется дополнительный анализ",
            "main_challenges": ["Определить требования", "Выбрать технологии"],
            "recommended_approach": "Поэтапная реализация"
        }

    def suggest_improvements(self, refined_idea: str) -> List[str]:
        """Предложение улучшений для идеи"""
        prompt = f"""
Уточненная идея: "{refined_idea}"

Предложи 3-5 конкретных улучшений или дополнений к этой идее.

Требования:
- Улучшения должны быть практичными и реализуемыми
- Каждое улучшение должно добавлять ценность
- Формулируй кратко и понятно

Формат ответа - просто список:
1. [улучшение]
2. [улучшение]
...
"""

        response = self.ai_client.make_request(
            prompt,
            SYSTEM_PROMPTS["refinement"],
            GENERATION.max_tokens_questions,
            GENERATION.temperature_refined
        )
        
        # Извлекаем список улучшений
        improvements = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith(('1.', '2.', '3.', '4.', '5.')) or line.startswith('-')):
                # Убираем номер и очищаем
                improvement = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                if improvement:
                    improvements.append(improvement)
        
        return improvements[:5]  # Максимум 5 улучшений 