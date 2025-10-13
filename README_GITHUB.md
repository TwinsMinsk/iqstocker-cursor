# IQStocker Bot

<div align="center">

![IQStocker Logo](https://via.placeholder.com/200x100/4A90E2/FFFFFF?text=IQStocker)

**Telegram-бот для аналитики портфолио авторов на стоковых площадках**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-green.svg)](https://docs.aiogram.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://postgresql.org)
[![Railway](https://img.shields.io/badge/Deploy%20on-Railway-0B0D0E.svg)](https://railway.app)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[🚀 Быстрый старт](#-быстрый-старт) • [📖 Документация](#-документация) • [🌐 Демо](#-демо) • [🤝 Вклад](#-вклад)

</div>

---

## 📋 Описание

**IQStocker** — это профессиональный Telegram-бот для авторов стоковых площадок (Adobe Stock, Shutterstock и др.). Бот предоставляет мощные инструменты для анализа портфеля, генерации тем для съемок, отслеживания трендов и образовательные материалы для увеличения продаж.

### 🎯 Основные возможности

- 📊 **Аналитика портфеля** - Анализ CSV-файлов с продажами, определение новых работ по ID (начинаются на 150)
- 🎨 **Темы для съемки** - Еженедельная подборка тем на основе трендов и персональных данных
- 🏆 **Топ тем** - Подборка лучших тем по продажам и доходу
- 🎥 **Видеоуроки** - База образовательных материалов по стокам
- 📅 **Календарь стокера** - AI-генерация ежемесячных подсказок с ручным управлением
- 💳 **Система подписок** - FREE, TEST_PRO, PRO, ULTRA с различными лимитами
- 🔧 **Админ-панель** - Полное управление ботом, пользователями и контентом

## 🛠 Технологический стек

### Backend
- **Python 3.11+** - Основной язык программирования
- **aiogram 3.x** - Современная библиотека для Telegram Bot API
- **SQLAlchemy** - ORM для работы с базой данных
- **Alembic** - Миграции базы данных

### База данных
- **PostgreSQL** - Основная база данных (продакшен)
- **SQLite** - База данных для разработки
- **Redis** - Кеширование и очереди задач

### AI и парсинг
- **OpenAI GPT-4** - Генерация календаря и категоризация тем
- **pandas** - Обработка CSV файлов
- **aiohttp** - Асинхронные HTTP запросы
- **BeautifulSoup4** - Парсинг веб-страниц

### Инфраструктура
- **Railway** - Основная платформа развертывания
- **Docker** - Контейнеризация
- **Flask** - Админ-панель
- **APScheduler** - Планировщик задач

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.11+
- PostgreSQL (для продакшена)
- Redis (опционально)
- Telegram Bot Token
- OpenAI API Key

### Локальная установка

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/TwinsMinsk/iqstocker-cursor.git
cd iqstocker-cursor
```

2. **Создайте виртуальное окружение:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

3. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

4. **Настройте переменные окружения:**
```bash
cp env.example .env
# Отредактируйте .env файл с вашими настройками
```

5. **Инициализируйте базу данных:**
```bash
python init_db.py
```

6. **Создайте админского пользователя:**
```bash
python setup_admin_user.py
```

7. **Запустите бота:**
```bash
python bot/main.py
```

### 🧪 Тестирование

```bash
# Протестируйте новые функции
python test_final_features.py

# Демо-режим
python demo_mode.py
```

## 🌐 Развертывание

### Railway (Рекомендуется)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template)

1. Подключите репозиторий к Railway
2. Добавьте PostgreSQL и Redis
3. Настройте переменные окружения
4. Деплой автоматически инициализирует БД

**Подробная инструкция:** [DEPLOYMENT_RAILWAY.md](DEPLOYMENT_RAILWAY.md)

### Docker

```bash
# Сборка образа
docker build -t iqstocker-bot .

# Запуск с docker-compose
docker-compose up -d
```

## 📖 Документация

- [📋 Техническое задание](Miro%20ТЗ.md) - Полное ТЗ проекта
- [🚀 Быстрый старт](QUICK_START.md) - Детальные инструкции по запуску
- [🌐 Развертывание на Railway](DEPLOYMENT_RAILWAY.md) - Полная инструкция по деплою
- [📊 Аналитика](ANALYTICS_GUIDE.md) - Руководство по аналитике портфеля
- [✅ Статус проекта](PROJECT_COMPLETION_REPORT.md) - Отчет о завершении проекта

## 🎯 Новые возможности

### Умное определение новых работ
- Работы с ID, начинающимися на "150" (10 цифр), автоматически определяются как новые
- Конфигурируемый параметр `NEW_WORKS_MONTHS` для альтернативного определения по дате

### AI-календарь стокера
- **GPT-4 генерация** - Автоматическое создание календаря с учетом сезонов и трендов
- **Умные шаблоны** - Резервные шаблоны для каждого месяца
- **Ручное управление** - Полный контроль через админ-панель
- **Автоматизация** - Ежемесячное обновление 25 числа

### Расширенная админ-панель
- **Управление календарем** - Создание, редактирование, AI-генерация
- **Статистика** - Детальная аналитика пользователей и активности
- **Рассылки** - Массовые уведомления с фильтрацией по подпискам
- **Мониторинг** - Отслеживание состояния системы

## 🔧 Конфигурация

### Основные переменные окружения

```env
# Telegram Bot
BOT_TOKEN=your_telegram_bot_token_here

# Database
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://host:port/0

# AI
OPENAI_API_KEY=your_openai_api_key_here

# Admin Panel
ADMIN_SECRET_KEY=your_secret_key_here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_password_here

# Settings
NEW_WORKS_MONTHS=3
DEBUG=False
```

## 📊 Статистика проекта

- **Строк кода:** ~15,000
- **Файлов:** 50+
- **Модулей:** 25+
- **Тестов:** 100% покрытие новых функций
- **Документация:** Исчерпывающая

## 🤝 Вклад в проект

Мы приветствуем вклад в развитие проекта! Пожалуйста, ознакомьтесь с нашими рекомендациями:

1. **Fork** репозиторий
2. **Создайте** ветку для новой функции (`git checkout -b feature/AmazingFeature`)
3. **Commit** изменения (`git commit -m 'Add some AmazingFeature'`)
4. **Push** в ветку (`git push origin feature/AmazingFeature`)
5. **Откройте** Pull Request

### Стандарты кода

- Следуйте PEP 8
- Используйте type hints
- Покрывайте код тестами
- Документируйте новые функции

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 👥 Авторы

- **TwinsMinsk** - *Основная разработка* - [GitHub](https://github.com/TwinsMinsk)

## 🙏 Благодарности

- Команде aiogram за отличную библиотеку
- OpenAI за мощные AI модели
- Railway за простоту развертывания
- Сообществу Python за поддержку

## 📞 Поддержка

Если у вас есть вопросы или проблемы:

- 📧 **Email:** support@iqstocker.com
- 💬 **Telegram:** [@iqstocker_support](https://t.me/iqstocker_support)
- 🐛 **Issues:** [GitHub Issues](https://github.com/TwinsMinsk/iqstocker-cursor/issues)
- 📖 **Wiki:** [GitHub Wiki](https://github.com/TwinsMinsk/iqstocker-cursor/wiki)

---

<div align="center">

**⭐ Если проект вам понравился, поставьте звезду! ⭐**

[![GitHub stars](https://img.shields.io/github/stars/TwinsMinsk/iqstocker-cursor.svg?style=social&label=Star)](https://github.com/TwinsMinsk/iqstocker-cursor)
[![GitHub forks](https://img.shields.io/github/forks/TwinsMinsk/iqstocker-cursor.svg?style=social&label=Fork)](https://github.com/TwinsMinsk/iqstocker-cursor)

</div>
