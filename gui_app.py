import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from session_manager import SessionManager
from neural_network import NeuralNetwork
from config import SessionStep
from session_monitor import session_monitor
from logger import logger
import requests


class AIBriefingGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI-Агент Брифинга")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Инициализация компонентов
        self.session_manager = SessionManager()
        self.neural_network = NeuralNetwork()
        self.current_session_id = None
        
        # Создание интерфейса
        self.create_widgets()
        self.update_session_list()
        
        # Проверка подключения к LM Studio
        self.check_lm_studio_status()
    
    def create_widgets(self):
        """Создание виджетов интерфейса"""
        # Главный контейнер
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Левая панель - управление сессиями
        self.create_sidebar(main_frame)
        
        # Правая панель - основной контент
        self.create_main_content(main_frame)
    
    def create_sidebar(self, parent):
        """Создание боковой панели"""
        sidebar_frame = ttk.LabelFrame(parent, text="🗂️ Управление сессиями", padding=10)
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Статус LM Studio
        self.lm_status_label = ttk.Label(sidebar_frame, text="🔴 LM Studio недоступен")
        self.lm_status_label.pack(pady=(0, 10))
        
        # Кнопка новой сессии
        new_session_btn = ttk.Button(
            sidebar_frame, 
            text="➕ Новая сессия",
            command=self.create_new_session
        )
        new_session_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Список сессий
        ttk.Label(sidebar_frame, text="📋 Сессии:").pack(anchor=tk.W)
        
        # Фрейм для списка сессий
        sessions_frame = ttk.Frame(sidebar_frame)
        sessions_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Список сессий с прокруткой
        self.sessions_listbox = tk.Listbox(sessions_frame, height=15, font=('Arial', 9))
        scrollbar = ttk.Scrollbar(sessions_frame, orient=tk.VERTICAL, command=self.sessions_listbox.yview)
        self.sessions_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.sessions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Добавляем прокрутку колесом мыши для списка сессий
        def _on_mousewheel_sessions(event):
            self.sessions_listbox.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.sessions_listbox.bind("<MouseWheel>", _on_mousewheel_sessions)
        
        # Привязка событий
        self.sessions_listbox.bind('<Double-Button-1>', self.load_selected_session)
        
        # Кнопки управления сессиями
        session_buttons_frame = ttk.Frame(sidebar_frame)
        session_buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        load_btn = ttk.Button(session_buttons_frame, text="Загрузить", command=self.load_selected_session)
        load_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        delete_btn = ttk.Button(session_buttons_frame, text="Удалить", command=self.delete_selected_session)
        delete_btn.pack(side=tk.LEFT)
    
    def create_main_content(self, parent):
        """Создание основной области контента"""
        self.content_frame = ttk.Frame(parent)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Заголовок
        self.title_label = ttk.Label(
            self.content_frame, 
            text="🤖 AI-Агент Брифинга", 
            font=('Arial', 16, 'bold')
        )
        self.title_label.pack(pady=(0, 20))
        
        # Индикатор прогресса
        self.progress_frame = ttk.Frame(self.content_frame)
        self.progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Основная область контента
        self.main_content_frame = ttk.Frame(self.content_frame)
        self.main_content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Показываем начальный экран
        self.show_welcome_screen()
    
    def show_welcome_screen(self):
        """Показ приветственного экрана"""
        self.clear_main_content()
        
        welcome_frame = ttk.Frame(self.main_content_frame)
        welcome_frame.pack(expand=True)
        
        ttk.Label(
            welcome_frame, 
            text="Добро пожаловать в AI-Агент Брифинга!", 
            font=('Arial', 14, 'bold')
        ).pack(pady=20)
        
        ttk.Label(
            welcome_frame,
            text="Создайте новую сессию или выберите существующую из списка слева",
            font=('Arial', 10)
        ).pack()
    
    def clear_main_content(self):
        """Очистка основной области контента"""
        for widget in self.main_content_frame.winfo_children():
            widget.destroy()
    
    def create_new_session(self):
        """Создание новой сессии"""
        try:
            session_id = self.session_manager.create_session()
            self.current_session_id = session_id
            self.update_session_list()
            self.show_input_idea_step()
            logger.info(f"Создана новая сессия: {session_id}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать сессию: {str(e)}")
            logger.error(f"Ошибка создания сессии: {e}")
    
    def update_session_list(self):
        """Обновление списка сессий"""
        try:
            sessions = self.session_manager.get_all_sessions()
            self.sessions_listbox.delete(0, tk.END)
            
            for session in sessions[:20]:  # Показываем последние 20
                status_emoji = "✅" if session['status'] == 'completed' else "🔄"
                display_text = f"{status_emoji} {session['user_idea'][:40]}..."
                self.sessions_listbox.insert(tk.END, display_text)
                
            # Сохраняем данные сессий для доступа
            self.session_data = sessions[:20]
            
        except Exception as e:
            logger.error(f"Ошибка обновления списка сессий: {e}")
    
    def load_selected_session(self, event=None):
        """Загрузка выбранной сессии"""
        selection = self.sessions_listbox.curselection()
        if not selection:
            return
        
        try:
            session_index = selection[0]
            session = self.session_data[session_index]
            self.current_session_id = session['session_id']
            
            # Загружаем данные сессии
            data = self.session_manager.load_session(self.current_session_id)
            
            # Показываем соответствующий шаг
            self.show_current_step(data)
            
            logger.info(f"Загружена сессия: {self.current_session_id}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить сессию: {str(e)}")
            logger.error(f"Ошибка загрузки сессии: {e}")
    
    def delete_selected_session(self):
        """Удаление выбранной сессии"""
        selection = self.sessions_listbox.curselection()
        if not selection:
            return
        
        if messagebox.askyesno("Подтверждение", "Удалить выбранную сессию?"):
            try:
                session_index = selection[0]
                session = self.session_data[session_index]
                self.session_manager.delete_session(session['session_id'])
                self.update_session_list()
                
                if self.current_session_id == session['session_id']:
                    self.current_session_id = None
                    self.show_welcome_screen()
                
                logger.info(f"Удалена сессия: {session['session_id']}")
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить сессию: {str(e)}")
                logger.error(f"Ошибка удаления сессии: {e}")
    
    def show_current_step(self, data):
        """Показ текущего шага сессии"""
        if not data:
            self.show_welcome_screen()
            return
        
        step = data.current_step
        
        if step == SessionStep.INPUT_IDEA:
            self.show_input_idea_step()
        elif step == SessionStep.COMPETENCY_ANALYSIS:
            self.show_competency_analysis_step()
        elif step == SessionStep.GENERATE_QUESTIONS:
            self.show_generate_questions_step()
        elif step == SessionStep.ANSWER_QUESTIONS:
            self.show_answer_questions_step()
        elif step == SessionStep.REFORMULATE_QUESTIONS:
            self.show_reformulate_questions_step()
        elif step == SessionStep.GENERATE_REFINED:
            self.show_generate_refined_step()
        elif step == SessionStep.VALIDATE_IDEA:
            self.show_validate_idea_step()
        elif step == SessionStep.COMPLETED:
            self.show_completed_session()
        else:
            self.show_welcome_screen()
    
    def show_validate_idea_step(self):
        """Шаг валидации идеи (заглушка)"""
        # Этот шаг обычно автоматически переходит к завершению
        self.show_completed_session()
    
    def show_input_idea_step(self):
        """Шаг ввода идеи"""
        self.clear_main_content()
        
        # Заголовок
        ttk.Label(
            self.main_content_frame,
            text="🎯 Опишите вашу идею",
            font=('Arial', 14, 'bold')
        ).pack(pady=(0, 10))
        
        ttk.Label(
            self.main_content_frame,
            text="Расскажите о своей идее своими словами. Не беспокойтесь о деталях - мы поможем их прояснить!",
            wraplength=600
        ).pack(pady=(0, 20))
        
        # Поле ввода идеи
        self.idea_text = scrolledtext.ScrolledText(
            self.main_content_frame,
            height=8,
            width=80,
            wrap=tk.WORD,
            font=('Arial', 10)
        )
        self.idea_text.pack(pady=(0, 20))
        self.idea_text.insert(tk.END, "Например: Хочу создать приложение для изучения языков с использованием ИИ...")
        
        # Добавляем прокрутку колесом мыши
        def _on_mousewheel_idea(event):
            self.idea_text.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.idea_text.bind("<MouseWheel>", _on_mousewheel_idea)
        
        # Очистка placeholder при фокусе
        def on_focus_in_idea(event):
            current_text = self.idea_text.get(1.0, tk.END).strip()
            if current_text.startswith("Например:"):
                self.idea_text.delete(1.0, tk.END)
        
        def on_focus_out_idea(event):
            current_text = self.idea_text.get(1.0, tk.END).strip()
            if not current_text:
                self.idea_text.insert(tk.END, "Например: Хочу создать приложение для изучения языков с использованием ИИ...")
        
        self.idea_text.bind("<FocusIn>", on_focus_in_idea)
        self.idea_text.bind("<FocusOut>", on_focus_out_idea)
        
        # Кнопка начала брифинга
        start_btn = ttk.Button(
            self.main_content_frame,
            text="🚀 Начать брифинг",
            command=self.start_briefing
        )
        start_btn.pack()
    
    def start_briefing(self):
        """Начало процесса брифинга"""
        idea_text = self.idea_text.get(1.0, tk.END).strip()
        
        if not idea_text or idea_text.startswith("Например:") or len(idea_text) < 10:
            messagebox.showwarning("Внимание", "Пожалуйста, опишите вашу идею более подробно")
            return
        
        try:
            # Сохраняем идею
            data = self.session_manager.load_session(self.current_session_id)
            data.user_idea = idea_text
            data.original_user_idea = idea_text
            data.current_step = SessionStep.COMPETENCY_ANALYSIS  # Сначала анализ компетенций!
            data.competency_stage = 'start'
            self.session_manager.save_session(data)
            
            # Переходим к анализу компетенций
            self.show_competency_analysis_step()
            self.update_session_list()
            
            logger.info(f"Идея сохранена для сессии {self.current_session_id}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить идею: {str(e)}")
            logger.error(f"Ошибка сохранения идеи: {e}")
    
    def show_competency_analysis_step(self):
        """Шаг анализа компетенций пользователя"""
        self.clear_main_content()
        
        ttk.Label(
            self.main_content_frame,
            text="🎓 Анализ компетенций",
            font=('Arial', 14, 'bold')
        ).pack(pady=(0, 20))
        
        # Прогресс-бар
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            self.main_content_frame,
            variable=self.progress_var,
            mode='indeterminate'
        )
        progress_bar.pack(fill=tk.X, pady=(0, 20))
        progress_bar.start()
        
        # Статус
        self.status_label = ttk.Label(
            self.main_content_frame,
            text="Анализируем вашу идею и определяем необходимые компетенции..."
        )
        self.status_label.pack()
        
        # Запускаем анализ компетенций в отдельном потоке
        threading.Thread(target=self.analyze_competency_async, daemon=True).start()

    def show_generate_questions_step(self):
        """Шаг генерации основных вопросов (после анализа компетенций)"""
        self.clear_main_content()
        
        ttk.Label(
            self.main_content_frame,
            text="❓ Генерация адаптивных вопросов",
            font=('Arial', 14, 'bold')
        ).pack(pady=(0, 20))
        
        # Прогресс-бар
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            self.main_content_frame,
            variable=self.progress_var,
            mode='indeterminate'
        )
        progress_bar.pack(fill=tk.X, pady=(0, 20))
        progress_bar.start()
        
        # Статус
        self.status_label = ttk.Label(
            self.main_content_frame,
            text="Генерируем вопросы с учетом ваших компетенций..."
        )
        self.status_label.pack()
        
        # Запускаем генерацию в отдельном потоке
        threading.Thread(target=self.generate_adaptive_questions_async, daemon=True).start()
    
    def analyze_competency_async(self):
        """Асинхронный анализ компетенций пользователя"""
        try:
            data = self.session_manager.load_session(self.current_session_id)
            
            # Обновляем статус
            self.root.after(0, lambda: self.status_label.config(text="Анализируем область знаний..."))
            
            # Используем правильный метод для анализа компетенций
            competency_result = self.neural_network.analyze_user_request_and_generate_competency_assessment(data.user_idea)
            
            # Сохраняем результат анализа
            data.context_questions = competency_result['context_questions']
            data.required_competencies = competency_result['required_competencies']
            data.competency_questions = competency_result['competency_questions']
            
            # Добавляем новые вопросы в список всех заданных вопросов
            for question in data.competency_questions:
                if question.text not in data.all_asked_questions:
                    data.all_asked_questions.append(question.text)
            
            # Переходим к ответам на вопросы о компетенциях
            if data.competency_questions:
                data.current_step = SessionStep.ANSWER_QUESTIONS
                data.competency_stage = 'assessment'  # Указываем, что это этап оценки компетенций
                self.session_manager.save_session(data)
                
                # Переходим к ответам на вопросы о компетенциях
                self.root.after(0, self.show_competency_questions_step)
            else:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", "Не удалось сгенерировать вопросы о компетенциях"))
                
        except Exception as e:
            error_msg = f"Ошибка анализа компетенций: {str(e)}"
            logger.error(error_msg)
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("Ошибка", msg))

    def generate_adaptive_questions_async(self):
        """Асинхронная генерация адаптивных вопросов (после анализа компетенций)"""
        try:
            data = self.session_manager.load_session(self.current_session_id)
            
            # Обновляем статус
            self.root.after(0, lambda: self.status_label.config(text="Генерируем адаптивные вопросы..."))
            
            # Собираем все уже заданные вопросы для предотвращения дубликатов
            all_existing_questions = data.all_asked_questions.copy()
            
            # Добавляем вопросы о компетенциях
            if data.competency_questions:
                for q in data.competency_questions:
                    if q.text not in all_existing_questions:
                        all_existing_questions.append(q.text)
            
            # Используем ответы о компетенциях для генерации основных вопросов
            adaptive_result = self.neural_network.build_competency_profile_and_generate_questions(
                data.user_idea,
                data.competency_answers,
                data.required_competencies,
                data.context_questions,
                all_existing_questions
            )
            
            # Сохраняем адаптивные вопросы
            data.clarifying_questions = adaptive_result['questions']
            data.competency_profile = adaptive_result['competency_profile']
            
            # Добавляем новые вопросы в список всех заданных вопросов
            for question in data.clarifying_questions:
                if question.text not in data.all_asked_questions:
                    data.all_asked_questions.append(question.text)
            
            # Переходим к ответам на основные вопросы
            if data.clarifying_questions:
                data.current_step = SessionStep.ANSWER_QUESTIONS
                data.competency_stage = 'main'  # Указываем, что это основной этап
                self.session_manager.save_session(data)
                
                # Переходим к ответам на основные вопросы
                self.root.after(0, self.show_main_questions_step)
            else:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", "Не удалось сгенерировать адаптивные вопросы"))
                
        except Exception as e:
            error_msg = f"Ошибка генерации адаптивных вопросов: {str(e)}"
            logger.error(error_msg)
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("Ошибка", msg))
    

    
    def show_competency_questions_step(self):
        """Шаг ответов на вопросы о компетенциях"""
        self.clear_main_content()
        
        data = self.session_manager.load_session(self.current_session_id)
        questions = [q.text for q in data.competency_questions] if data and data.competency_questions else []
        
        ttk.Label(
            self.main_content_frame,
            text="🎓 Оценка компетенций",
            font=('Arial', 14, 'bold')
        ).pack(pady=(0, 10))
        
        ttk.Label(
            self.main_content_frame,
            text="Для лучшего понимания вашего уровня знаний, ответьте на несколько вопросов:",
            wraplength=600
        ).pack(pady=(0, 20))
        
        self._show_questions_form(questions, self.submit_competency_answers)

    def show_main_questions_step(self):
        """Шаг ответов на основные вопросы (после анализа компетенций)"""
        self.clear_main_content()
        
        data = self.session_manager.load_session(self.current_session_id)
        questions = [q.text for q in data.clarifying_questions] if data and data.clarifying_questions else []
        
        ttk.Label(
            self.main_content_frame,
            text="❓ Детализация идеи",
            font=('Arial', 14, 'bold')
        ).pack(pady=(0, 10))
        
        ttk.Label(
            self.main_content_frame,
            text="Теперь давайте детально обсудим вашу идею:",
            wraplength=600
        ).pack(pady=(0, 20))
        
        self._show_questions_form(questions, self.submit_main_answers)

    def show_answer_questions_step(self):
        """Шаг ответов на вопросы (универсальный метод для совместимости)"""
        data = self.session_manager.load_session(self.current_session_id)
        
        # Определяем, какой этап сейчас
        if hasattr(data, 'competency_stage') and data.competency_stage == 'assessment':
            self.show_competency_questions_step()
        elif hasattr(data, 'competency_stage') and data.competency_stage == 'main':
            self.show_main_questions_step()
        else:
            # Fallback для старых сессий
            self.show_competency_questions_step()

    def _show_questions_form(self, questions, submit_callback):
        """Универсальный метод для показа формы с вопросами"""
        # Создаем скроллируемую область для вопросов
        canvas = tk.Canvas(self.main_content_frame)
        scrollbar = ttk.Scrollbar(self.main_content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Добавляем прокрутку колесом мыши
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)
        
        # Поля для ответов (радиокнопки и комментарии)
        self.answer_vars = []  # Переменные для радиокнопок
        self.comment_entries = []  # Поля для комментариев
        
        for i, question in enumerate(questions):
            # Фрейм для вопроса
            q_frame = ttk.LabelFrame(scrollable_frame, text=f"Вопрос {i+1}", padding=10)
            q_frame.pack(fill=tk.X, pady=(0, 10), padx=10)
            
            # Текст вопроса (с возможностью выделения)
            question_label = tk.Label(
                q_frame, 
                text=question, 
                wraplength=500,
                justify=tk.LEFT,
                font=('Arial', 12),
                bg='white',
                relief=tk.FLAT,
                padx=5,
                pady=5
            )
            question_label.pack(anchor=tk.W, pady=(0, 15), fill=tk.X)
            
            # Делаем текст выделяемым
            question_label.bind("<Button-1>", lambda e: e.widget.focus_set())
            question_label.bind("<Control-a>", lambda e: e.widget.selection_range(0, tk.END))
            
            # Радиокнопки для выбора ответа
            answer_var = tk.StringVar(value="")
            self.answer_vars.append(answer_var)
            
            options_frame = ttk.Frame(q_frame)
            options_frame.pack(fill=tk.X, pady=(0, 10))
            
            # Радиокнопки без иконок
            ttk.Radiobutton(
                options_frame, 
                text="Да", 
                variable=answer_var, 
                value="Да"
            ).pack(side=tk.LEFT, padx=(0, 20))
            
            ttk.Radiobutton(
                options_frame, 
                text="Нет", 
                variable=answer_var, 
                value="Нет"
            ).pack(side=tk.LEFT, padx=(0, 20))
            
            ttk.Radiobutton(
                options_frame, 
                text="Доверяю решение ИИ", 
                variable=answer_var, 
                value="Доверяю решение ИИ"
            ).pack(side=tk.LEFT)
            
            # Поле для комментария
            comment_entry = scrolledtext.ScrolledText(
                q_frame, 
                height=2, 
                width=60,
                wrap=tk.WORD,
                font=('Arial', 9)
            )
            comment_entry.pack(fill=tk.X, pady=(10, 0))
            comment_entry.insert(tk.END, "Место для комментария (не обязательно)")
            comment_entry.config(fg='#888888')  # Светло-серый цвет
            
            # Очистка placeholder при фокусе
            def on_focus_in(event, entry=comment_entry):
                if entry.get(1.0, tk.END).strip() == "Место для комментария (не обязательно)":
                    entry.delete(1.0, tk.END)
                    entry.config(fg='black')  # Возвращаем черный цвет
            
            def on_focus_out(event, entry=comment_entry):
                if not entry.get(1.0, tk.END).strip():
                    entry.insert(tk.END, "Место для комментария (не обязательно)")
                    entry.config(fg='#888888')  # Светло-серый цвет
            
            comment_entry.bind("<FocusIn>", on_focus_in)
            comment_entry.bind("<FocusOut>", on_focus_out)
            
            self.comment_entries.append(comment_entry)
        
        # Кнопка отправки ответов в самом низу
        submit_btn = ttk.Button(
            scrollable_frame,
            text="Отправить ответы",
            command=submit_callback
        )
        submit_btn.pack(pady=(20, 10))
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def submit_competency_answers(self):
        """Отправка ответов на вопросы о компетенциях"""
        # Собираем ответы из радиокнопок
        radio_answers = []
        for var in self.answer_vars:
            radio_answers.append(var.get())
        
        # Собираем комментарии
        comments = []
        for entry in self.comment_entries:
            comment = entry.get(1.0, tk.END).strip()
            if comment == "Место для комментария (не обязательно)":
                comment = ""
            comments.append(comment)
        
        # Проверяем, что есть хотя бы один ответ
        if not any(radio_answers):
            messagebox.showwarning("Внимание", "Пожалуйста, выберите ответ хотя бы на один вопрос")
            return
        
        try:
            data = self.session_manager.load_session(self.current_session_id)
            questions = [q.text for q in data.competency_questions] if data.competency_questions else []
            
            # Сохраняем ответы о компетенциях с учетом радиокнопок и комментариев
            answers_dict = {}
            comments_dict = {}
            
            for i, question in enumerate(questions):
                if i < len(radio_answers) and radio_answers[i]:
                    # Если выбрано "Доверяю решение ИИ", генерируем ответ через ИИ
                    if radio_answers[i] == "Доверяю решение ИИ":
                        ai_answer = self._generate_ai_answer_for_competency(question, data.user_idea)
                        answers_dict[question] = ai_answer
                    else:
                        answers_dict[question] = radio_answers[i]
                    
                    # Сохраняем комментарий если есть
                    if i < len(comments) and comments[i]:
                        comments_dict[question] = comments[i]
            
            data.competency_answers = answers_dict
            if comments_dict:
                if not hasattr(data, 'competency_comments'):
                    data.competency_comments = {}
                data.competency_comments.update(comments_dict)
            
            data.current_step = SessionStep.GENERATE_QUESTIONS
            data.competency_stage = 'profile_built'
            self.session_manager.save_session(data)
            
            self.show_generate_questions_step()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить ответы: {str(e)}")
            logger.error(f"Ошибка сохранения ответов о компетенциях: {e}")

    def submit_main_answers(self):
        """Отправка ответов на основные вопросы"""
        # Собираем ответы из радиокнопок
        radio_answers = []
        for var in self.answer_vars:
            radio_answers.append(var.get())
        
        # Собираем комментарии
        comments = []
        for entry in self.comment_entries:
            comment = entry.get(1.0, tk.END).strip()
            if comment == "Место для комментария (не обязательно)":
                comment = ""
            comments.append(comment)
        
        # Проверяем, что есть хотя бы один ответ
        if not any(radio_answers):
            messagebox.showwarning("Внимание", "Пожалуйста, выберите ответ хотя бы на один вопрос")
            return
        
        try:
            data = self.session_manager.load_session(self.current_session_id)
            questions = [q.text for q in data.clarifying_questions] if data.clarifying_questions else []
            
            # Сохраняем ответы на основные вопросы с учетом радиокнопок и комментариев
            answers_dict = {}
            comments_dict = {}
            
            for i, question in enumerate(questions):
                if i < len(radio_answers) and radio_answers[i]:
                    # Если выбрано "Доверяю решение ИИ", генерируем ответ через ИИ
                    if radio_answers[i] == "Доверяю решение ИИ":
                        ai_answer = self._generate_ai_answer_for_main_question(question, data.user_idea, data.competency_profile)
                        answers_dict[question] = ai_answer
                    else:
                        answers_dict[question] = radio_answers[i]
                    
                    # Сохраняем комментарий если есть
                    if i < len(comments) and comments[i]:
                        comments_dict[question] = comments[i]
            
            data.main_answers = answers_dict
            if comments_dict:
                if not hasattr(data, 'main_comments'):
                    data.main_comments = {}
                data.main_comments.update(comments_dict)
            
            data.current_step = SessionStep.REFORMULATE_QUESTIONS
            self.session_manager.save_session(data)
            
            self.show_reformulate_questions_step()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить ответы: {str(e)}")
            logger.error(f"Ошибка сохранения основных ответов: {e}")
    
    def _generate_ai_answer_for_competency(self, question: str, user_idea: str) -> str:
        """Генерация ответа ИИ для вопроса о компетенциях"""
        try:
            prompt = f"""
Пользователь описал свою идею: "{user_idea}"

Вопрос о компетенциях: "{question}"

Пользователь выбрал "Доверяю решение ИИ", что означает, что он хочет, чтобы ты ответил на этот вопрос в его лучших интересах, основываясь на его идее.

Ответь "Да" или "Нет" в зависимости от того, что будет лучше для реализации его идеи. Дай краткое обоснование своего выбора.

Формат ответа: "Да/Нет - [краткое обоснование]"
"""
            
            response = self.neural_network._make_request(prompt, max_tokens=200, temperature=0.3)
            return response.strip() if response else "Да - ИИ рекомендует положительный ответ"
            
        except Exception as e:
            logger.error(f"Ошибка генерации ответа ИИ для компетенций: {e}")
            return "Да - ИИ рекомендует положительный ответ"
    
    def _generate_ai_answer_for_main_question(self, question: str, user_idea: str, competency_profile) -> str:
        """Генерация ответа ИИ для основного вопроса"""
        try:
            profile_info = ""
            if competency_profile:
                profile_info = f"Уровень компетенций пользователя: {competency_profile.overall_level.value if hasattr(competency_profile.overall_level, 'value') else competency_profile.overall_level}"
            
            prompt = f"""
Пользователь описал свою идею: "{user_idea}"
{profile_info}

Основной вопрос: "{question}"

Пользователь выбрал "Доверяю решение ИИ", что означает, что он хочет, чтобы ты ответил на этот вопрос в его лучших интересах, учитывая его идею и уровень компетенций.

Ответь "Да" или "Нет" в зависимости от того, что будет лучше для реализации его идеи. Дай краткое обоснование своего выбора.

Формат ответа: "Да/Нет - [краткое обоснование]"
"""
            
            response = self.neural_network._make_request(prompt, max_tokens=300, temperature=0.3)
            return response.strip() if response else "Да - ИИ рекомендует положительный ответ"
            
        except Exception as e:
            logger.error(f"Ошибка генерации ответа ИИ для основного вопроса: {e}")
            return "Да - ИИ рекомендует положительный ответ"
    
    def show_reformulate_questions_step(self):
        """Шаг переформулировки вопросов"""
        self.clear_main_content()
        
        ttk.Label(
            self.main_content_frame,
            text="🔧 Уточнение и переформулировка",
            font=('Arial', 14, 'bold')
        ).pack(pady=(0, 20))
        
        # Прогресс-бар
        progress_bar = ttk.Progressbar(self.main_content_frame, mode='indeterminate')
        progress_bar.pack(fill=tk.X, pady=(0, 20))
        progress_bar.start()
        
        self.status_label = ttk.Label(
            self.main_content_frame,
            text="Анализируем ваши ответы и уточняем идею..."
        )
        self.status_label.pack()
        
        # Запускаем обработку в отдельном потоке
        threading.Thread(target=self.process_answers_async, daemon=True).start()
    
    def process_answers_async(self):
        """Асинхронная обработка ответов"""
        try:
            data = self.session_manager.load_session(self.current_session_id)
            
            # Собираем все ответы и комментарии для передачи в нейросеть
            all_answers = {}
            all_comments = {}
            
            # Добавляем ответы о компетенциях
            if hasattr(data, 'competency_answers') and data.competency_answers:
                all_answers.update(data.competency_answers)
            
            # Добавляем комментарии о компетенциях
            if hasattr(data, 'competency_comments') and data.competency_comments:
                all_comments.update(data.competency_comments)
            
            # Добавляем основные ответы
            if hasattr(data, 'main_answers') and data.main_answers:
                all_answers.update(data.main_answers)
            
            # Добавляем основные комментарии
            if hasattr(data, 'main_comments') and data.main_comments:
                all_comments.update(data.main_comments)
            
            # Добавляем ответы из предыдущих итераций
            if hasattr(data, 'all_iterations') and data.all_iterations:
                for iteration in data.all_iterations:
                    if hasattr(iteration, 'answers'):
                        for answer in iteration.answers:
                            all_answers[answer.question] = answer.answer
                            if answer.comment:
                                all_comments[answer.question] = answer.comment
            
            # Обрабатываем ответы через нейросеть
            refined_idea = self.neural_network.generate_refined_idea(
                data.user_idea, 
                all_answers,
                all_comments
            )
            
            if refined_idea:
                data.refined_idea = refined_idea
                data.current_step = SessionStep.GENERATE_REFINED
                self.session_manager.save_session(data)
                
                self.root.after(0, self.show_generate_refined_step)
            else:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", "Не удалось обработать ответы"))
                
        except Exception as e:
            error_msg = f"Ошибка обработки ответов: {str(e)}"
            logger.error(error_msg)
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("Ошибка", msg))
    
    def show_generate_refined_step(self):
        """Показ уточненной идеи"""
        self.clear_main_content()
        
        data = self.session_manager.load_session(self.current_session_id)
        
        ttk.Label(
            self.main_content_frame,
            text="✨ Уточненная идея",
            font=('Arial', 14, 'bold')
        ).pack(pady=(0, 20))
        
        # Показываем уточненную идею
        refined_text = scrolledtext.ScrolledText(
            self.main_content_frame,
            height=15,
            width=80,
            wrap=tk.WORD,
            font=('Arial', 10)
        )
        refined_text.pack(pady=(0, 20))
        refined_text.insert(tk.END, data.refined_idea if data else "")
        refined_text.config(state=tk.DISABLED)
        
        # Добавляем прокрутку колесом мыши
        def _on_mousewheel_refined(event):
            refined_text.yview_scroll(int(-1*(event.delta/120)), "units")
        
        refined_text.bind("<MouseWheel>", _on_mousewheel_refined)
        
        # Разрешаем выделение текста даже в disabled состоянии
        refined_text.bind("<Button-1>", lambda e: refined_text.focus_set())
        refined_text.bind("<Control-a>", lambda e: refined_text.tag_add(tk.SEL, "1.0", tk.END))
        
        # Кнопки
        buttons_frame = ttk.Frame(self.main_content_frame)
        buttons_frame.pack()
        
        approve_btn = ttk.Button(
            buttons_frame,
            text="✅ Принять",
            command=self.approve_refined_idea
        )
        approve_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        iterate_btn = ttk.Button(
            buttons_frame,
            text="🔄 Уточнить еще",
            command=self.iterate_again
        )
        iterate_btn.pack(side=tk.LEFT)
    
    def approve_refined_idea(self):
        """Принятие уточненной идеи"""
        try:
            data = self.session_manager.load_session(self.current_session_id)
            data.current_step = SessionStep.COMPLETED
            data.status = 'completed'
            self.session_manager.save_session(data)
            
            self.show_completed_session()
            self.update_session_list()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось завершить сессию: {str(e)}")
            logger.error(f"Ошибка завершения сессии: {e}")
    
    def iterate_again(self):
        """Новая итерация уточнения"""
        try:
            data = self.session_manager.load_session(self.current_session_id)
            
            # Сохраняем текущую итерацию в историю
            from models import SessionIteration, Answer
            from datetime import datetime
            
            current_iteration = SessionIteration(
                iteration=data.iteration_count,
                timestamp=datetime.now(),
                refined_idea=data.refined_idea,
                feedback_type="iterate_again",
                comments="Пользователь запросил новую итерацию",
                questions=data.clarifying_questions.copy() if data.clarifying_questions else [],
                answers=[]
            )
            
            # Добавляем ответы в итерацию
            if hasattr(data, 'main_answers') and data.main_answers:
                for question, answer in data.main_answers.items():
                    comment = ""
                    if hasattr(data, 'main_comments') and data.main_comments and question in data.main_comments:
                        comment = data.main_comments[question]
                    
                    answer_obj = Answer(
                        question=question,
                        answer=answer,
                        comment=comment,
                        timestamp=datetime.now()
                    )
                    current_iteration.answers.append(answer_obj)
            
            # Добавляем итерацию в историю
            if not hasattr(data, 'all_iterations'):
                data.all_iterations = []
            data.all_iterations.append(current_iteration)
            
            # Увеличиваем счетчик итераций
            data.iteration_count += 1
            
            # Очищаем текущие ответы для новой итерации
            data.main_answers = {}
            data.main_comments = {}
            data.clarifying_questions = []
            
            # НЕ очищаем all_asked_questions - они должны накапливаться между итерациями
            
            # Возвращаемся к генерации адаптивных вопросов (пропускаем анализ компетенций)
            data.current_step = SessionStep.GENERATE_QUESTIONS
            data.competency_stage = 'profile_built'  # Профиль уже построен
            
            self.session_manager.save_session(data)
            self.show_generate_questions_step()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось начать новую итерацию: {str(e)}")
            logger.error(f"Ошибка новой итерации: {e}")
    
    def show_completed_session(self):
        """Показ завершенной сессии"""
        self.clear_main_content()
        
        data = self.session_manager.load_session(self.current_session_id)
        
        ttk.Label(
            self.main_content_frame,
            text="🎉 Брифинг завершен!",
            font=('Arial', 16, 'bold')
        ).pack(pady=(0, 20))
        
        # Исходная идея
        ttk.Label(
            self.main_content_frame,
            text="💡 Исходная идея:",
            font=('Arial', 12, 'bold')
        ).pack(anchor=tk.W, pady=(0, 5))
        
        original_text = scrolledtext.ScrolledText(
            self.main_content_frame,
            height=5,
            width=80,
            wrap=tk.WORD,
            font=('Arial', 10)
        )
        original_text.pack(pady=(0, 20))
        original_text.insert(tk.END, data.original_user_idea if data else "")
        original_text.config(state=tk.DISABLED)
        
        # Добавляем прокрутку и выделение для исходной идеи
        def _on_mousewheel_original(event):
            original_text.yview_scroll(int(-1*(event.delta/120)), "units")
        
        original_text.bind("<MouseWheel>", _on_mousewheel_original)
        original_text.bind("<Button-1>", lambda e: original_text.focus_set())
        original_text.bind("<Control-a>", lambda e: original_text.tag_add(tk.SEL, "1.0", tk.END))
        
        # Финальная идея
        ttk.Label(
            self.main_content_frame,
            text="✨ Финальная идея:",
            font=('Arial', 12, 'bold')
        ).pack(anchor=tk.W, pady=(0, 5))
        
        final_text = scrolledtext.ScrolledText(
            self.main_content_frame,
            height=10,
            width=80,
            wrap=tk.WORD,
            font=('Arial', 10)
        )
        final_text.pack(pady=(0, 20))
        final_text.insert(tk.END, data.refined_idea if data else "")
        final_text.config(state=tk.DISABLED)
        
        # Добавляем прокрутку и выделение для финальной идеи
        def _on_mousewheel_final(event):
            final_text.yview_scroll(int(-1*(event.delta/120)), "units")
        
        final_text.bind("<MouseWheel>", _on_mousewheel_final)
        final_text.bind("<Button-1>", lambda e: final_text.focus_set())
        final_text.bind("<Control-a>", lambda e: final_text.tag_add(tk.SEL, "1.0", tk.END))
        
        # Кнопка новой сессии
        new_session_btn = ttk.Button(
            self.main_content_frame,
            text="🆕 Новая сессия",
            command=self.create_new_session
        )
        new_session_btn.pack()
    
    def check_lm_studio_status(self):
        """Проверка статуса LM Studio"""
        def check_async():
            try:
                response = requests.get("http://localhost:1234/v1/models", timeout=5)
                if response.status_code == 200:
                    self.root.after(0, lambda: self.lm_status_label.config(
                        text="🟢 LM Studio подключен",
                        foreground="green"
                    ))
                else:
                    self.root.after(0, lambda: self.lm_status_label.config(
                        text="🔴 LM Studio недоступен",
                        foreground="red"
                    ))
            except:
                self.root.after(0, lambda: self.lm_status_label.config(
                    text="🔴 LM Studio недоступен",
                    foreground="red"
                ))
        
        threading.Thread(target=check_async, daemon=True).start()
        
        # Повторная проверка через 30 секунд
        self.root.after(30000, self.check_lm_studio_status)
    
    def run(self):
        """Запуск приложения"""
        self.root.mainloop()


if __name__ == "__main__":
    app = AIBriefingGUI()
    app.run() 