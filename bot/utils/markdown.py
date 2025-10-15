"""
Универсальные функции для экранирования Markdown и HTML в Telegram боте.
"""

def escape_markdown(text: str) -> str:
    """Экранирует специальные символы для Markdown."""
    return (text.replace('*', '\\*')
                .replace('-', '\\-')
                .replace('(', '\\(')
                .replace(')', '\\)')
                .replace('.', '\\.')
                .replace('!', '\\!')
                .replace('_', '\\_')
                .replace('[', '\\[')
                .replace(']', '\\]')
                .replace('`', '\\`')
                .replace('+', '\\+'))


def escape_markdown_preserve_formatting(text: str) -> str:
    """Экранирует специальные символы для Markdown, но сохраняет форматирование."""
    # Сначала защищаем форматирование
    text = text.replace('**', '___BOLD___')
    text = text.replace('*', '___ITALIC___')
    
    # Экранируем остальные символы (кроме _)
    text = (text.replace('-', '\\-')
                .replace('(', '\\(')
                .replace(')', '\\)')
                .replace('.', '\\.')
                .replace('!', '\\!')
                .replace('[', '\\[')
                .replace(']', '\\]')
                .replace('`', '\\`')
                .replace('+', '\\+'))
    
    # Восстанавливаем форматирование
    text = text.replace('___BOLD___', '**')
    text = text.replace('___ITALIC___', '*')
    
    return text


def escape_html(text: str) -> str:
    """Экранирует специальные символы для HTML."""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))


def format_html(text: str) -> str:
    """Безопасное форматирование HTML текста."""
    return escape_html(text)
