import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

class BriefingLogger:
    """Логгер для AI-агента брифинга"""
    
    def __init__(self, name: str = "briefing_agent", log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Избегаем дублирования хендлеров
        if not self.logger.handlers:
            self._setup_handlers(log_file)
    
    def _setup_handlers(self, log_file: Optional[str]):
        """Настройка обработчиков логов"""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Консольный вывод
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Файловый вывод
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str, session_id: str = None):
        """Информационное сообщение"""
        if session_id:
            message = f"[{session_id}] {message}"
        self.logger.info(message)
    
    def error(self, message: str, session_id: str = None, exc_info: bool = False):
        """Сообщение об ошибке"""
        if session_id:
            message = f"[{session_id}] {message}"
        self.logger.error(message, exc_info=exc_info)
    
    def debug(self, message: str, session_id: str = None):
        """Отладочное сообщение"""
        if session_id:
            message = f"[{session_id}] {message}"
        self.logger.debug(message)
    
    def warning(self, message: str, session_id: str = None):
        """Предупреждение"""
        if session_id:
            message = f"[{session_id}] {message}"
        self.logger.warning(message)

# Глобальный экземпляр логгера
logger = BriefingLogger("briefing_agent", "logs/briefing.log") 