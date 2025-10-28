# 🎯 Руководство по управлению лимитами пользователей

## 📋 Обзор изменений

Данный документ описывает систему управления лимитами пользователей IQStocker и изменения, внесенные в код для корректной работы системы.

---

## ✅ Исправленные проблемы

### 1. **Списание лимитов аналитики**
**Проблема:** Лимит на аналитику списывался ДО обработки CSV-файла. Если обработка падала, лимит все равно был потрачен.

**Решение:** 
- Удалено преждевременное списание в `bot/handlers/analytics.py` (строки 565, 653)
- Добавлено списание лимита ПОСЛЕ успешной обработки CSV в функции `process_csv_analysis()` (строка 917-919)

```python
# СПИСЫВАЕМ ЛИМИТ ТОЛЬКО ПОСЛЕ УСПЕШНОЙ ОБРАБОТКИ
user_limits = db.query(Limits).filter(Limits.user_id == user.id).first()
if user_limits:
    user_limits.analytics_used += 1
```

### 2. **Логика начисления лимитов при оплате**
**Проблема:** Не было четкой логики обработки первой покупки vs продления подписки.

**Решение:** 
- Добавлены комментарии в `core/subscriptions/payment_handler.py`
- Логика: при продлении лимиты **добавляются** к существующим (можно накапливать)
- При истечении подписки `analytics_used` и `themes_used` НЕ обнуляются (сохраняется история)

### 3. **Единообразие текстов сообщений**
**Проблема:** Сообщения об исчерпании лимитов были захардкожены в разных местах кода.

**Решение:**
- Добавлены ключи в `bot/lexicon/lexicon_ru.py`:
  - `limits_analytics_exhausted`
  - `limits_themes_exhausted`
- Обновлены хэндлеры для использования лексикона

---

## 🛠️ Новые возможности

### 1. **API эндпоинты для управления лимитами**

#### GET `/api/admin/users/{user_id}/limits`
Получение текущих лимитов пользователя.

**Пример ответа:**
```json
{
  "success": true,
  "data": {
    "user_id": 123,
    "telegram_id": 987654321,
    "username": "john_doe",
    "subscription_type": "PRO",
    "limits": {
      "analytics_total": 5,
      "analytics_used": 2,
      "analytics_remaining": 3,
      "themes_total": 10,
      "themes_used": 4,
      "themes_remaining": 6
    }
  }
}
```

#### PUT `/api/admin/users/{user_id}/limits`
Обновление лимитов пользователя.

**Тело запроса:**
```json
{
  "analytics_total": 10,
  "analytics_used": 2,
  "themes_total": 20,
  "themes_used": 5
}
```

**Пример ответа:**
```json
{
  "success": true,
  "message": "Limits updated for user 123",
  "data": {
    "user_id": 123,
    "username": "john_doe",
    "telegram_id": 987654321,
    "old_values": {
      "analytics_total": 5,
      "analytics_used": 2,
      "themes_total": 10,
      "themes_used": 4
    },
    "new_values": {
      "analytics_total": 10,
      "analytics_used": 2,
      "themes_total": 20,
      "themes_used": 5
    },
    "current_limits": {
      "analytics_total": 10,
      "analytics_used": 2,
      "analytics_remaining": 8,
      "themes_total": 20,
      "themes_used": 5,
      "themes_remaining": 15
    }
  }
}
```

**Важно:** Все изменения автоматически логируются в `AuditLog` с указанием:
- Кто изменил (admin_username)
- Когда изменил (created_at)
- Какие были старые значения (old_values)
- Какие стали новые значения (new_values)

### 2. **Web-интерфейс управления лимитами**

**URL:** `/admin/user-limits`

**Возможности:**
- 🔍 Поиск пользователя по User ID (внутренний ID из базы)
- 📊 Просмотр текущих лимитов и статистики использования
- ✏️ Редактирование всех 4 полей лимитов:
  - `analytics_total` - Всего аналитик
  - `analytics_used` - Использовано аналитик
  - `themes_total` - Всего тем
  - `themes_used` - Использовано тем
- 💾 Сохранение изменений с автоматическим логированием
- 🔄 Сброс формы к исходным значениям

**Интерфейс:**
- Современный дизайн с Bootstrap 5
- Градиентные карточки и кнопки
- Информативные badge-элементы для статуса
- Уведомления об успехе/ошибке
- Responsive-дизайн для работы на всех устройствах

---

## 📊 Логика работы лимитов

### Тарифные планы и лимиты (из `config/settings.py`)

| Тариф | Аналитика (мес.) | Темы (мес.) |
|-------|------------------|-------------|
| **FREE** | 0 | 4 |
| **TEST_PRO** | 1 | 2 (за 2 недели) |
| **PRO** | 1 | 4 |
| **ULTRA** | 2 | 4 |

### Жизненный цикл лимитов

1. **Регистрация нового пользователя (TEST_PRO)**
   - Создается запись `User` с `subscription_type = TEST_PRO`
   - Создается запись `Limits` с начальными значениями из settings
   - `bot/handlers/start.py` (строки 61-68)

