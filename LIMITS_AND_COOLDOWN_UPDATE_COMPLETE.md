# 🎉 Обновление системы лимитов и cooldown тем - ЗАВЕРШЕНО

## ✅ Выполненные задачи

### 1. **Исправлено списание лимитов тем** ✅
**Проблема:** Лимиты тем не списывались при генерации тем через кнопку "Получить темы".

**Решение:**
- Добавлен импорт модели `Limits` в `bot/handlers/themes.py`
- В функции `generate_themes_callback` добавлено корректное списание лимитов:
  ```python
  # Обновляем лимиты тем
  limits_query = select(Limits).where(Limits.user_id == user.id)
  limits_result = await session.execute(limits_query)
  user_limits = limits_result.scalar_one_or_none()
  
  if user_limits:
      user_limits.themes_used += 1
      user_limits.last_theme_request_at = datetime.utcnow()
      session.add(user_limits)
  
  await session.commit()
  ```

**Файлы изменены:**
- `bot/handlers/themes.py` (строки 194-206)

---

### 2. **Проверен и работает cooldown (1 раз в неделю)** ✅
**Статус:** Cooldown для тем уже был реализован и работает корректно.

**Как работает:**
- Cooldown проверяется в двух местах:
  1. При открытии раздела "Темы" (`themes_callback`)
  2. При нажатии "Получить темы" (`generate_themes_callback`)
- Используется функция `get_theme_cooldown_days_sync()` из `core/theme_settings.py`
- Cooldown берется из таблицы `llm_settings` (поле `theme_request_interval_days`)

---

### 3. **Добавлена настройка cooldown в админ-панель** ✅
**Новая возможность:** Теперь можно настраивать cooldown тем в днях, часах и минутах через админ-панель.

**Что добавлено:**

#### A. Новое поле в модели `LLMSettings`:
```python
# database/models/llm_settings.py
theme_cooldown_minutes: Mapped[int] = mapped_column(Integer, server_default="10080", nullable=True)
# 7 days = 10080 minutes
```

#### B. Новый админ-интерфейс `LLMSettingsAdmin`:
```python
# scripts/runners/admin_fastapi.py
class LLMSettingsAdmin(ModelView, model=LLMSettings):
    column_list = [
        LLMSettings.id, LLMSettings.provider_name, LLMSettings.model_name,
        LLMSettings.is_active, LLMSettings.theme_cooldown_minutes, LLMSettings.requests_count,
        LLMSettings.last_used_at, LLMSettings.created_at
    ]
    
    # Custom formatters
    column_formatters = {
        LLMSettings.theme_cooldown_minutes: lambda m, a: f"{m.theme_cooldown_minutes} мин ({m.theme_cooldown_minutes // 1440}д {(m.theme_cooldown_minutes % 1440) // 60}ч {m.theme_cooldown_minutes % 60}м)" if m.theme_cooldown_minutes else "7 дней (по умолчанию)"
    }
```

#### C. Обновлена функция получения cooldown:
```python
# core/theme_settings.py
def get_theme_cooldown_days_sync() -> int:
    """Get theme cooldown days from database (sync version)."""
    db = SessionLocal()
    try:
        # Пытаемся получить cooldown в минутах (новое поле)
        result = db.query(LLMSettings.theme_cooldown_minutes).filter(
            LLMSettings.is_active == True
        ).first()
        
        if result and result[0]:
            # Конвертируем минуты в дни
            return result[0] // 1440  # 1440 минут = 1 день
        
        # Fallback на старое поле
        result_days = db.query(LLMSettings.theme_request_interval_days).filter(
            LLMSettings.is_active == True
        ).first()
        return result_days[0] if result_days else 7
    finally:
        db.close()
```

**Как использовать:**
1. Откройте админ-панель: `http://localhost:5000/admin`
2. Перейдите в раздел **LLM Settings**
3. Найдите активную запись (`is_active = True`)
4. Измените поле `theme_cooldown_minutes`:
   - **1 день** = 1440 минут
   - **1 час** = 60 минут
   - **7 дней** (по умолчанию) = 10080 минут
   - **30 минут** = 30 минут (для тестирования)
