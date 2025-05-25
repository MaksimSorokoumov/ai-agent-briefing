import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from models import SessionData, SessionIteration
from config import SessionStep


class SessionManager:
    """Менеджер сессий с типизированными данными"""
    
    def __init__(self, sessions_dir: str = "sessions"):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)

    def create_session(self) -> str:
        """Создание новой сессии"""
        session_id = str(uuid.uuid4())
        session_data = SessionData(
            session_id=session_id,
            created_at=datetime.now(),
            status='active',
            current_step=SessionStep.INPUT_IDEA
        )
        
        self.save_session(session_data)
        return session_id

    def load_session(self, session_id: str) -> Optional[SessionData]:
        """Загрузка сессии"""
        file_path = self.sessions_dir / f"{session_id}.json"
        
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return SessionData.from_dict(data)
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            print(f"⚠️ Ошибка загрузки сессии {session_id}: {e}")
            return None

    def save_session(self, session_data: SessionData) -> bool:
        """Сохранение сессии"""
        session_data.updated_at = datetime.now()
        file_path = self.sessions_dir / f"{session_data.session_id}.json"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(session_data.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка сохранения сессии {session_data.session_id}: {e}")
            return False

    def update_step(self, session_id: str, step: SessionStep) -> bool:
        """Обновление текущего шага"""
        session_data = self.load_session(session_id)
        if not session_data:
            return False
        
        session_data.current_step = step
        return self.save_session(session_data)

    def add_iteration(self, session_id: str, iteration_data: Dict[str, Any]) -> bool:
        """Добавление новой итерации"""
        session_data = self.load_session(session_id)
        if not session_data:
            return False
        
        session_data.iteration_count += 1
        
        iteration = SessionIteration(
            iteration=session_data.iteration_count,
            timestamp=datetime.now(),
            refined_idea=iteration_data.get('refined_idea', ''),
            feedback_type=iteration_data.get('feedback_type', ''),
            comments=iteration_data.get('comments', '')
        )
        
        session_data.all_iterations.append(iteration)
        return self.save_session(session_data)

    def add_validation(self, session_id: str, validation_data: Dict[str, Any]) -> bool:
        """Добавление записи валидации"""
        session_data = self.load_session(session_id)
        if not session_data:
            return False
        
        validation_record = {
            'timestamp': datetime.now().isoformat(),
            **validation_data
        }
        
        session_data.validation_history.append(validation_record)
        return self.save_session(session_data)

    def complete_session(self, session_id: str, final_result: str) -> bool:
        """Завершение сессии"""
        session_data = self.load_session(session_id)
        if not session_data:
            return False
        
        session_data.status = 'completed'
        session_data.final_result = final_result
        session_data.current_step = SessionStep.COMPLETED
        return self.save_session(session_data)

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Получение списка всех сессий"""
        sessions = []
        
        for file_path in self.sessions_dir.glob("*.json"):
            session_id = file_path.stem
            session_data = self.load_session(session_id)
            
            if session_data:
                # Обрезаем длинные идеи для отображения
                user_idea = session_data.user_idea
                if len(user_idea) > 100:
                    user_idea = user_idea[:100] + '...'
                
                sessions.append({
                    'session_id': session_id,
                    'created_at': session_data.created_at.isoformat(),
                    'status': session_data.status,
                    'user_idea': user_idea,
                    'iteration_count': session_data.iteration_count,
                    'current_step': session_data.current_step.value
                })
        
        # Сортируем по дате создания (новые сначала)
        sessions.sort(key=lambda x: x['created_at'], reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """Удаление сессии"""
        file_path = self.sessions_dir / f"{session_id}.json"
        
        try:
            if file_path.exists():
                file_path.unlink()
                return True
        except Exception as e:
            print(f"⚠️ Ошибка удаления сессии {session_id}: {e}")
        
        return False

    def get_session_statistics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Получение статистики сессии"""
        session_data = self.load_session(session_id)
        if not session_data:
            return None
        
        return {
            'session_id': session_id,
            'status': session_data.status,
            'current_step': session_data.current_step.value,
            'iteration_count': session_data.iteration_count,
            'questions_count': len(session_data.clarifying_questions),
            'competency_questions_count': len(session_data.competency_questions),
            'answers_count': len(session_data.answers),
            'validations_count': len(session_data.validation_history),
            'created_at': session_data.created_at.isoformat(),
            'updated_at': session_data.updated_at.isoformat(),
            'duration_minutes': (session_data.updated_at - session_data.created_at).total_seconds() / 60
        }

    def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """Очистка старых сессий"""
        cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        deleted_count = 0
        
        for file_path in self.sessions_dir.glob("*.json"):
            if file_path.stat().st_mtime < cutoff_date:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"⚠️ Ошибка удаления старой сессии {file_path.name}: {e}")
        
        return deleted_count

    def export_session(self, session_id: str, export_path: str) -> bool:
        """Экспорт сессии в файл"""
        session_data = self.load_session(session_id)
        if not session_data:
            return False
        
        try:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(session_data.to_dict(), f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"⚠️ Ошибка экспорта сессии {session_id}: {e}")
            return False

    def import_session(self, import_path: str) -> Optional[str]:
        """Импорт сессии из файла"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            session_data = SessionData.from_dict(data)
            
            # Генерируем новый ID для избежания конфликтов
            session_data.session_id = str(uuid.uuid4())
            session_data.created_at = datetime.now()
            session_data.updated_at = datetime.now()
            
            if self.save_session(session_data):
                return session_data.session_id
            
        except Exception as e:
            print(f"⚠️ Ошибка импорта сессии: {e}")
        
        return None