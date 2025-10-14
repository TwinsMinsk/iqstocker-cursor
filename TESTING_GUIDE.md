# 🧪 Testing Guide for IQStocker Bot

## Обзор тестирования

Этот документ описывает все доступные тесты для проверки функциональности IQStocker Bot перед деплоем на Railway.

## 🚀 Быстрый старт

### 1. Быстрое тестирование (рекомендуется перед деплоем)
```bash
python test_quick.py
```
**Время выполнения:** ~30 секунд  
**Что тестирует:** Критические импорты, подключение к БД, AI компоненты, админ-панель

### 2. Полное тестирование
```bash
python run_all_tests.py
```
**Время выполнения:** ~5-10 минут  
**Что тестирует:** Все компоненты системы

## 📋 Доступные тесты

### 🔬 Unit Tests
```bash
# Все unit тесты
python -m pytest tests/ -v

# Только AI компоненты
python -m pytest tests/test_ai_components.py -v

# Только интеграционные тесты
python -m pytest tests/test_ai_integration.py -v
```

### 🧪 Comprehensive Tests
```bash
python test_comprehensive.py
```
**Тестирует:**
- Подключение к базе данных
- Все AI компоненты
- Админ-панель
- Bot handlers
- Enhanced Theme Manager
- Report Generator
- Миграции БД
- Переменные окружения
- Health check

### 🏭 Production Tests
```bash
python test_production.py
```
**Тестирует:**
- Переменные окружения
- Формат URL баз данных
- Docker конфигурацию
- Файл requirements.txt
- Настройки безопасности
- Права доступа к файлам
- Health check endpoint
- Railway конфигурацию

### 🤖 Bot Tests
```bash
python test_bot_local.py
```
**Тестирует:**
- Инициализацию бота
- Импорт всех handlers
- Импорт keyboards
- Импорт middlewares
- Импорт states
- Импорт utils
- Импорт core модулей
- Импорт моделей БД
- Импорт config модулей
- Импорт админ-панели

## 🎯 Пошаговый план тестирования

### Этап 1: Подготовка
```bash
# 1. Убедитесь, что все зависимости установлены
pip install -r requirements.txt

# 2. Проверьте переменные окружения
cp env.example .env
# Отредактируйте .env файл с вашими настройками

# 3. Инициализируйте базу данных
python init_railway_db.py
```

### Этап 2: Быстрое тестирование
```bash
# Запустите быстрые тесты
python test_quick.py
```

### Этап 3: Детальное тестирование
```bash
# Если быстрые тесты прошли, запустите полные тесты
python run_all_tests.py
```

### Этап 4: Production готовность
```bash
# Проверьте production конфигурацию
python test_production.py
```

## 🔧 Troubleshooting

### Ошибки импорта
```bash
# Проверьте PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Или добавьте в начало скриптов
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

### Ошибки базы данных
```bash
# Проверьте подключение к БД
python -c "from config.database import SessionLocal; print('DB OK')"

# Проверьте миграции
alembic current
alembic history
```

### Ошибки AI компонентов
```bash
# Проверьте API ключи
python -c "from config.settings import settings; print('OpenAI:', bool(settings.openai_api_key))"

# Проверьте Redis
python -c "from config.database import redis_client; print('Redis:', redis_client.ping())"
```

## 📊 Интерпретация результатов

### ✅ Успешные тесты
```
✅ All quick tests passed! Ready for deployment.
```
**Действие:** Можно переходить к деплою

### ❌ Неуспешные тесты
```
❌ Some tests failed. Check errors above.
```
**Действие:** Исправьте ошибки и запустите тесты снова

### ⚠️ Частично успешные тесты
```
Success Rate: 85.0%
```
**Действие:** Проверьте неуспешные тесты и решите, критичны ли они

## 🚀 Готовность к деплою

### Минимальные требования
- ✅ Все быстрые тесты прошли
- ✅ Production тесты прошли
- ✅ Переменные окружения настроены
- ✅ База данных доступна

### Рекомендуемые требования
- ✅ Все тесты прошли (100% success rate)
- ✅ Unit тесты прошли
- ✅ Интеграционные тесты прошли
- ✅ Code quality проверки прошли

## 🔍 Мониторинг после деплоя

### Health Check
```bash
curl https://your-app.railway.app/health
```

### Логи
```bash
# Railway CLI
railway logs

# Или через веб-интерфейс Railway
```

### Метрики
- Response time < 2 секунды
- Success rate > 95%
- Memory usage < 512MB
- CPU usage < 50%

## 📝 Чек-лист перед деплоем

- [ ] Все быстрые тесты прошли
- [ ] Production тесты прошли
- [ ] Переменные окружения настроены
- [ ] База данных доступна
- [ ] Redis доступен
- [ ] API ключи настроены
- [ ] Docker конфигурация готова
- [ ] Railway конфигурация готова
- [ ] Health check работает
- [ ] Логирование настроено

## 🆘 Поддержка

Если тесты не проходят:

1. **Проверьте логи ошибок** - они содержат детальную информацию
2. **Проверьте переменные окружения** - убедитесь, что все необходимые переменные установлены
3. **Проверьте зависимости** - убедитесь, что все пакеты установлены
4. **Проверьте подключения** - убедитесь, что БД и Redis доступны
5. **Запустите тесты по отдельности** - для выявления конкретной проблемы

## 📚 Дополнительные ресурсы

- [AI Features Guide](docs/AI_FEATURES_GUIDE.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
