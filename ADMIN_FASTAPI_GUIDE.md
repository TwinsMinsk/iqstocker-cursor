# 🎛️ FastAPI Admin Panel Guide

## 📋 Обзор

Новая админ-панель IQStocker Bot построена на **FastAPI** с использованием **SQLAdmin** для создания современного и безопасного интерфейса управления.

## ✨ Особенности

### 🔐 Безопасность
- **Аутентификация:** Защищенный вход с проверкой логина/пароля
- **Сессии:** Безопасные сессионные cookie с секретным ключом
- **Авторизация:** Контроль доступа к админ-функциям

### 🎨 Современный UI
- **Responsive Design:** Адаптивный дизайн для всех устройств
- **Material Design:** Современный интерфейс
- **Fast Loading:** Быстрая загрузка и отзывчивость

### 📊 Управление данными
- **CRUD операции:** Создание, чтение, обновление, удаление
- **Фильтрация:** Поиск и фильтрация данных
- **Сортировка:** Сортировка по любым полям
- **Экспорт:** Экспорт данных в различных форматах

## 🚀 Запуск

### Локальный запуск
```bash
# Активируйте виртуальное окружение
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Запустите админ-панель
python run_admin_fastapi.py
```

### Доступ к панели
- **Админ-панель:** http://localhost:5000/admin
- **API документация:** http://localhost:5000/docs
- **Health check:** http://localhost:5000/health

## 🔑 Аутентификация

### Данные для входа
- **Логин:** `admin` (или значение из `ADMIN_USERNAME`)
- **Пароль:** `admin123` (или значение из `ADMIN_PASSWORD`)

### Настройка через переменные окружения
```env
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_secure_password
ADMIN_SECRET_KEY=your_secret_key_for_sessions
```

## 📊 Управляемые сущности

### 👥 Пользователи (Users)
- **Просмотр:** Список всех пользователей с фильтрацией
- **Поиск:** По username, first_name
- **Сортировка:** По дате создания, подписке
- **Ограничения:** Создание и удаление отключены

### 💳 Подписки (Subscriptions)
- **Управление:** Полный CRUD для подписок
- **Фильтрация:** По типу подписки, статусу
- **Сортировка:** По датам начала/окончания

### 📈 Лимиты (Limits)
- **Настройка:** Управление лимитами пользователей
- **Мониторинг:** Отслеживание использования
- **Корректировка:** Ручная корректировка лимитов

### 📊 Аналитика (CSV Analysis)
- **Мониторинг:** Статус обработки CSV файлов
- **История:** Просмотр всех анализов
- **Управление:** Удаление старых записей

### 📋 Отчеты (Analytics Reports)
- **Просмотр:** Детальные отчеты по аналитике
- **Фильтрация:** По периоду, пользователю
- **Экспорт:** Выгрузка отчетов

### 🎯 Темы (Themes)
- **Топ темы:** Управление популярными темами
- **Запросы:** Обработка запросов тем от пользователей
- **Глобальные темы:** Управление общими темами

### 🎥 Видеоуроки (Video Lessons)
- **Контент:** Управление видеоуроками
- **Доступ:** Настройка ограничений по подпискам
- **Активация:** Включение/отключение уроков

### 📅 Календарь (Calendar)
- **Планирование:** Управление календарными записями
- **AI генерация:** Отслеживание источников создания
- **Редактирование:** Ручное редактирование календаря

### 📢 Рассылки (Broadcasts)
- **Создание:** Новые рассылки
- **Статистика:** Отслеживание отправленных сообщений
- **Управление:** Редактирование и удаление

## 🛠 Технические детали

### Архитектура
```
FastAPI App
├── SQLAdmin (Admin Interface)
├── Authentication Backend
├── Database Models
└── Settings Configuration
```

### Зависимости
- **FastAPI:** Веб-фреймворк
- **SQLAdmin:** Админ-интерфейс
- **SQLAlchemy:** ORM для работы с БД
- **Uvicorn:** ASGI сервер

### Конфигурация
```python
# Настройки аутентификации
authentication_backend = AdminAuth(secret_key=settings.admin.secret_key)

# Подключение админки
admin = Admin(
    app=app,
    engine=engine,
    authentication_backend=authentication_backend,
    title="IQStocker Admin",
    base_url="/admin"
)
```

## 🔧 Настройка

### Переменные окружения
```env
# Админ-панель
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure_password_here
ADMIN_SECRET_KEY=very_long_secret_key_for_sessions

# База данных
DATABASE_URL=postgresql://user:password@host:port/database

# Приложение
DEBUG=False
HOST=0.0.0.0
PORT=5000
```

### Кастомизация
```python
# Добавление новых полей в админку
class CustomUserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.email]
    column_searchable_list = [User.username, User.email]
    can_create = True
    can_edit = True
    can_delete = False

admin.add_view(CustomUserAdmin)
```

## 🚀 Развертывание

### Railway
```bash
# Добавьте в Railway переменные окружения
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_secure_password
ADMIN_SECRET_KEY=your_secret_key

# Railway автоматически запустит админ-панель
```

### Docker
```dockerfile
# В Dockerfile добавьте
CMD ["python", "run_admin_fastapi.py"]
```

### Локальный продакшен
```bash
# Установите зависимости
pip install -r requirements.txt

# Запустите с uvicorn
uvicorn admin_fastapi:app --host 0.0.0.0 --port 5000
```

## 📊 Мониторинг

### Health Check
```bash
curl http://localhost:5000/health
```

Ответ:
```json
{
  "status": "healthy",
  "service": "iqstocker-admin",
  "version": "1.0.0"
}
```

### Логи
```bash
# Просмотр логов
tail -f logs/admin.log

# Мониторинг в реальном времени
uvicorn admin_fastapi:app --reload --log-level debug
```

## 🔒 Безопасность

### Рекомендации
1. **Измените пароли по умолчанию**
2. **Используйте сложные секретные ключи**
3. **Ограничьте доступ по IP**
4. **Регулярно обновляйте зависимости**
5. **Мониторьте логи на подозрительную активность**

### Настройка HTTPS
```python
# Для продакшена используйте HTTPS
uvicorn.run(
    app,
    host="0.0.0.0",
    port=5000,
    ssl_keyfile="path/to/key.pem",
    ssl_certfile="path/to/cert.pem"
)
```

## 🆘 Устранение неполадок

### Проблемы с аутентификацией
```bash
# Проверьте переменные окружения
echo $ADMIN_USERNAME
echo $ADMIN_PASSWORD
echo $ADMIN_SECRET_KEY
```

### Проблемы с БД
```bash
# Проверьте подключение
python -c "from config.database import engine; print('DB OK' if engine else 'DB Error')"
```

### Проблемы с портами
```bash
# Проверьте доступность порта
netstat -an | grep :5000
```

## 📞 Поддержка

- **GitHub Issues:** [Создать issue](https://github.com/TwinsMinsk/iqstocker-cursor/issues)
- **Документация:** [FastAPI Docs](https://fastapi.tiangolo.com/)
- **SQLAdmin:** [SQLAdmin Docs](https://sqladmin.aminalaee.dev/)

---

**🎉 Новая админ-панель готова к использованию!**
