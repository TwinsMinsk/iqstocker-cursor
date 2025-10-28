# Исправление лимитов тем

## Дата: 26 октября 2025

## Проблемы и решения

### 1. Themes Limit = 5 вместо 4

**Проблема:**
- В админке отображалось `themes_total = 5` вместо требуемых 4
- Настройки в `config/settings.py` были неправильными

**Решение:**
✅ Обновлены настройки в `config/settings.py`:
- `free_themes_limit`: 1 → **4**
- `pro_themes_limit`: 5 → **4**
- `ultra_themes_limit`: 10 → **4**
- `test_pro_themes_limit`: остался **4** ✓

✅ Обновлены существующие записи в БД:
```sql
UPDATE limits SET themes_total = 4 WHERE themes_total = 5
```

### 2. Ошибка при создании Limits через админку

**Проблема:**
```
NOT NULL constraint failed: limits.user_id
```
Поле `user_id` было обязательным, но не заполнялось при создании через форму.

**Решение:**
✅ Добавлены `form_args` в `LimitsAdmin` с:
- Описаниями для всех полей
- Значениями по умолчанию:
  - `analytics_total`: 0
  - `analytics_used`: 0
  - `themes_total`: **4**
  - `themes_used`: 0
  - `theme_cooldown_days`: 7
- Подсказкой для `user_id`: "ID пользователя (обязательное поле)"

## Результат

### Лимиты тем для всех тарифов: 4 генерации в месяц

| Тариф | Analytics Limit | Themes Limit | Cooldown |
|-------|----------------|--------------|----------|
| FREE | 0 | **4** | 7 дней |
| TEST_PRO | 1 | **4** | 7 дней |
| PRO | 1 | **4** | 7 дней |
| ULTRA | 2 | **4** | 7 дней |

### Админ-панель

✅ **Создание Limits работает:**
- Поле User ID обязательное с подсказкой
- Все поля имеют значения по умолчанию
- themes_total = 4 по умолчанию

✅ **Редактирование Limits работает:**
- Все поля доступны для изменения
- Отображение в формате "X из Y"
- Cooldown настраивается индивидуально

✅ **Отображение:**
- "1 из 4", "2 из 4", "3 из 4", "4 из 4"
- "7 дней (1 недель)" для cooldown

## Файлы изменены

1. **config/settings.py**
   - Обновлены все `*_themes_limit` на значение 4

2. **scripts/runners/admin_fastapi.py**
   - Добавлены `form_args` для LimitsAdmin
   - Установлены значения по умолчанию для всех полей

3. **database/models/limits.py** (ранее)
   - Добавлено поле `theme_cooldown_days`
   - Изменено значение по умолчанию `themes_total` с 0 на 4

4. **SQLite база данных**
   - Обновлены существующие записи: themes_total = 4

## Проверка

```powershell
# Запустить админ-панель
.\venv\Scripts\python.exe scripts\runners\admin_fastapi.py

# Перейти на http://localhost:5000/admin/limits/list
# Проверить:
# - Все записи имеют themes_total = 4 или "X из 4"
# - Создание новых Limits работает
# - Редактирование работает
```

✅ **Все исправлено и работает!**

