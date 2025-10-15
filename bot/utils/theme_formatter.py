"""Theme formatting utilities for beautiful message display."""

from datetime import datetime
from typing import List, Dict, Any


def format_themes(themes: List[Dict[str, Any]], requested_date: str = None) -> str:
    """
    Форматирует темы в красивое HTML-сообщение.
    
    Args:
        themes: Список словарей с темами
        requested_date: Дата запроса тем
    
    Returns:
        Отформатированная строка для вывода
    """
    # Маппинг источников
    source_mapping = {
        'seasonal': '🌿 Сезонный тренд',
        'trending': '📈 Рыночный тренд',
        'personal': '⭐ Персональная рекомендация',
        'market': '🔥 Популярная тема'
    }
    
    # Маппинг уверенности
    confidence_mapping = {
        'high': ('Высокая', '🟢'),
        'medium': ('Средняя', '🟡'),
        'low': ('Низкая', '🟠')
    }
    
    # Маппинг прогноза
    performance_mapping = {
        'high': '🚀 Высокая эффективность',
        'medium': '📊 Средняя эффективность',
        'low': '📉 Базовая эффективность'
    }
    
    # Эмодзи для тем
    theme_emojis = {
        'halloween': '🎃',
        'autumn': '🍂',
        'winter': '❄️',
        'christmas': '🎄',
        'new year': '🎆',
        'spring': '🌸',
        'summer': '☀️',
        'love': '❤️',
        'valentine': '💝',
        'easter': '🥚',
        'thanksgiving': '🦃',
        'хэллоуин': '🎃',
        'осень': '🍂',
        'осенние': '🍂',
        'зима': '❄️',
        'зимние': '❄️',
        'рождество': '🎄',
        'рождественские': '🎄',
        'новый год': '🎆',
        'весна': '🌸',
        'весенние': '🌸',
        'лето': '☀️',
        'летние': '☀️',
        'любовь': '❤️',
        'любовные': '❤️',
        'валентинка': '💝',
        'пасха': '🥚',
        'пасхальные': '🥚',
        'благодарение': '🦃'
    }
    
    # Формируем заголовок
    date_str = requested_date or datetime.now().strftime('%d.%m.%Y')
    result = f"📌 <b>Твои темы недели</b> (<i>запрошены {date_str}</i>)\n\n"
    
    # Форматируем каждую тему
    for i, theme_data in enumerate(themes, 1):
        # Если тема - строка, преобразуем в словарь
        if isinstance(theme_data, str):
            theme_name = theme_data
            source = 'market'
            confidence = 'medium'
            reason = 'Актуальная рыночная тема'
            performance = 'medium'
        else:
            theme_name = theme_data.get('theme', theme_data.get('theme_name', 'Неизвестная тема'))
            source = theme_data.get('source', 'market')
            confidence = theme_data.get('confidence', 'medium')
            reason = theme_data.get('reason', 'Актуальная тема')
            performance = theme_data.get('predicted_performance', 'medium')
        
        # Подбираем эмодзи для темы
        theme_emoji = ''
        theme_lower = theme_name.lower()
        for keyword, emoji in theme_emojis.items():
            if keyword in theme_lower or theme_lower in keyword:
                theme_emoji = emoji
                break
        
        # Форматируем тему
        result += f"<b>{i}. {theme_name}</b> {theme_emoji}\n"
        result += f"   ▫️ <i>Источник:</i> {source_mapping.get(source, 'Общая тема')}\n"
        
        # Форматируем уверенность
        conf_text, conf_emoji = confidence_mapping.get(confidence, ('Средняя', '🟡'))
        conf_percent = {
            'high': 80,
            'medium': 60,
            'low': 40
        }.get(confidence, 60)
        result += f"   ▫️ <i>Уверенность:</i> {conf_text} {conf_emoji} ({conf_percent}%)\n"
        
        result += f"   ▫️ <i>Прогноз:</i> {performance_mapping.get(performance, '📊 Средняя эффективность')}\n"
        
        if reason and i <= 3:  # Показываем причину только для первых 3 тем
            result += f"   ▫️ <i>Почему:</i> {reason}\n"
        
        result += "\n"
    
    # Добавляем футер
    result += "❗️ <b>Важно:</b> Все твои темы сохраняются в этом разделе. "
    result += "Ты можешь заходить сюда в любое время, чтобы пересмотреть их.\n\n"
    
    result += "⚡️ <b>Совет:</b> Не теряй время! Чем быстрее эти темы попадут в твой портфель, "
    result += "тем выше шанс, что именно твои работы получат больше продаж.\n\n"
    
    result += "🕔 <i>Следующий запрос доступен через неделю после последнего.</i>"
    
    return result


def format_single_theme(theme: str) -> str:
    """
    Форматирует одну тему для FREE пользователей.
    
    Args:
        theme: Название темы
    
    Returns:
        Отформатированная строка для вывода
    """
    # Эмодзи для тем
    theme_emojis = {
        'halloween': '🎃',
        'autumn': '🍂',
        'winter': '❄️',
        'christmas': '🎄',
        'new year': '🎆',
        'spring': '🌸',
        'summer': '☀️',
        'love': '❤️',
        'valentine': '💝',
        'easter': '🥚',
        'thanksgiving': '🦃',
        'хэллоуин': '🎃',
        'осень': '🍂',
        'осенние': '🍂',
        'зима': '❄️',
        'зимние': '❄️',
        'рождество': '🎄',
        'рождественские': '🎄',
        'новый год': '🎆',
        'весна': '🌸',
        'весенние': '🌸',
        'лето': '☀️',
        'летние': '☀️',
        'любовь': '❤️',
        'любовные': '❤️',
        'валентинка': '💝',
        'пасха': '🥚',
        'пасхальные': '🥚',
        'благодарение': '🦃'
    }
    
    # Подбираем эмодзи для темы
    theme_emoji = ''
    for keyword, emoji in theme_emojis.items():
        if keyword in theme.lower():
            theme_emoji = emoji
            break
    
    result = f"📌 <b>Твоя тема недели</b>\n\n"
    result += f"<b>1. {theme}</b> {theme_emoji}\n\n"
    
    result += "❗️ Все твои темы сохраняются в этом разделе без ограничения по времени. "
    result += "Ты можешь заходить сюда в любое время, чтобы пересмотреть их.\n\n"
    
    result += "⚡️ Но не теряй время! Чем быстрее эти темы попадут в твой портфель, "
    result += "тем выше шанс, что именно твои работы получат больше продаж."
    
    return result
