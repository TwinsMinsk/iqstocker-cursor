# Инструкция по настройке Supabase и созданию таблицы tariff_limits

## Шаг 1: Выполнение SQL через Supabase Dashboard (быстрый способ)

1. Откройте [Supabase Dashboard](https://supabase.com/dashboard)
2. Выберите ваш проект
3. Перейдите в раздел **SQL Editor** (в левом меню)
4. Создайте новый запрос (New Query)
5. Скопируйте и вставьте SQL из файла `scripts/data/tariff_limits_supabase.sql`
6. Нажмите **Run** или `Ctrl+Enter` для выполнения
7. Проверьте результат - должно появиться 4 записи

✅ **Таблица создана и данные инициализированы!**

---

## Шаг 2: Настройка Supabase CLI (для будущего использования)

### Вариант A: Использование через npx (без установки)

**Рекомендуется!** Не требует установки, всегда использует последнюю версию:

```powershell
# Проверка версии
npx supabase --version

# Вход в Supabase
npx supabase login

# Связывание проекта
npx supabase link --project-ref ваш-project-ref

# Выполнение SQL
npx supabase db execute -f scripts/data/tariff_limits_supabase.sql
```

### Вариант B: Установка через Scoop (Windows)

1. **Установите Scoop** (если еще не установлен):
   ```powershell
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   irm get.scoop.sh | iex
   ```

2. **Установите Supabase CLI:**
   ```powershell
   scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
   scoop install supabase
   ```

3. **Проверьте установку:**
   ```powershell
   supabase --version
   ```

### Вариант C: Скачать бинарный файл напрямую

1. Перейдите на [GitHub Releases Supabase CLI](https://github.com/supabase/cli/releases)
2. Скачайте `supabase_windows_amd64.zip` для Windows
3. Распакуйте и добавьте путь к исполняемому файлу в PATH

### Вариант D: Использовать через Docker (если установлен Docker)

```powershell
docker run --rm supabase/cli:latest --version
```

### Авторизация в Supabase CLI

1. **Войдите в Supabase:**
   ```powershell
   supabase login
   ```

2. **Сгенерируйте токен доступа:**
   - Откройте [Supabase Dashboard → Account → Access Tokens](https://supabase.com/dashboard/account/tokens)
   - Нажмите "Generate new token"
   - Скопируйте токен и вставьте в командную строку

3. **Свяжите проект с локальным CLI:**
   ```powershell
   supabase link --project-ref ваш-project-ref
   ```
   Project ref можно найти в Dashboard → Settings → General → Reference ID

### Использование CLI для выполнения SQL

**Через npx (рекомендуется):**
```powershell
npx supabase db execute -f scripts/data/tariff_limits_supabase.sql
```

**Или через установленный CLI:**
```powershell
supabase db execute -f scripts/data/tariff_limits_supabase.sql
```

**Или через Python скрипт:**
```powershell
python scripts/execute_sql_via_cli.py
```

---

## Шаг 3: Настройка MCP Supabase (опционально)

MCP Supabase уже настроен в вашем `mcp.json` файле. Для использования:

1. **Получите Project Reference ID:**
   - Dashboard → Settings → General → Reference ID
   - Пример: `tqydndcvjqigxvjmaacj`

2. **Используйте MCP через Cursor:**
   - MCP Supabase доступен через инструменты Cursor
   - Можно выполнять SQL запросы и управлять базой данных

---

## Проверка результата

После выполнения SQL в Dashboard проверьте:

```sql
SELECT * FROM tariff_limits ORDER BY subscription_type;
```

Должны быть 4 записи:
- FREE: Analytics=0, Themes=4
- TEST_PRO: Analytics=1, Themes=2, Duration=14 дней
- PRO: Analytics=1, Themes=4
- ULTRA: Analytics=2, Themes=4

---

## Полезные команды Supabase CLI

**Через npx (если не установлен):**
```powershell
# Просмотр схемы базы данных
npx supabase db dump --schema public

# Выполнение SQL файла
npx supabase db execute -f путь/к/файлу.sql

# Просмотр логов
npx supabase db logs

# Создание миграции
npx supabase migration new название_миграции
```

**Через установленный CLI:**
```powershell
# Просмотр схемы базы данных
supabase db dump --schema public

# Выполнение SQL файла
supabase db execute -f путь/к/файлу.sql

# Просмотр логов
supabase db logs

# Создание миграции
supabase migration new название_миграции
```

---

## Решение проблем с подключением

Если у вас проблемы с DNS (`getaddrinfo failed`):

1. **Проверьте интернет-соединение**
2. **Попробуйте использовать VPN** (если есть ограничения)
3. **Используйте Supabase Dashboard** для выполнения SQL (наиболее надежный способ)
4. **Используйте Supabase CLI** после установки (может работать лучше, чем прямое подключение)

---

## Следующие шаги

После создания таблицы:
1. ✅ Таблица `tariff_limits` создана
2. ✅ Данные инициализированы
3. ✅ Можно использовать админ-панель для управления тарифами
4. ✅ Бот будет использовать данные из базы вместо `settings.py`

