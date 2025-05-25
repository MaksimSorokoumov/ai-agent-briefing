from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from config import CompetencyLevel, QuestionComplexity, SessionStep

@dataclass
class Question:
    """Модель вопроса"""
    text: str
    explanation: str = ""
    examples: List[str] = field(default_factory=list)
    category: str = ""
    weight: str = "medium"
    adapted_for: str = ""

@dataclass
class Answer:
    """Модель ответа"""
    question: str
    answer: str
    comment: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class CompetencyProfile:
    """Профиль компетенций пользователя"""
    domain: str
    overall_level: CompetencyLevel
    education_level: str = ""
    practical_experience: str = ""
    theoretical_knowledge: str = ""
    technical_skills: str = ""
    strengths: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    question_strategy: Dict[str, Any] = field(default_factory=dict)
    profile_summary: str = ""

@dataclass
class DomainAnalysis:
    """Анализ области знаний"""
    primary_domain: str
    secondary_domains: List[str] = field(default_factory=list)
    complexity_level: str = "средняя"
    requires_technical_knowledge: bool = False
    requires_specialized_knowledge: bool = False
    domain_description: str = ""

@dataclass
class RequiredCompetencies:
    """Необходимые компетенции для области"""
    domain: str
    competencies: List[str] = field(default_factory=list)
    knowledge: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    experience: List[str] = field(default_factory=list)

@dataclass
class SessionIteration:
    """Итерация сессии"""
    iteration: int
    timestamp: datetime
    refined_idea: str
    feedback_type: str = ""
    comments: str = ""
    questions: List[Question] = field(default_factory=list)
    answers: List[Answer] = field(default_factory=list)

