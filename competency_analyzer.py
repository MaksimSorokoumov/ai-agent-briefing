from typing import Dict, List, Any, Optional
from ai_client import AIClient
from models import DomainAnalysis, RequiredCompetencies, CompetencyProfile, Question
from config import SYSTEM_PROMPTS, GENERATION, KNOWLEDGE_DOMAINS, CompetencyLevel


class CompetencyAnalyzer:
    """Анализатор компетенций пользователя"""
    
    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client

    def analyze_idea_domain(self, user_idea: str) -> Optional[DomainAnalysis]:
        """Анализ области знаний идеи"""
        domains_text = ", ".join(KNOWLEDGE_DOMAINS)
        
        prompt = f"""
Проанализируй идею пользователя: "{user_idea}"

Определи основную область знаний и смежные области из списка:
{domains_text}

ФОРМАТ ОТВЕТА (JSON):
{{
  "primary_domain": "Основная область",
  "secondary_domains": ["Смежная область 1", "Смежная область 2"],
  "complexity_level": "простая/средняя/сложная",
  "requires_technical_knowledge": true/false,
  "requires_specialized_knowledge": true/false,
  "domain_description": "Краткое описание необходимых знаний"
}}
"""

        response = self.ai_client.make_request(
            prompt, 
            SYSTEM_PROMPTS["competency"],
            GENERATION.max_tokens_questions,
            GENERATION.temperature_questions
        )
        
        data = self.ai_client.parse_json_response(response)
        if not data:
            return DomainAnalysis(primary_domain="Общая")
        
        return DomainAnalysis(
            primary_domain=data.get('primary_domain', 'Общая'),
            secondary_domains=data.get('secondary_domains', []),
            complexity_level=data.get('complexity_level', 'средняя'),
            requires_technical_knowledge=data.get('requires_technical_knowledge', False),
            requires_specialized_knowledge=data.get('requires_specialized_knowledge', False),
            domain_description=data.get('domain_description', '')
        )

    def generate_context_questions(self, user_idea: str) -> List[str]:
        """Генерация контекстно-специфичных вопросов"""
        prompt = f"""
Пользователь написал: "{user_idea}"

Сгенерируй 8-10 уточняющих вопросов, которые помогут лучше понять суть запроса.

ТРЕБОВАНИЯ:
- Вопросы должны быть специфичными для данной области/темы
- Каждый вопрос должен помочь уточнить важные детали
- Вопросы должны быть практичными и релевантными
- Формулируй как обычные вопросы (не обязательно да/нет)

Формат ответа - просто список вопросов:
1. [вопрос]
2. [вопрос]
...
"""

        response = self.ai_client.make_request(
            prompt,
            SYSTEM_PROMPTS["questions"],
            GENERATION.max_tokens_questions,
            GENERATION.temperature_questions
        )
        
        from question_validator import QuestionValidator
        validator = QuestionValidator()
        return validator.extract_questions_from_text(response)

    def analyze_required_competencies(self, user_idea: str, context_questions: List[str]) -> Optional[RequiredCompetencies]:
        """Анализ необходимых компетенций"""
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(context_questions)])
        
        prompt = f"""
Пользователь написал: "{user_idea}"

Для ответа на эти уточняющие вопросы:
{questions_text}

Определи необходимые компетенции, знания, умения и опыт.

ФОРМАТ ОТВЕТА (JSON):
{{
  "domain": "Основная область знаний",
  "competencies": ["Компетенция 1", "Компетенция 2", "Компетенция 3"],
  "knowledge": ["Знание 1", "Знание 2", "Знание 3"],
  "skills": ["Умение 1", "Умение 2", "Умение 3"],
  "experience": ["Опыт 1", "Опыт 2"]
}}
"""

        response = self.ai_client.make_request(
            prompt,
            SYSTEM_PROMPTS["competency"],
            GENERATION.max_tokens_questions,
            GENERATION.temperature_questions
        )
        
        data = self.ai_client.parse_json_response(response)
        if not data:
            return None
        
        return RequiredCompetencies(
            domain=data.get('domain', 'Общая'),
            competencies=data.get('competencies', []),
            knowledge=data.get('knowledge', []),
            skills=data.get('skills', []),
            experience=data.get('experience', [])
        )

    def generate_competency_assessment_questions(self, user_idea: str, 
                                               required_competencies: RequiredCompetencies) -> List[Question]:
        """Генерация вопросов для оценки компетенций"""
        domain = required_competencies.domain
        competencies_text = ", ".join(required_competencies.competencies)
        knowledge_text = ", ".join(required_competencies.knowledge)
        skills_text = ", ".join(required_competencies.skills)
        experience_text = ", ".join(required_competencies.experience)
        
        prompt = f"""
Пользователь написал: "{user_idea}"

Для качественной помощи нужны компетенции:
КОМПЕТЕНЦИИ: {competencies_text}
ЗНАНИЯ: {knowledge_text}
УМЕНИЯ: {skills_text}
ОПЫТ: {experience_text}

Сгенерируй {GENERATION.competency_questions_count} вопросов закрытого типа (да/нет) для оценки уровня пользователя в области "{domain}".

ПРИНЦИПЫ:
- Вопросы должны быть в закрытой форме (Да/Нет)
- Начинать с базовых, постепенно усложняя
- Покрывать разные аспекты: образование, опыт, практические навыки, знания
- Быть специфичными для области "{domain}"

ФОРМАТ ОТВЕТА (JSON):
[
  {{
    "text": "Есть ли у вас образование в области {domain}?",
    "category": "education",
    "weight": "high",
    "explanation": "Определить базовый уровень образования"
  }},
  ...
]
"""

        response = self.ai_client.make_request(
            prompt,
            SYSTEM_PROMPTS["competency"],
            GENERATION.max_tokens_questions,
            GENERATION.temperature_questions
        )
        
        data = self.ai_client.parse_json_response(response)
        if not data or not isinstance(data, list):
            return self._generate_fallback_competency_questions(domain)
        
        questions = []
        for item in data:
            if isinstance(item, dict) and 'text' in item:
                questions.append(Question(
                    text=item['text'],
                    category=item.get('category', ''),
                    weight=item.get('weight', 'medium'),
                    explanation=item.get('explanation', '')
                ))
        
        return questions[:GENERATION.competency_questions_count]

    def build_competency_profile(self, competency_answers: Dict[str, str], 
                                required_competencies: RequiredCompetencies) -> CompetencyProfile:
        """Построение профиля компетенций на основе ответов"""
        domain = required_competencies.domain
        answers_text = "\n".join([f"- {q}: {a}" for q, a in competency_answers.items()])
        
        competencies_text = "\n".join([f"- {c}" for c in required_competencies.competencies])
        knowledge_text = "\n".join([f"- {k}" for k in required_competencies.knowledge])
        skills_text = "\n".join([f"- {s}" for s in required_competencies.skills])
        experience_text = "\n".join([f"- {e}" for e in required_competencies.experience])
        
        prompt = f"""
Область: {domain}

НЕОБХОДИМЫЕ КОМПЕТЕНЦИИ:
{competencies_text}

ЗНАНИЯ:
{knowledge_text}

УМЕНИЯ:
{skills_text}

ОПЫТ:
{experience_text}

ОТВЕТЫ ПОЛЬЗОВАТЕЛЯ:
{answers_text}

Проанализируй ответы и создай профиль компетенций.

ФОРМАТ ОТВЕТА (JSON):
{{
  "domain": "{domain}",
  "overall_level": "новичок/базовый/средний/продвинутый/эксперт",
  "competency_analysis": {{
    "education_level": "нет/базовое/среднее/высшее/специализированное",
    "practical_experience": "нет/минимальный/средний/большой/экспертный",
    "theoretical_knowledge": "слабое/базовое/хорошее/отличное/экспертное",
    "technical_skills": "нет/базовые/средние/продвинутые/экспертные"
  }},
  "strengths": ["Что пользователь знает/умеет хорошо"],
  "gaps": ["Чего пользователь не знает/не умеет"],
  "question_strategy": {{
    "complexity_level": "простые/средние/сложные",
    "terminology_usage": "избегать/базовая/профессиональная",
    "explanation_needed": true/false,
    "examples_needed": true/false
  }},
  "profile_summary": "Краткое описание уровня пользователя"
}}
"""

        response = self.ai_client.make_request(
            prompt,
            SYSTEM_PROMPTS["competency"],
            GENERATION.max_tokens_questions,
            GENERATION.temperature_refined
        )
        
        data = self.ai_client.parse_json_response(response)
        if not data:
            return self._generate_fallback_profile(domain)
        
        # Определяем уровень компетенций
        overall_level_str = data.get('overall_level', 'базовый')
        try:
            overall_level = CompetencyLevel(overall_level_str)
        except ValueError:
            overall_level = CompetencyLevel.BASIC
        
        return CompetencyProfile(
            domain=domain,
            overall_level=overall_level,
            education_level=data.get('competency_analysis', {}).get('education_level', ''),
            practical_experience=data.get('competency_analysis', {}).get('practical_experience', ''),
            theoretical_knowledge=data.get('competency_analysis', {}).get('theoretical_knowledge', ''),
            technical_skills=data.get('competency_analysis', {}).get('technical_skills', ''),
            strengths=data.get('strengths', []),
            gaps=data.get('gaps', []),
            question_strategy=data.get('question_strategy', {}),
            profile_summary=data.get('profile_summary', '')
        )

    def _generate_fallback_competency_questions(self, domain: str) -> List[Question]:
        """Fallback вопросы о компетенциях"""
        return [
            Question(
                text=f"Есть ли у вас образование в области {domain}?",
                category="education",
                weight="high",
                explanation="Определить базовый уровень образования"
            ),
            Question(
                text=f"Имеете ли вы практический опыт в {domain}?",
                category="experience",
                weight="high",
                explanation="Выяснить практические навыки"
            ),
            Question(
                text=f"Знакомы ли вы с профессиональной терминологией в {domain}?",
                category="knowledge",
                weight="medium",
                explanation="Оценить глубину знаний"
            )
        ]

    def _generate_fallback_profile(self, domain: str) -> CompetencyProfile:
        """Fallback профиль компетенций"""
        return CompetencyProfile(
            domain=domain,
            overall_level=CompetencyLevel.BASIC,
            education_level='базовое',
            practical_experience='минимальный',
            theoretical_knowledge='базовое',
            technical_skills='базовые',
            strengths=['Базовые знания'],
            gaps=['Требуется дополнительное изучение'],
            question_strategy={
                'complexity_level': 'средние',
                'terminology_usage': 'базовая',
                'explanation_needed': True,
                'examples_needed': True
            },
            profile_summary='Пользователь с базовыми знаниями, требуются пояснения и примеры'
        ) 