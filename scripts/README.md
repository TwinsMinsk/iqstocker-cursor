# 🔧 Скрипты и утилиты

Этот раздел содержит все служебные скрипты проекта IQStocker, организованные по назначению.

## Структура

```
scripts/
├── setup/                  # Скрипты настройки
│   ├── setup_admin_user.py
│   ├── setup_bot_token.py
│   ├── setup_demo.py
│   └── setup_railway_env.py
├── database/               # Скрипты работы с БД
│   ├── init_*.py           # Инициализация БД
│   ├── fix_*.py            # Исправления БД
│   ├── check_*.py          # Проверки БД
│   └── recalculate_*.py    # Пересчеты данных
├── data/                   # Скрипты работы с данными
│   ├── add_test_*.py       # Добавление тестовых данных
│   ├── create_*.py         # Создание данных
│   └── iqstocker_process_csv.py
├── deployment/             # Скрипты деплоя
│   ├── railway_*.py        # Railway деплой
│   └── start_worker.py     # Запуск воркеров
└── runners/                # Скрипты запуска
    ├── run_*.py            # Запуск компонентов
    └── admin_fastapi.py    # FastAPI админка
```

## Использование

### Настройка проекта
```bash
python scripts/setup/setup_admin_user.py
python scripts/setup/setup_bot_token.py
python scripts/setup/setup_demo.py
```

### Работа с базой данных
```bash
python scripts/database/init_db.py
python scripts/database/fix_database.py
python scripts/database/check_database_content.py
```

### Обработка данных
```bash
python scripts/data/create_test_csv.py
python scripts/data/iqstocker_process_csv.py
```

### Запуск компонентов
```bash
python scripts/runners/run_bot.py
python scripts/runners/run_admin_fastapi.py
python scripts/runners/run_all_tests.py
```

### Деплой
```bash
python scripts/deployment/railway_startup.py
python scripts/deployment/start_worker.py
```

## Примечания

- Все скрипты автоматически добавляют корневую папку проекта в `sys.path`
- Скрипты можно запускать из любой папки проекта
- Для production используйте соответствующие скрипты деплоя
