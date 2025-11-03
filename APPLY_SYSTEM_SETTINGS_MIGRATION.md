# Инструкция по применению миграции system_settings

## Проблема
Из-за особенностей кодировки DATABASE_URL в локальной Windows-среде, миграция не может быть применена локально. Однако она будет автоматически применена при деплое на Railway, или можно применить её вручную на сервере.

## Автоматическое применение (рекомендуется)

Миграция будет автоматически применена при следующем деплое на Railway через `scripts/deployment/run_migrations.py`.

## Ручное применение на Railway

1. Подключитесь к Railway CLI:
   ```bash
   railway link
   ```

2. Запустите миграцию:
   ```bash
   railway run python scripts/deployment/run_migrations.py
   ```

3. Инициализируйте admin_ids:
   ```bash
   railway run python scripts/data/init_admin_ids.py
   ```

## Альтернативный способ: через SQL напрямую

Если нужно применить миграцию немедленно без деплоя, можно выполнить SQL команды напрямую в базе данных:

```sql
-- Создать таблицу system_settings
CREATE TABLE IF NOT EXISTS system_settings (
    key VARCHAR(100) NOT NULL PRIMARY KEY,
    value TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Создать индекс
CREATE INDEX IF NOT EXISTS ix_system_settings_key ON system_settings(key);

-- Инициализировать admin_ids
INSERT INTO system_settings (key, value, created_at, updated_at)
VALUES (
    'admin_ids',
    '[811079407, 441882529]',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
)
ON CONFLICT (key) DO NOTHING;
```

## Проверка

После применения миграции проверьте:

1. Таблица создана:
   ```sql
   SELECT * FROM system_settings WHERE key = 'admin_ids';
   ```

2. В админ-панели должны отображаться администраторы из списка admin_ids.

## Файлы миграции

- Миграция: `database/migrations/versions/b6c6fd3f6bc_add_system_settings_table.py`
- Скрипт инициализации: `scripts/data/init_admin_ids.py`

