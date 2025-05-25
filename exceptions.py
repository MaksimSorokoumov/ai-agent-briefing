"""Кастомные исключения для AI-агента брифинга"""

class BriefingError(Exception):
    """Базовое исключение для системы брифинга"""
    pass

class AIConnectionError(BriefingError):
    """Ошибка подключения к AI-сервису"""
    def __init__(self, message: str = "Не удалось подключиться к AI-сервису"):
        self.message = message
        super().__init__(self.message)

class InvalidResponseError(BriefingError):
    """Ошибка некорректного ответа от AI"""
    def __init__(self, message: str = "Получен некорректный ответ от AI"):
        self.message = message
        super().__init__(self.message)

class SessionNotFoundError(BriefingError):
    """Ошибка - сессия не найдена"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.message = f"Сессия {session_id} не найдена"
        super().__init__(self.message)

class ValidationError(BriefingError):
    """Ошибка валидации данных"""
    def __init__(self, message: str, field: str = None):
        self.field = field
        self.message = message
        super().__init__(self.message)

class QuestionGenerationError(BriefingError):
    """Ошибка генерации вопросов"""
    def __init__(self, message: str = "Не удалось сгенерировать вопросы"):
        self.message = message
        super().__init__(self.message)

class CompetencyAnalysisError(BriefingError):
    """Ошибка анализа компетенций"""
    def __init__(self, message: str = "Не удалось проанализировать компетенции"):
        self.message = message
        super().__init__(self.message)

class IdeaProcessingError(BriefingError):
    """Ошибка обработки идеи"""
    def __init__(self, message: str = "Не удалось обработать идею"):
        self.message = message
        super().__init__(self.message) 