import time
from typing import Dict, Any, Optional
from logger import logger


class SessionMonitor:
    """Монитор состояния сессий для предотвращения зацикливания"""
    
    def __init__(self):
        self.session_states = {}
        self.max_attempts = 3
        self.max_stage_time = 300  # 5 минут на этап
    
    def track_stage_entry(self, session_id: str, stage: str) -> bool:
        """
        Отслеживает вход в этап и проверяет на зацикливание
        Возвращает True если можно продолжить, False если нужно прервать
        """
        current_time = time.time()
        
        if session_id not in self.session_states:
            self.session_states[session_id] = {}
        
        session_state = self.session_states[session_id]
        
        # Инициализируем данные этапа если их нет
        if stage not in session_state:
            session_state[stage] = {
                'attempts': 0,
                'first_entry': current_time,
                'last_entry': current_time
            }
        
        stage_data = session_state[stage]
        
        # Проверяем, не слишком ли долго находимся на этом этапе
        time_on_stage = current_time - stage_data['first_entry']
        if time_on_stage > self.max_stage_time:
            logger.warning(f"Сессия {session_id} слишком долго на этапе {stage}: {time_on_stage:.1f}с")
            return False
        
        # Проверяем количество попыток
        if stage_data['attempts'] >= self.max_attempts:
            logger.warning(f"Сессия {session_id} превысила лимит попыток на этапе {stage}: {stage_data['attempts']}")
            return False
        
        # Проверяем частоту входов (защита от быстрого зацикливания)
        time_since_last = current_time - stage_data['last_entry']
        if time_since_last < 1.0:  # Менее секунды между входами
            stage_data['attempts'] += 1
            logger.warning(f"Быстрое повторение этапа {stage} в сессии {session_id}, попытка {stage_data['attempts']}")
        
        stage_data['last_entry'] = current_time
        
        return True
    
    def mark_stage_completed(self, session_id: str, stage: str):
        """Отмечает этап как завершенный"""
        if session_id in self.session_states and stage in self.session_states[session_id]:
            self.session_states[session_id][stage]['completed'] = True
            logger.debug(f"Этап {stage} завершен для сессии {session_id}")
    
    def is_stage_completed(self, session_id: str, stage: str) -> bool:
        """Проверяет, завершен ли этап"""
        if session_id not in self.session_states:
            return False
        if stage not in self.session_states[session_id]:
            return False
        return self.session_states[session_id][stage].get('completed', False)
    
    def reset_stage(self, session_id: str, stage: str):
        """Сбрасывает состояние этапа"""
        if session_id in self.session_states and stage in self.session_states[session_id]:
            del self.session_states[session_id][stage]
            logger.debug(f"Состояние этапа {stage} сброшено для сессии {session_id}")
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Получает статистику сессии"""
        if session_id not in self.session_states:
            return {}
        
        stats = {}
        for stage, data in self.session_states[session_id].items():
            stats[stage] = {
                'attempts': data['attempts'],
                'time_spent': time.time() - data['first_entry'],
                'completed': data.get('completed', False)
            }
        
        return stats
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Очищает старые данные сессий"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        sessions_to_remove = []
        for session_id, session_state in self.session_states.items():
            # Находим самое раннее время входа
            earliest_time = min(
                stage_data['first_entry'] 
                for stage_data in session_state.values()
            )
            
            if current_time - earliest_time > max_age_seconds:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.session_states[session_id]
            logger.info(f"Удалены старые данные мониторинга для сессии {session_id}")


# Глобальный экземпляр монитора
session_monitor = SessionMonitor() 