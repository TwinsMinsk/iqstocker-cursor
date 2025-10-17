# 🚀 ИНСТРУКЦИЯ ПО ЗАПУСКУ И ПРОВЕРКЕ СИСТЕМЫ

## ✅ **Система готова к работе!**

### **📋 Результаты проверки:**
- ✅ **ENCRYPTION_KEY** установлен и валидный
- ✅ **DATABASE_URL** настроен (SQLite)
- ✅ **База данных** доступна
- ✅ **Админ-панель** запущена
- ⚠️ **OPENAI_API_KEY** нужно настроить через админ-панель

---

## 🔧 **Команды для запуска (по порядку):**

### **1. Активировать виртуальное окружение:**
```bash
venv\Scripts\activate
```

### **2. Проверить систему:**
```bash
python test_system.py
```

### **3. Запустить админ-панель:**
```bash
python admin/app.py
```

### **4. Открыть браузер:**
```
http://localhost:5000/llm-settings
```

---

## 🎯 **Настройка ChatGPT-4o:**

### **В админ-панели:**
1. **Выберите провайдера:** "OpenAI GPT-4o"
2. **Введите API-ключ:** ваш реальный ключ OpenAI
3. **Нажмите:** "Сохранить и активировать"

### **Проверка настройки:**
```bash
python test_system.py
```

---

## 🤖 **Запуск бота (после настройки LLM):**

### **1. Запустить воркеры Dramatiq:**
```bash
python scripts/start_workers.py
```

### **2. Запустить бота:**
```bash
python bot/main.py
```

### **3. Тестировать функционал:**
- Перейти в раздел "Темы и тренды"
- Нажать "Получить темы"
- Проверить "История генерации"

---

## 🔍 **Диагностика проблем:**

### **Если админ-панель не запускается:**
```bash
# Проверить переменные окружения
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('ENCRYPTION_KEY:', os.getenv('ENCRYPTION_KEY')[:10] + '...')"
```

### **Если ошибка с базой данных:**
```bash
# Проверить подключение к БД
python -c "import sys; sys.path.append('.'); from config.database import SessionLocal; db = SessionLocal(); print('БД доступна'); db.close()"
```

### **Если LLM-сервис не работает:**
```bash
# Проверить настройки в БД
python -c "import sys; sys.path.append('.'); from config.database import SessionLocal; from database.models import LLMSettings; db = SessionLocal(); count = db.query(LLMSettings).count(); print(f'Настроек LLM: {count}'); db.close()"
```

---

## 📞 **Поддержка:**

### **Логи админ-панели:**
- Отображаются в терминале при запуске `python admin/app.py`

### **Логи бота:**
- Файл: `logs/bot.log`

### **Тестовый скрипт:**
- Файл: `test_system.py` - запускайте для диагностики

---

## 🎉 **Готово к работе!**

**Система полностью настроена и готова к генерации персонализированных тем с помощью ChatGPT-4o!**
