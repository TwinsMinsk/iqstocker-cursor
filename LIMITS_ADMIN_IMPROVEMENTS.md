# Улучшения админ-панели Limits

## Дата: 26 октября 2025

## Реализованные функции

### 1. Добавлено поле `theme_cooldown_days` в модель Limits

**Файл:** `database/models/limits.py`

- ✅ Добавлено поле `theme_cooldown_days: Mapped[int]` с значением по умолчанию 7 дней
- ✅ Изменен `themes_total` по умолчанию с 0 на 4 (4 генерации в месяц = 1 раз в неделю)
- ✅ Создана и применена миграция БД

### 2. Улучшена админ-панель Limits

**Файл:** `scripts/runners/admin_fastapi.py`

**Добавлено:**
- ✅ Колонка `theme_cooldown_days` для настройки cooldown периода
- ✅ Форматеры для отображения:
  - `themes_used`: "X из Y" (например "1 из 4")
  - `analytics_used`: "X из Y"
  - `theme_cooldown_days`: "X дней (Y недель)"
- ✅ Описания полей (`column_descriptions`) для подсказок
- ✅ Возможность редактировать cooldown через форму
- ✅ Eager loading пользователя для избежания DetachedInstanceError

**Подписи колонок:**
- "Analytics Limit" / "Analytics Used"
- "Themes Limit (per month)" / "Themes Used"
- "Theme Cooldown (days)"
- "Last Theme Request"

### 3. Обновлена логика получения cooldown

**Файл:** `core/theme_settings.py`

**Изменения:**
- ✅ `get_theme_cooldown_days(user_id)` - теперь получает cooldown из лимитов пользователя
- ✅ `get_theme_cooldown_days_sync(user_id)` - синхронная версия
- ✅ Fallback на DEFAULT_THEME_COOLDOWN_DAYS = 7 если не найдено в БД
- ✅ Добавлен импорт модели `Limits`

### 4. Обновлен обработчик тем

**Файл:** `bot/handlers/themes.py`

**Изменения:**
- ✅ Вызов `get_theme_cooldown_days_sync(user.id)` теперь передает user_id
- ✅ Cooldown теперь индивидуален для каждого пользователя

## Функциональность

### Лимиты на генерацию тем

**По умолчанию:**
- 📊 **4 генерации в месяц** (themes_total = 4)
- ⏱️ **7 дней между генерациями** (theme_cooldown_days = 7)
- 📈 **Отображение прогресса**: "1 из 4", "2 из 4" и т.д.

**Настройка в админке:**
1. Перейти в `/admin/limits/list`
2. Выбрать пользователя
3. Редактировать поля:
   - `Themes Limit (per month)` - количество генераций
   - `Theme Cooldown (days)` - минимальный период между генерациями
   - `Themes Used` - сколько использовано

### Примеры использования

**Стандартный тариф:**
- themes_total = 4
- theme_cooldown_days = 7
- Результат: 1 генерация в неделю, 4 в месяц

**Премиум тариф (пример):**
- themes_total = 8
- theme_cooldown_days = 3
- Результат: 1 генерация каждые 3 дня, 8 в месяц

**VIP тариф (пример):**
- themes_total = 30
- theme_cooldown_days = 1
- Результат: 1 генерация в день, 30 в месяц

## Миграция БД

**Файл миграции:** `database/migrations/versions/b241e3487fd2_add_theme_cooldown_days_to_limits.py`

**Изменения:**
- Добавлена колонка `theme_cooldown_days INTEGER DEFAULT 7` в таблицу `limits`
- Миграция успешно применена ✅

## Результат

✅ **Админ-панель теперь позволяет:**
1. Видеть использование лимитов в формате "X из Y"
2. Настраивать индивидуальный cooldown для каждого пользователя
3. Устанавливать количество генераций тем в месяц
4. Видеть последний запрос тем

✅ **Бот теперь:**
1. Использует индивидуальный cooldown из лимитов пользователя
2. Показывает прогресс использования лимитов
3. Поддерживает 4 генерации в месяц по умолчанию

✅ **0 ошибок линтера**

