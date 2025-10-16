import os
import sys
#!/usr/bin/env python3
"""
Скрипт для массового исправления всех сообщений в faq.py
"""

import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def fix_faq_messages():
    """Исправляет все сообщения в faq.py"""
    
    with open('bot/handlers/faq.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Находим все определения answer_text = """..."""
    pattern = r'(answer_text = )"""([^"]+)"""'
    
    def replace_func(match):
        prefix = match.group(1)
        text = match.group(2)
        return f'{prefix}escape_markdown("""{text}""")'
    
    # Заменяем все вхождения
    new_content = re.sub(pattern, replace_func, content, flags=re.DOTALL)
    
    # Сохраняем файл
    with open('bot/handlers/faq.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Все сообщения в faq.py исправлены!")

if __name__ == "__main__":
    fix_faq_messages()
