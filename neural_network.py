from typing import Dict, List, Any, Optional
from ai_client import AIClient
from competency_analyzer import CompetencyAnalyzer
from question_generator import QuestionGenerator
from question_validator import QuestionValidator
from idea_processor import IdeaProcessor
from models import (
    Question, CompetencyProfile, DomainAnalysis, 
    RequiredCompetencies, SessionData
)
from config import GENERATION


class NeuralNetwork:
    """
    Главный класс для работы с нейросетью
    Координирует работу всех модулей
    """
    
    def __init__(self, base_url: str = None):
        # Инициализация компонентов
        self.ai_client = AIClient(base_url)
        self.competency_analyzer = CompetencyAnalyzer(self.ai_client)
        self.question_generator = QuestionGenerator(self.ai_client)
        self.question_validator = QuestionValidator()
        self.idea_processor = IdeaProcessor(self.ai_client)
        
        print("🤖 Нейросеть инициализирована с модульной архитектурой")

    # === ОСНОВНЫЕ МЕТОДЫ ДЛЯ СОВМЕСТИМОСТИ ===
    
    def analyze_user_request_and_generate_competency_assessment(self, user_idea: str) -> Dict[str, Any]:
        """
        Многоэтапный анализ запроса пользователя для определения компетенций
        
        Этапы:
        1. Анализ запроса и генерация контекстно-специфичных вопросов
        2. Определение необходимых компетенций для ответа на эти вопросы
        3. Формирование вопросов для оценки компетенций пользователя
        """
        
        # Этап 1: Генерация контекстно-специфичных вопросов
        context_questions = self.competency_analyzer.generate_context_questions(user_idea)
        
        # Этап 2: Анализ необходимых компетенций
        required_competencies = self.competency_analyzer.analyze_required_competencies(
            user_idea, context_questions
        )
        
        if not required_competencies:
            # Fallback если анализ не удался
            required_competencies = RequiredCompetencies(
                domain="Общая",
                competencies=["Базовые знания"],
                knowledge=["Общие представления"],
                skills=["Базовые навыки"],
                experience=["Минимальный опыт"]
            )
        
        # Этап 3: Генерация вопросов для оценки компетенций
        competency_assessment_questions = self.competency_analyzer.generate_competency_assessment_questions(
            user_idea, required_competencies
        )
        
        return {
            'stage': 'competency_assessment',
            'user_request': user_idea,
            'context_questions': context_questions,
            'required_competencies': required_competencies,
            'competency_questions': competency_assessment_questions,
            'message': f'Пользователь написал: "{user_idea}"\n\nЧтобы дать вам квалифицированную помощь, мне нужно понять ваш уровень компетенций. Ответьте на несколько вопросов:'
        }

    def build_competency_profile_and_generate_questions(self, user_idea: str, 
                                                      competency_answers: Dict[str, str],
                                                      required_competencies: RequiredCompetencies,
                                                      context_questions: List[str],
                                                      existing_questions: List[str] = None) -> Dict[str, Any]:
        """
        Построение профиля компетенций пользователя и генерация адаптивных вопросов
        """
        
        # Строим детальный профиль компетенций
        competency_profile = self.competency_analyzer.build_competency_profile(
            competency_answers, required_competencies
        )
        
        # Генерируем адаптивные вопросы на основе профиля
        # Объединяем переданные уже заданные вопросы с вопросами о компетенциях
        all_existing_questions = existing_questions.copy() if existing_questions else []
        if competency_answers:
            all_existing_questions.extend(list(competency_answers.keys()))
        
        adaptive_questions = self.question_generator.generate_adaptive_questions(
            user_idea, competency_profile, context_questions, all_existing_questions
        )
        
        return {
            'stage': 'main_briefing',
            'user_request': user_idea,
            'competency_profile': competency_profile,
            'required_competencies': required_competencies,
            'questions': adaptive_questions,
            'message': f"Отлично! На основе ваших ответов я понял ваш уровень компетенций в области '{competency_profile.domain}'. Теперь перейдем к детальному обсуждению вашей идеи:"
        }

    def generate_refined_idea(self, user_idea: str, answers: Dict[str, str], 
                            comments: Dict[str, str] = None) -> str:
        """Генерация уточненной идеи на основе ответов и комментариев"""
        return self.idea_processor.generate_refined_idea(user_idea, answers, comments)

    def process_feedback_and_regenerate(self, user_idea: str, current_refined_idea: str, 
                                      feedback_type: str, comments: str = "") -> str:
        """Обработка обратной связи и перегенерация идеи"""
        return self.idea_processor.process_feedback_and_regenerate(
            user_idea, current_refined_idea, feedback_type, comments
        )

    def generate_final_result(self, user_idea: str, refined_idea: str, 
                            all_iterations: List[Dict], iteration_count: int) -> str:
        """Генерация финального результата брифинга"""
        return self.idea_processor.generate_final_result(
            user_idea, refined_idea, all_iterations, iteration_count
        )

    def reformulate_unclear_questions(self, user_idea: str, unclear_questions: List[Dict], 
                                    user_profile: Dict[str, str]) -> List[Dict[str, Any]]:
        """Переформулировка непонятных вопросов"""
        
        # Преобразуем старый формат профиля в новый для совместимости
        from config import CompetencyLevel
        
        try:
            overall_level = CompetencyLevel(user_profile.get('domain_expertise', 'базовый'))
        except ValueError:
            overall_level = CompetencyLevel.BASIC
        
        competency_profile = CompetencyProfile(
            domain=user_profile.get('domain', 'Общая'),
            overall_level=overall_level,
            question_strategy=user_profile
        )
        
        return self.question_generator.reformulate_unclear_questions(
            user_idea, unclear_questions, competency_profile
        )

    # === МЕТОДЫ ДЛЯ ОБРАТНОЙ СОВМЕСТИМОСТИ ===
    
    def generate_clarifying_questions(self, user_idea: str) -> List[str]:
        """Генерация базовых уточняющих вопросов (для обратной совместимости)"""
        questions = self.question_generator.generate_clarifying_questions(user_idea, [])
        return [q.text for q in questions]

    def generate_adaptive_questions(self, user_idea: str, user_profile: Dict[str, str], 
                                  domain_analysis: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Генерация адаптивных вопросов (для обратной совместимости)"""
        
        # Преобразуем старый формат в новый
        from config import CompetencyLevel
        
        try:
            overall_level = CompetencyLevel(user_profile.get('domain_expertise', 'базовый'))
        except ValueError:
            overall_level = CompetencyLevel.BASIC
        
        competency_profile = CompetencyProfile(
            domain=user_profile.get('domain', 'Общая'),
            overall_level=overall_level,
            question_strategy=user_profile
        )
        
        context_questions = []  # Пустой список для совместимости
        existing_questions = []  # Пустой список для совместимости
        
        questions = self.question_generator.generate_adaptive_questions(
            user_idea, competency_profile, context_questions, existing_questions
        )
        
        # Преобразуем в старый формат
        return [
            {
                'question': q.text,
                'explanation': q.explanation,
                'examples': q.examples,
                'adapted_for': q.adapted_for
            }
            for q in questions
        ]

    # === УСТАРЕВШИЕ МЕТОДЫ (для совместимости) ===
    
    def determine_user_competency_profile(self, user_idea: str) -> Dict[str, Any]:
        """УСТАРЕВШИЙ МЕТОД - используйте analyze_user_request_and_generate_competency_assessment"""
        
        domain_analysis = self.competency_analyzer.analyze_idea_domain(user_idea)
        competency_questions = self.competency_analyzer.generate_competency_assessment_questions(
            user_idea, RequiredCompetencies(domain=domain_analysis.primary_domain)
        )
        
        return {
            'domain_analysis': domain_analysis,
            'competency_questions': competency_questions,
            'status': 'awaiting_competency_assessment'
        }

    def build_user_profile_from_competency(self, competency_answers: Dict[str, str], 
                                         domain_analysis: Dict[str, Any]) -> Dict[str, str]:
        """УСТАРЕВШИЙ МЕТОД - используйте build_competency_profile"""
        
        required_competencies = RequiredCompetencies(
            domain=domain_analysis.get('primary_domain', 'Общая')
        )
        
        profile = self.competency_analyzer.build_competency_profile(
            competency_answers, required_competencies
        )
        
        # Преобразуем в старый формат
        return {
            'domain_expertise': profile.overall_level.value,
            'theoretical_knowledge': profile.theoretical_knowledge,
            'practical_experience': profile.practical_experience,
            'terminology_familiarity': profile.technical_skills,
            'question_complexity': profile.question_strategy.get('complexity_level', 'средние'),
            'explanation_needed': profile.question_strategy.get('explanation_needed', True),
            'examples_needed': profile.question_strategy.get('examples_needed', True),
            'profile_summary': profile.profile_summary
        }

    def generate_questions_with_competency_analysis(self, user_idea: str) -> Dict[str, Any]:
        """УСТАРЕВШИЙ МЕТОД - используйте analyze_user_request_and_generate_competency_assessment"""
        return self.analyze_user_request_and_generate_competency_assessment(user_idea)

    def process_competency_answers_and_generate_questions(self, user_idea: str, 
                                                        competency_answers: Dict[str, str],
                                                        domain_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """УСТАРЕВШИЙ МЕТОД - используйте build_competency_profile_and_generate_questions"""
        
        required_competencies = RequiredCompetencies(
            domain=domain_analysis.get('primary_domain', 'Общая')
        )
        
        return self.build_competency_profile_and_generate_questions(
            user_idea, competency_answers, required_competencies, []
        )

    # === ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ ===
    
    def check_connection(self) -> bool:
        """Проверка подключения к LM Studio"""
        return self.ai_client.check_connection()

    def analyze_idea_complexity(self, user_idea: str) -> Dict[str, Any]:
        """Анализ сложности идеи"""
        return self.idea_processor.analyze_idea_complexity(user_idea)

    def suggest_improvements(self, refined_idea: str) -> List[str]:
        """Предложение улучшений для идеи"""
        return self.idea_processor.suggest_improvements(refined_idea)

    def validate_question(self, question: str) -> bool:
        """Валидация вопроса на закрытую форму"""
        return self.question_validator.is_closed_form_question(question)

    def get_validation_errors(self, question: str) -> List[str]:
        """Получение ошибок валидации для вопроса"""
        return self.question_validator.get_validation_errors(question)

    # === ВНУТРЕННИЕ МЕТОДЫ (для совместимости) ===
    
    def _make_request(self, prompt: str, max_tokens: int = 8192, temperature: float = 0.7) -> str:
        """Внутренний метод для запросов (для совместимости)"""
        return self.ai_client.make_request(prompt, None, max_tokens, temperature)

    def _extract_questions(self, response: str) -> List[str]:
        """Извлечение вопросов из ответа (для совместимости)"""
        return self.question_validator.extract_questions_from_text(response)

    def _is_closed_form_question(self, question: str) -> bool:
        """Проверка закрытой формы (для совместимости)"""
        return self.question_validator.is_closed_form_question(question)

    def _regenerate_question(self, user_idea: str, invalid_question: str) -> str:
        """Перегенерация вопроса (для совместимости)"""
        return self.question_generator._regenerate_question(user_idea, invalid_question)