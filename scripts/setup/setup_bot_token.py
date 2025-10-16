import sys
"""Setup bot token for testing."""

import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def setup_bot_token():
    """Setup bot token for testing."""
    
    print("🤖 Настройка токена Telegram бота")
    print("=" * 50)
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        print("Создайте файл .env на основе env.example")
        return
    
    # Read current .env
    with open('.env', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if token is set
    if 'BOT_TOKEN=your_telegram_bot_token_here' in content:
        print("⚠️  Токен бота не установлен!")
        print("\nДля получения токена:")
        print("1. Откройте Telegram")
        print("2. Найдите @BotFather")
        print("3. Отправьте команду /newbot")
        print("4. Следуйте инструкциям")
        print("5. Скопируйте полученный токен")
        print("\nЗатем отредактируйте файл .env и замените:")
        print("BOT_TOKEN=your_telegram_bot_token_here")
        print("на:")
        print("BOT_TOKEN=ваш_реальный_токен")
        return
    
    # Check if token looks valid
    lines = content.split('\n')
    token_line = None
    for line in lines:
        if line.startswith('BOT_TOKEN='):
            token_line = line
            break
    
    if token_line:
        token = token_line.split('=', 1)[1].strip()
        if len(token) > 20 and ':' in token:
            print("✅ Токен бота найден и выглядит корректно")
            print(f"Токен: {token[:10]}...{token[-10:]}")
        else:
            print("❌ Токен бота выглядит некорректно")
            print("Проверьте формат токена в .env файле")
    else:
        print("❌ Токен бота не найден в .env файле")

if __name__ == "__main__":
    setup_bot_token()