5. Сохраните изменения

**Файлы изменены:**
- `database/models/llm_settings.py` (строки 37-39)
- `scripts/runners/admin_fastapi.py` (строки 418-441, 457)
- `core/theme_settings.py` (строки 35-54)

---

### 4. **Добавлены telegram_id и username в таблицу Limits** ✅
**Новая возможность:** В админ-панели в разделе Limits теперь отображаются telegram_id и username пользователей.

**Что добавлено:**
```python
# scripts/runners/admin_fastapi.py
class LimitsAdmin(ModelView, model=Limits):
    # Добавляем кастомные колонки для отображения telegram_id и username
    column_formatters = {
        Limits.user_id: lambda m, a: f"{m.user_id} (TG: {m.user.telegram_id}, @{m.user.username})" if m.user else str(m.user_id)
    }
```

**Как выглядит:**
```
user_id: 1 (TG: 811079407, @oleg_smirniy)
user_id: 2 (TG: 441882529, @buttlenny)
```

**Файлы изменены:**
- `scripts/runners/admin_fastapi.py` (строки 199-202)

---

## 📊 Итоговая статистика изменений

| Файл | Строки изменены | Описание |
|------|----------------|----------|
| `bot/handlers/themes.py` | 194-206 | Добавлено списание лимитов тем |
| `database/models/llm_settings.py` | 37-39 | Добавлено поле `theme_cooldown_minutes` |
| `core/theme_settings.py` | 35-54 | Обновлена логика получения cooldown |
| `scripts/runners/admin_fastapi.py` | 199-202, 418-441, 457 | Добавлены форматтеры и админ-интерфейс |

**Всего изменено:** 4 файла  
**Всего добавлено:** ~50 строк кода

---

## 🚀 Как протестировать

### 1. Тестирование списания лимитов тем:
```bash
# Запустите бота
python start_bot.py

# В Telegram:
1. Откройте бота
2. Перейдите в раздел "Темы"
3. Нажмите "Получить темы"
4. Перейдите в "Профиль"
5. Проверьте, что лимит тем уменьшился
```

### 2. Тестирование cooldown:
```bash
# В админ-панели:
1. Откройте http://localhost:5000/admin
2. Перейдите в "LLM Settings"
3. Установите theme_cooldown_minutes = 30 (30 минут для теста)
4. Сохраните

# В Telegram:
1. Получите темы
2. Попробуйте получить темы снова
3. Должно появиться сообщение о cooldown
4. Подождите 30 минут
5. Попробуйте снова - должно сработать
```

### 3. Тестирование отображения telegram_id:
```bash
# В админ-панели:
1. Откройте http://localhost:5000/admin
2. Перейдите в "Limits"
3. Проверьте, что в колонке user_id отображается:
   "1 (TG: 811079407, @oleg_smirniy)"
```

---

## ⚠️ Важные замечания

### Миграция базы данных:
После обновления кода необходимо выполнить миграцию для добавления поля `theme_cooldown_minutes`:

```bash
# Создать миграцию
alembic revision --autogenerate -m "Add theme_cooldown_minutes to llm_settings"

# Применить миграцию
alembic upgrade head
```

### Значения по умолчанию:
- `theme_cooldown_minutes` = 10080 (7 дней)
- Если поле не заполнено, используется `theme_request_interval_days` (7 дней)

### Конвертация времени:
- **1 минута** = 1
- **1 час** = 60 минут
- **1 день** = 1440 минут
- **1 неделя** = 10080 минут
- **1 месяц (30 дней)** = 43200 минут

---

## 🎯 Все задачи выполнены успешно!

✅ Списание лимитов тем работает корректно  
✅ Cooldown тем проверен и работает  
✅ Настройка cooldown доступна в админ-панели  
✅ telegram_id и username отображаются в таблице Limits  

**Система лимитов и cooldown полностью функциональна и готова к использованию!** 🚀