@dataclass
class SessionData:
    """Данные сессии"""
    session_id: str
    created_at: datetime
    updated_at: datetime = field(default_factory=datetime.now)
    status: str = "active"
    current_step: SessionStep = SessionStep.INPUT_IDEA
    iteration_count: int = 0
    competency_stage: str = ""
    
    # Основные данные
    user_idea: str = ""
    original_user_idea: str = ""
    refined_idea: str = ""
    final_result: str = ""
    
    # Компетенции
    competency_profile: Optional[CompetencyProfile] = None
    domain_analysis: Optional[DomainAnalysis] = None
    required_competencies: Optional[RequiredCompetencies] = None
    
    # Вопросы и ответы
    context_questions: List[str] = field(default_factory=list)
    competency_questions: List[Question] = field(default_factory=list)
    clarifying_questions: List[Question] = field(default_factory=list)
    competency_answers: Dict[str, str] = field(default_factory=dict)
    competency_comments: Dict[str, str] = field(default_factory=dict)
    main_answers: Dict[str, str] = field(default_factory=dict)
    main_comments: Dict[str, str] = field(default_factory=dict)
    answers: Dict[str, str] = field(default_factory=dict)
    comments: Dict[str, str] = field(default_factory=dict)
    
    # История всех заданных вопросов для предотвращения дубликатов
    all_asked_questions: List[str] = field(default_factory=list)
    
    # История
    all_iterations: List[SessionIteration] = field(default_factory=list)
    validation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для сохранения"""
        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'status': self.status,
            'current_step': self.current_step.value,
            'iteration_count': self.iteration_count,
            'competency_stage': self.competency_stage,
            'user_idea': self.user_idea,
            'original_user_idea': self.original_user_idea,
            'refined_idea': self.refined_idea,
            'final_result': self.final_result,
            'competency_profile': self._serialize_competency_profile(),
            'domain_analysis': self._serialize_domain_analysis(),
            'required_competencies': self._serialize_required_competencies(),
            'context_questions': self.context_questions,
            'competency_questions': [self._serialize_question(q) for q in self.competency_questions],
            'clarifying_questions': [self._serialize_question(q) for q in self.clarifying_questions],
            'competency_answers': self.competency_answers,
            'competency_comments': self.competency_comments,
            'main_answers': self.main_answers,
            'main_comments': self.main_comments,
            'answers': self.answers,
            'comments': self.comments,
            'all_asked_questions': self.all_asked_questions,
            'all_iterations': [self._serialize_iteration(it) for it in self.all_iterations],
            'validation_history': self.validation_history
        }
    
    def _serialize_competency_profile(self) -> Optional[Dict[str, Any]]:
        if not self.competency_profile:
            return None
        return {
            'domain': self.competency_profile.domain,
            'overall_level': self.competency_profile.overall_level.value,
            'education_level': self.competency_profile.education_level,
            'practical_experience': self.competency_profile.practical_experience,
            'theoretical_knowledge': self.competency_profile.theoretical_knowledge,
            'technical_skills': self.competency_profile.technical_skills,
            'strengths': self.competency_profile.strengths,
            'gaps': self.competency_profile.gaps,
            'question_strategy': self.competency_profile.question_strategy,
            'profile_summary': self.competency_profile.profile_summary
        }
    
    def _serialize_domain_analysis(self) -> Optional[Dict[str, Any]]:
        if not self.domain_analysis:
            return None
        return {
            'primary_domain': self.domain_analysis.primary_domain,
            'secondary_domains': self.domain_analysis.secondary_domains,
            'complexity_level': self.domain_analysis.complexity_level,
            'requires_technical_knowledge': self.domain_analysis.requires_technical_knowledge,
            'requires_specialized_knowledge': self.domain_analysis.requires_specialized_knowledge,
            'domain_description': self.domain_analysis.domain_description
        }
    
    def _serialize_required_competencies(self) -> Optional[Dict[str, Any]]:
        if not self.required_competencies:
            return None
        return {
            'domain': self.required_competencies.domain,
            'competencies': self.required_competencies.competencies,
            'knowledge': self.required_competencies.knowledge,
            'skills': self.required_competencies.skills,
            'experience': self.required_competencies.experience
        }
    
    def _serialize_question(self, question: Question) -> Dict[str, Any]:
        return {
            'text': question.text,
            'explanation': question.explanation,
            'examples': question.examples,
            'category': question.category,
            'weight': question.weight,
            'adapted_for': question.adapted_for
        }
    
    def _serialize_iteration(self, iteration: SessionIteration) -> Dict[str, Any]:
        return {
            'iteration': iteration.iteration,
            'timestamp': iteration.timestamp.isoformat(),
            'refined_idea': iteration.refined_idea,
            'feedback_type': iteration.feedback_type,
            'comments': iteration.comments,
            'questions': [self._serialize_question(q) for q in iteration.questions],
            'answers': [self._serialize_answer(a) for a in iteration.answers]
        }
    
    def _serialize_answer(self, answer: Answer) -> Dict[str, Any]:
        return {
            'question': answer.question,
            'answer': answer.answer,
            'comment': answer.comment,
            'timestamp': answer.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionData':
        """Создание из словаря"""
        session = cls(
            session_id=data.get('session_id', ''),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat())),
            status=data.get('status', 'active'),
            current_step=SessionStep(data.get('current_step', 'input_idea')),
            iteration_count=data.get('iteration_count', 0),
            competency_stage=data.get('competency_stage', ''),
            user_idea=data.get('user_idea', ''),
            original_user_idea=data.get('original_user_idea', ''),
            refined_idea=data.get('refined_idea', ''),
            final_result=data.get('final_result', ''),
            context_questions=data.get('context_questions', []),
            competency_answers=data.get('competency_answers', {}),
            competency_comments=data.get('competency_comments', {}),
            main_answers=data.get('main_answers', {}),
            main_comments=data.get('main_comments', {}),
            answers=data.get('answers', {}),
            comments=data.get('comments', {}),
            validation_history=data.get('validation_history', [])
        )
        
        # Десериализация сложных объектов
        if data.get('competency_profile'):
            session.competency_profile = cls._deserialize_competency_profile(data['competency_profile'])
        
        if data.get('domain_analysis'):
            session.domain_analysis = cls._deserialize_domain_analysis(data['domain_analysis'])
        
        if data.get('required_competencies'):
            session.required_competencies = cls._deserialize_required_competencies(data['required_competencies'])
        
        if data.get('competency_questions'):
            session.competency_questions = [cls._deserialize_question(q) for q in data['competency_questions']]
        
        if data.get('clarifying_questions'):
            session.clarifying_questions = [cls._deserialize_question(q) for q in data['clarifying_questions']]
        
        if data.get('all_iterations'):
            session.all_iterations = [cls._deserialize_iteration(it) for it in data['all_iterations']]
        
        # Десериализация all_asked_questions
        session.all_asked_questions = data.get('all_asked_questions', [])
        
        return session
    
    @classmethod
    def _deserialize_competency_profile(cls, data: Dict[str, Any]) -> CompetencyProfile:
        return CompetencyProfile(
            domain=data.get('domain', ''),
            overall_level=CompetencyLevel(data.get('overall_level', 'базовый')),
            education_level=data.get('education_level', ''),
            practical_experience=data.get('practical_experience', ''),
            theoretical_knowledge=data.get('theoretical_knowledge', ''),
            technical_skills=data.get('technical_skills', ''),
            strengths=data.get('strengths', []),
            gaps=data.get('gaps', []),
            question_strategy=data.get('question_strategy', {}),
            profile_summary=data.get('profile_summary', '')
        )
    
    @classmethod
    def _deserialize_domain_analysis(cls, data: Dict[str, Any]) -> DomainAnalysis:
        return DomainAnalysis(
            primary_domain=data.get('primary_domain', ''),
            secondary_domains=data.get('secondary_domains', []),
            complexity_level=data.get('complexity_level', 'средняя'),
            requires_technical_knowledge=data.get('requires_technical_knowledge', False),
            requires_specialized_knowledge=data.get('requires_specialized_knowledge', False),
            domain_description=data.get('domain_description', '')
        )
    
    @classmethod
    def _deserialize_required_competencies(cls, data: Dict[str, Any]) -> RequiredCompetencies:
        return RequiredCompetencies(
            domain=data.get('domain', ''),
            competencies=data.get('competencies', []),
            knowledge=data.get('knowledge', []),
            skills=data.get('skills', []),
            experience=data.get('experience', [])
        )
    
    @classmethod
    def _deserialize_question(cls, data: Dict[str, Any]) -> Question:
        return Question(
            text=data.get('text', ''),
            explanation=data.get('explanation', ''),
            examples=data.get('examples', []),
            category=data.get('category', ''),
            weight=data.get('weight', 'medium'),
            adapted_for=data.get('adapted_for', '')
        )
    
    @classmethod
    def _deserialize_iteration(cls, data: Dict[str, Any]) -> SessionIteration:
        return SessionIteration(
            iteration=data.get('iteration', 0),
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            refined_idea=data.get('refined_idea', ''),
            feedback_type=data.get('feedback_type', ''),
            comments=data.get('comments', ''),
            questions=[cls._deserialize_question(q) for q in data.get('questions', [])],
            answers=[cls._deserialize_answer(a) for a in data.get('answers', [])]
        )
    
    @classmethod
    def _deserialize_answer(cls, data: Dict[str, Any]) -> Answer:
        return Answer(
            question=data.get('question', ''),
            answer=data.get('answer', ''),
            comment=data.get('comment', ''),
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
        ) 