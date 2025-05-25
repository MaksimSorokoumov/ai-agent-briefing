#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Пример использования новой логики многоэтапного анализа компетенций
"""

from neural_network import NeuralNetwork

def example_competency_analysis():
    """
    Демонстрация новой логики работы с компетенциями
    """
    
    # Инициализация нейросети
    nn = NeuralNetwork()
    
    # Пример запроса пользователя
    user_idea = "Хочу придумать новое блюдо из доступных мне ингредиентов"
    
    print("🔍 ЭТАП 1: Анализ запроса и определение компетенций")
    print(f"Запрос пользователя: '{user_idea}'")
    print()
    
    # Этап 1: Многоэтапный анализ
    analysis_result = nn.analyze_user_request_and_generate_competency_assessment(user_idea)
    
    print("📋 Контекстно-специфичные вопросы:")
    for i, question in enumerate(analysis_result['context_questions'], 1):
        print(f"{i}. {question}")
    print()
    
    print("🎯 Необходимые компетенции:")
    competencies = analysis_result['required_competencies']
    print(f"Область: {competencies['domain']}")
    print(f"Компетенции: {', '.join(competencies['competencies'])}")
    print(f"Знания: {', '.join(competencies['knowledge'])}")
    print(f"Умения: {', '.join(competencies['skills'])}")
    print(f"Опыт: {', '.join(competencies['experience'])}")
    print()
    
    print("❓ Вопросы для оценки компетенций:")
    for i, q_data in enumerate(analysis_result['competency_questions'], 1):
        print(f"{i}. {q_data['question']} ({q_data['category']})")
    print()
    
    # Симуляция ответов пользователя
    print("🔍 ЭТАП 2: Обработка ответов пользователя")
    
    # Пример ответов (в реальности будут от пользователя)
    competency_answers = {
        "Есть ли у вас образование в области Кулинария?": "Нет",
        "Имеете ли вы практический опыт в Кулинария?": "Да", 
        "Умеете ли вы готовить основные блюда?": "Да",
        "Знакомы ли вы с принципами сочетания продуктов?": "Нет"
    }
    
    print("Ответы пользователя:")
    for question, answer in competency_answers.items():
        print(f"- {question}: {answer}")
    print()
    
    # Этап 2: Построение профиля и генерация адаптивных вопросов
    final_result = nn.build_competency_profile_and_generate_questions(
        user_idea,
        competency_answers,
        analysis_result['required_competencies'],
        analysis_result['context_questions']
    )
    
    print("👤 Профиль компетенций пользователя:")
    profile = final_result['competency_profile']
    print(f"Общий уровень: {profile['overall_level']}")
    print(f"Сильные стороны: {', '.join(profile['strengths'])}")
    print(f"Пробелы: {', '.join(profile['gaps'])}")
    print(f"Стратегия: {profile['question_strategy']['complexity_level']} вопросы")
    print()
    
    print("🎯 Адаптивные вопросы для брифинга:")
    for i, q_data in enumerate(final_result['questions'], 1):
        print(f"{i}. {q_data['question']}")
        if q_data.get('explanation'):
            print(f"   💡 {q_data['explanation']}")
        if q_data.get('examples'):
            print(f"   📝 Примеры: {', '.join(q_data['examples'])}")
        print(f"   🔧 {q_data['adapted_for']}")
        print()

if __name__ == "__main__":
    example_competency_analysis() 