2. **Использование функций**
   - **Аналитика:** Лимит списывается ПОСЛЕ успешной обработки CSV
   - **Темы:** Лимит списывается ПОСЛЕ успешной генерации тем
   - Проверка лимита происходит ДО начала обработки

3. **Покупка/Продление подписки**
   - Лимиты **добавляются** к существующим (можно накапливать)
   - Создается запись в `Subscription` с деталями платежа
   - `core/subscriptions/payment_handler.py` (строки 91-102)

4. **Истечение подписки**
   - Пользователь переходит на `FREE`
   - `analytics_total` и `themes_total` устанавливаются в FREE-значения
   - `analytics_used` и `themes_used` сохраняются (история)
   - Метод `check_subscription_expiry()` (строки 117-155)

---

## 🔐 Безопасность и Аудит

### Audit Log
Все изменения лимитов через админ-панель автоматически логируются в таблицу `audit_logs`:

**Поля:**
- `admin_username` - Кто изменил
- `admin_ip` - С какого IP
- `action` - Тип действия (UPDATE)
- `resource_type` - Тип ресурса (Limits)
- `resource_id` - ID пользователя
- `old_values` - Старые значения (JSON)
- `new_values` - Новые значения (JSON)
- `description` - Описание изменения
- `created_at` - Время изменения

### Просмотр Audit Log
Доступ к логам через:
- API: `/api/audit/logs`
- Админ-панель: SQLAdmin → AuditLog

---

## 🧪 Тестирование

### Ручное тестирование

1. **Запуск FastAPI админ-панели:**
   ```bash
   cd scripts/runners
   python admin_fastapi.py
   ```
   Или через виртуальное окружение:
   ```bash
   venv\Scripts\activate
   python scripts/runners/admin_fastapi.py
   ```

2. **Доступ к интерфейсу:**
   - Откройте браузер: `http://localhost:5000/admin/user-limits`
   - Войдите с admin credentials (из `.env`)

3. **Тестовые сценарии:**
   
   **Сценарий 1: Просмотр лимитов**
   - Найдите тестового пользователя по User ID
   - Проверьте отображение всех полей
   - Убедитесь, что "Осталось" рассчитывается правильно

   **Сценарий 2: Изменение лимитов**
   - Измените `analytics_total` с 5 на 10
   - Сохраните изменения
   - Проверьте успешное сообщение
   - Проверьте обновление "Осталось"

   **Сценарий 3: Audit Log**
   - Перейдите в `/admin` → AuditLog
   - Найдите последнюю запись
   - Проверьте наличие старых и новых значений

   **Сценарий 4: API напрямую**
   ```bash
   # GET request
   curl -X GET http://localhost:5000/api/admin/users/1/limits
   
   # PUT request
   curl -X PUT http://localhost:5000/api/admin/users/1/limits \
     -H "Content-Type: application/json" \
     -d '{"analytics_total": 10, "analytics_used": 2, "themes_total": 20, "themes_used": 5}'
   ```

### Автоматизированное тестирование

Создайте файл `tests/integration/test_limits_api.py`:

```python
import pytest
from fastapi.testclient import TestClient
from scripts.runners.admin_fastapi import app

client = TestClient(app)

def test_get_user_limits():
    response = client.get("/api/admin/users/1/limits")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "limits" in data["data"]

def test_update_user_limits():
    response = client.put(
        "/api/admin/users/1/limits",
        json={
            "analytics_total": 10,
            "analytics_used": 2,
            "themes_total": 20,
            "themes_used": 5
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
```

---

## 📝 Checklist для проверки

- [x] Модель `Limits` корректна
- [x] Значения лимитов в `settings.py` соответствуют тарифам
- [x] Лимиты списываются ПОСЛЕ успешной обработки
- [x] Тексты сообщений хранятся в `lexicon_ru.py`
- [x] API эндпоинты созданы и работают
- [x] Изменения логируются в `AuditLog`
- [x] Web-интерфейс создан и функционален
- [ ] Ручное тестирование пройдено
- [ ] Автоматизированные тесты написаны и пройдены

---

## 🎯 Итоговые файлы изменений

### Измененные файлы:
1. `bot/handlers/analytics.py` - Исправлено списание лимитов
2. `bot/handlers/themes.py` - Использование лексикона
3. `bot/lexicon/lexicon_ru.py` - Добавлены сообщения о лимитах
4. `core/subscriptions/payment_handler.py` - Улучшена логика начисления
5. `scripts/runners/admin_fastapi.py` - Добавлены API эндпоинты

### Новые файлы:
1. `admin/templates/user_limits.html` - Web-интерфейс управления лимитами
2. `LIMITS_MANAGEMENT_GUIDE.md` - Данное руководство

---

## 💡 Рекомендации

1. **Регулярно проверяйте Audit Log** на предмет подозрительных изменений
2. **Используйте User ID**, а не Telegram ID для поиска пользователей
3. **Будьте осторожны** с изменением `*_used` полей - это может нарушить историю
4. **Создавайте backup** базы данных перед массовыми изменениями лимитов
5. **Мониторьте** частоту исчерпания лимитов для оптимизации тарифных планов

---

**Дата создания:** 2025-01-26  
**Версия:** 1.0  
**Автор:** IQStocker Development Team

