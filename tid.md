## Technical Implementation Document (TID) — IQStocker

Этот документ — единственный источник правды для полного переиздания проекта на «чистом коде». Новый проект должен сохранить 100% функциональности, но избавиться от мусора, устаревших файлов и неиспользуемых зависимостей. Все тексты бота и кнопок должны храниться строго в одном месте: `bot/lexicon/lexicon_ru.py`.


## 1. Стек технологий

- **Python**: основной язык реализации.
- **Aiogram 3.x**: Telegram-бот (FSM, роутеры, middlewares). Используется в `bot/`.
- **FastAPI**: админ-панель (`admin_panel/`) и вебхуки/микросервисы (`api/webhook_server.py`).
- **SQLAlchemy 2.x**: ORM, модели и сессии (`database/models`, `config/database.py`).
- **Alembic**: миграции (`database/migrations`, `database/alembic.ini`).
- **PostgreSQL (Supabase) / SQLite**: БД. В проде — PostgreSQL (в т.ч. Supabase пулер), локально возможен SQLite.
- **Redis**: кеш/брокер, лимиты, Dramatiq брокер (`config/settings.py`, `workers/actors.py`).
- **Dramatiq**: фоновые задачи/актеры (`workers/actors.py`).
- **Pandas / NumPy / scikit-learn**: парсинг, расчеты, аналитика CSV (`core/analytics/*`).
- **Jinja2 + sqladmin**: UI админки, модели в админке (`admin_panel/main.py`, `admin_panel/templates`).
- **Uvicorn**: ASGI-сервер для FastAPI.

Роли технологий:
- **Aiogram** — взаимодействие с пользователем в Telegram, FSM для сбора данных, навигация.
- **FastAPI** — админ-панель (просмотр/управление данными, настройки) и вебхуки платежей.
- **SQLAlchemy/Alembic** — хранение пользователей, подписок, лимитов, CSV-анализов, отчетов, тем и системных сообщений; миграции схемы.
- **Dramatiq/Redis** — асинхронные фоновые задачи (обработка файлов, уведомления, уборка).
- **PostgreSQL** — основная БД; поддержка SQLite локально для разработки. Для хостинга может использоваться Railway PostgreSQL.


## 2. Архитектура проекта

Высокоуровневая структура (оставить и воспроизвести только нужные директории):

- `bot/` — код Telegram-бота
  - `main.py` — запуск бота, регистрация middlewares и роутеров
  - `handlers/` — обработчики команд/кнопок (admin, analytics, themes, profile, start, menu, lessons, calendar, faq, channel, payments, invite)
  - `middlewares/` — инъекция сессии БД, пользователя, лимитов (`database.py`, `subscription.py`, `limits.py`)
  - `keyboards/` — фабрики клавиатур и callback-схемы
  - `lexicon/lexicon_ru.py` — ЕДИНЫЙ источник всех текстов сообщений и кнопок
  - `states/` — FSM-состояния (например, AnalyticsStates)
  - `utils/` — вспомогательные утилиты (safe_edit и др.)

- `admin_panel/` — FastAPI админка и страницы
  - `main.py` — приложение FastAPI + sqladmin, роутеры, шаблоны, статика
  - `auth.py` — аутентификация через Telegram ID администратора
  - `views/` — страницы: `dashboard.py`, `themes.py`, `placeholders.py`
  - `templates/` — HTML-шаблоны (Jinja2)
  - `static/` — статика

- `api/` — вспомогательные сервисы (в чистой версии — только health)
  - `health.py` — FastAPI endpoint `/health` для Railway

- `core/` — доменная логика
  - `analytics/` — парсер CSV, расчеты KPI, генератор отчетов
  - `notifications/` — планировщик уведомлений (scheduler)
  - `theme_settings.py` — правила cooldown и тексты
  - `subscriptions/`, `payments/`, `utils/` — платежи, вспомогательные утилиты

- `config/` — конфигурации
  - `settings.py` — Pydantic Settings, env, флаги
  - `database.py` — синхронные/асинхронные движки SQLAlchemy, Redis клиент
  - (удалить в чистой версии: `ai.py`)

- `database/` — БД слой
  - `models/` — все ORM модели
  - `migrations/` — Alembic миграции
  - `alembic.ini` — конфиг Alembic

- `workers/actors.py` — актеры Dramatiq

Важно: все тексты UI (бот/кнопки) — ТОЛЬКО в `bot/lexicon/lexicon_ru.py`.


## 3. Модели данных (SQLAlchemy)

Подключение к базе: `config/database.py`
- Из переменных окружения берется `DATABASE_URL` (приоритет), иначе `settings.database_url`.
- Поддержка PostgreSQL (asyncpg) и SQLite (aiosqlite). Для Supabase — SSL и отключенный statement cache для pgbouncer.
- Экспортируются `engine`, `AsyncSessionLocal`, `SessionLocal`, `Base` и провайдеры сессий `get_db()`, `get_async_session()`.
- Redis клиент доступен через `get_redis()`.

Модели (все в `database/models/`). В чистой реализации оставить только используемые ботом и админкой:

- `User`
  - Поля: `id`, `telegram_id` (unique, index), `username`, `first_name`, `last_name`, `subscription_type` (Enum: FREE, PRO, ULTRA, TEST_PRO), `subscription_expires_at`, `test_pro_started_at`, `created_at`, `updated_at`, `last_activity_at`, `is_admin`.
  - Связи (cascade="all, delete-orphan"): `subscriptions` → `Subscription`, `limits` (one-to-one) → `Limits`, `csv_analyses` → `CSVAnalysis`, `theme_requests` → `ThemeRequest`, `issued_themes` → `UserIssuedTheme`.
  - Индексы: по активности/дате/типу подписки.

- (удалить в чистой версии) `Subscription` — история платежей не используется.

- `Limits`
  - Поля: `id`, `user_id` (unique FK), `analytics_total`, `analytics_used`, `themes_total`, `themes_used`, `theme_cooldown_days` (по умолчанию 7), `last_theme_request_at`, `created_at`, `updated_at`.
  - Связь: `user` → `User`.
  - Свойства: `analytics_remaining`, `themes_remaining` (max(0, total-used)).

- `CSVAnalysis`
  - Поля: `id`, `user_id` (FK), `file_path`, `month`, `year`, `portfolio_size`, `upload_limit`, `monthly_uploads`, `acceptance_rate` (Numeric), `content_type` (Enum name="contenttype" с PHOTOS/VIDEOS/MIXED), `status` (PENDING/PROCESSING/COMPLETED/FAILED), `processed_at`, `analytics_message_ids`, `created_at`.
  - Связи: `user` → `User`, `analytics_report` (one-to-one) → `AnalyticsReport`.
  - Индексы: `user_id,created_at`, `status,created_at`, `month,year`.

- `AnalyticsReport`
  - Поля: `id`, `csv_analysis_id` (FK), KPI: `total_sales`, `total_revenue` (Numeric), `avg_revenue_per_sale` (Numeric), проценты: `portfolio_sold_percent`, `new_works_sales_percent`, `acceptance_rate_calc` (Numeric), `upload_limit_usage` (Numeric), `report_text_html` (Text), `period_human_ru` (String), `created_at`.
  - Связь: `csv_analysis` → `CSVAnalysis`.

- `ThemeRequest`
  - Поля: `id`, `user_id` (FK), `theme_name` (строка с темами через переносы), `status` (PENDING/READY/ISSUED), `created_at`, `updated_at`.
  - Связь: `user` → `User`.

- (опционально удалить) `GlobalTheme`/`UserIssuedTheme` — не требуются для текущей выдачи тем пользователю.

  

- `SystemMessage`
  - Поля: `key` (PK, String), `text` — используется для управляемых из админки сообщений (например, текст cooldown).

- (удалить в чистой версии) `LLMSettings` — LLM-провайдеры не используются.

- (удалить в чистой версии, если не используются в UI) `VideoLesson`, `AssetDetails`, `AuditLog`, `BroadcastMessage`, `CalendarEntry`.

Миграции Alembic:
- Конфиг: `database/alembic.ini`.
- Каталог миграций: `database/migrations/` (держать в актуальном состоянии; Enum `contenttype` должен соответствовать значениям модели `CSVAnalysis`).
- Применение миграций: `alembic upgrade head` (при наличии корректного `DATABASE_URL`).


## 4. Пошаговое воссоздание функционала

### Часть A: Core и конфигурация

- Конфигурация `config/settings.py` (Pydantic Settings):
  - Блоки: `BotSettings` (BOT_TOKEN, WEBHOOK_URL), `DBSettings` (DATABASE_URL), `RedisSettings` (REDIS_URL), `AdminSettings` (логин/секрет), `AISettings` (ключи провайдеров), `PaymentSettings` (Boosty).
  - `AppSettings`: логирование, лимиты, пороги, новые работы id, пр.
  - Глобальный `settings = Settings()` прокидывает совместимые алиасы свойств для старого кода.

- Подключение БД `config/database.py`:
  - Выбор драйверов и async URL, SSL/pgbouncer-совместимость для Supabase, пул коннектов для PostgreSQL, `StaticPool` для SQLite.
  - Экспорт синхронной/асинхронной фабрик сессий, Redis клиента.

-- Сервисы `core`:
  - `core/analytics/advanced_csv_processor.py`: чтение/нормализация CSV (Adobe Stock), фильтрация «битых» строк, расчет метрик, генерация результата `AdvancedProcessResult` с KPI и топами; вычисления используют `KPICalculator`.
  - `core/analytics/report_generator_fixed.py`: формирование текстов отчета для бота и архивной версии; ВСЕ тексты берутся из `LEXICON_RU`.
  - `core/theme_settings.py`: извлечение интервала cooldown и текстов из БД (`SystemMessage` и/или `Limits`), sync/async варианты.
  - `core/notifications/scheduler`: планировщик задач (напоминания, рассылки) — вызывается из `bot/main.py` (должен быть инициализирован).


### Часть B: Telegram-бот (Aiogram 3.x)

Инициализация `bot/main.py`:
- Логирование, валидация лексикона через `core/utils/lexicon_validator.validate_or_raise()`.
- Создание `Bot` с ParseMode HTML, `Dispatcher(MemoryStorage)`.
- Регистрация middlewares в порядке: `DatabaseMiddleware` → `SubscriptionMiddleware` → `LimitsMiddleware`.
- Регистрация роутеров: `start`, `menu`, `profile`, `analytics`, `themes`, `lessons`, `calendar`, `faq`, `channel`, `payments`, `admin`, `invite`.
- Запуск scheduler и поллинга.

Middlewares:
- `DatabaseMiddleware`: кладет `AsyncSession` в `data["session"]` на запрос.
- `SubscriptionMiddleware`: по `telegram_id` подтягивает `User` и кладет в `data["user"]`.
- `LimitsMiddleware`: по `user.id` подтягивает `Limits` и кладет в `data["limits"]`.

Обязательная интеграция лексикона: все тексты и кнопки — ключи из `bot/lexicon/lexicon_ru.py`. Примеры ключей: `LEXICON_RU['main_menu_message']`, `LEXICON_RU['analytics_intro']`, `LEXICON_COMMANDS_RU['get_themes']`.

Хэндлеры (триггеры/логика/псевдокод):

- `handlers/start.py`
  - Триггер: `@router.message(F.text == "/start")`.
  - Логика:
    1) FSM clear.
    2) По `telegram_id` ищет/создает `User`. Новый — TEST_PRO с лимитами (`Limits`).
    3) Новому: отправляет `LEXICON_RU['start_promo']`, пауза 2 сек, затем `LEXICON_RU['start_howto']` + `get_main_menu_keyboard()`.
    4) Существующему: при необходимости перевод TEST_PRO → FREE по истечению; обновляет `last_activity_at`; отправляет `LEXICON_RU['returning_user_welcome']` с главным меню.
  - Сообщения: строго из `LEXICON_RU`.

- `handlers/menu.py`
  - Триггер: callback `data == "main_menu"`.
  - Логика: редактирует сообщение на `LEXICON_RU['main_menu_message']` + `get_main_menu_keyboard(user.subscription_type)`.

- `handlers/profile.py`
  - Триггеры: callback `data == "profile"`; callback-и `ProfileCallbackData` (`limits_help`, `back_to_profile`, `show_offer`, `compare_free_pro`, `compare_pro_ultra`, `show_free_offer`), и старые обратносуместимые `limits_info`, `upgrade_pro`, `upgrade_ultra`, `noop`.
  - Логика: выбирает шаблон профиля по `SubscriptionType` и подставляет значения лимитов. Тексты:
    - TEST_PRO: `LEXICON_RU['profile_test_pro_main']`
    - FREE: `LEXICON_RU['profile_free_main']`
    - PRO: `LEXICON_RU['profile_pro_main']`
    - ULTRA: `LEXICON_RU['profile_ultra_main']`
    - Кнопки — из соответствующих фабрик; тексты кнопок из `LEXICON_COMMANDS_RU`.
  - Спецэкраны: `profile_limits_help` (`LEXICON_RU['profile_limits_help']`), сравнения (`profile_free_compare`, `profile_pro_compare`), офферы подписок (`profile_test_pro_offer`, `profile_free_offer`).

- `handlers/analytics.py`
  - Триггеры:
    - `Command("cancel")` — отмена FSM
    - callback: `analytics_start`, `analytics` (вход), `analytics_show_csv_guide`, `analytics_show_intro`, `analytics_show_reports`, `new_analysis`, `view_report_<id>`, `analytics_report_back_<analysis_id>`
    - сообщения в FSM: `waiting_for_*` (portfolio_size → upload_limit → monthly_uploads → acceptance_rate → выбор content_type), и callback `content_type_*`.
  - Логика, кратко:
    1) FREE — показывает `LEXICON_RU['analytics_unavailable_free']`.
    2) Показывает intro `LEXICON_RU['analytics_intro']` (+ `LEXICON_RU['analytics_csv_instruction']`), либо список отчетов.
    3) Обработка загрузки CSV: прием файла, валидации, сохранение `CSVAnalysis(status=PENDING)`; запуск FSM вопросов.
    4) По завершении FSM — обновление `CSVAnalysis` (status=PROCESSING), фоновая обработка через `process_csv_analysis()`.
    5) `process_csv_analysis()`: `AdvancedCSVProcessor.process_csv()` → `FixedReportGenerator.generate_monthly_report()` и `generate_combined_report_for_archive()` → сохранить `AnalyticsReport`, отметить `CSVAnalysis` COMPLETED, списать лимит `Limits.analytics_used += 1`; отправить последовательность сообщений:
       - `LEXICON_RU['final_analytics_report']`
       - `LEXICON_RU['analytics_explanation_title']`
       - `LEXICON_RU['sold_portfolio_report']`
       - `LEXICON_RU['new_works_report']`
       - `LEXICON_RU['upload_limit_report']`
       - `LEXICON_RU['analytics_closing_message']` + кнопка назад (`LEXICON_COMMANDS_RU['back_to_main_menu']`).
    6) Хранит `analytics_message_ids` для удаления пачки сообщений по кнопке «Назад».
  - Псевдокод FSM (упрощенно):
    ```python
    on CSV upload:
      if user.type == FREE or limits.analytics_remaining <= 0: reply LEXICON_RU['limits_analytics_exhausted']; stop
      save CSVAnalysis(PENDING)
      ask: LEXICON_RU['ask_portfolio_size'] -> int > 0
      ask: LEXICON_RU['ask_monthly_limit'] -> int > 0
      ask: LEXICON_RU['ask_monthly_uploads'] -> int >= 0
      ask: LEXICON_RU['ask_profit_percentage'] -> 0..100
      ask button content_type (AI/PHOTO/ILLUSTRATION/VIDEO/VECTOR)
      set CSVAnalysis(status=PROCESSING, content_type=ENUM)
      reply: LEXICON_RU['processing_csv']
      process_csv_analysis(csv_id)
    ```

- `handlers/themes.py`
  - Триггеры: callback `themes` (вход), `ThemesCallback(action=="generate")`, `ThemesCallback(action=="archive"|"archive_page")`, `noop`.
  - Логика:
    1) Проверка cooldown: последняя `ThemeRequest` со статусом ISSUED + `get_theme_cooldown_days_sync(user.id)` → если ещё рано, показать `LEXICON_RU['themes_cooldown']` с `create_cooldown_keyboard()`.
    2) Вступительный экран: FREE → `LEXICON_RU['themes_intro_free']`; PRO/ULTRA/TEST_PRO → `LEXICON_RU['themes_intro_pro_ultra']`. Кнопки — `get_themes_menu_keyboard()`.
    3) «Получить темы»: проверить лимиты; повторная проверка cooldown; выбрать количество тем: FREE=1, PRO/TEST_PRO=5, ULTRA=10; взять пул `ThemeRequest(status=READY)` случайно, исключая ранее выданные пользователю названия; если не хватает — добрать любыми READY; выдать пользователю форматированный список с заголовком `LEXICON_RU['themes_list_free']` или `LEXICON_RU['themes_list_pro_ultra']`; сохранить как `ThemeRequest(ISSUED)` и увеличить `limits.themes_used`.
    4) Архив: пагинация по `ThemeRequest(ISSUED)`, форматирование списка.
  - Псевдокод генерации:
    ```python
    on ThemesCallback(generate):
      assert limits.themes_remaining > 0
      assert cooldown passed (last ISSUED vs now)
      amount = {FREE:1, PRO/TEST_PRO:5, ULTRA:10}
      issued_names = all previously ISSUED names splitlines
      ready = select ThemeRequest where status==READY order by random
      available = [t for t in ready if t.theme_name not in issued_names][:amount]
      if len(available) < amount: available = ready[:amount]
      save ThemeRequest(ISSUED, theme_name='\n'.join(selected))
      limits.themes_used += 1; limits.last_theme_request_at = now
      reply with LEXICON_RU[result_key]
    ```

- `handlers/admin.py`
  - Триггер: `/admin` (message). Требуется `is_admin(user_id)`.
  - Разделы: статистика (`admin_stats`), рассылка (`admin_broadcast` + выбор целевой аудитории + ввод текста → массовая отправка), системные функции (`admin_system`), здоровье (`admin_health`), управление тарифом (`admin_manage_tariff` + `ActionCallback(action="admin_set_tariff", param=...)`).
  - Тексты: меню переключает экран; при изменении тарифа — использовать `LEXICON_RU['admin_tariff_*']`.

- Прочие хэндлеры (lessons, calendar, faq, channel, payments, invite):
  - Должны использовать тексты из `LEXICON_RU` и кнопки из `LEXICON_COMMANDS_RU`.


### Часть B1: Полная спецификация приема CSV, FSM и данных

Контракт входящих данных CSV (ожидаемые колонки):
- sale_datetime_utc (ISO8601, UTC), asset_id (string), asset_title (string), license_plan ("custom"|"subscription"), royalty_usd (денежный формат), media_type ("photos"|"videos"|"illustrations"), filename, contributor_name, size_label.

Очистка и нормализация (строго):
- Удаление валютных символов и пробелов из royalty_usd, замена запятой на точку, `to_numeric(errors='coerce')`.
- Тримминг строк, приведение категорий к lower-case.
- Даты: `to_datetime(..., utc=True, errors='coerce')`.

Валидность месяца (ровно один календарный месяц):
- Преобразовать даты к `period('M')`, должно быть одно значение. Если больше — использовать первое (для устойчивости), сформировать `period_month = YYYY-MM-01` и `period_human_ru = <Месяц RU> <YYYY>`.

Фильтрация «битых» строк:
- Критические поля: sale_datetime_utc, asset_id, royalty_usд (если присутствуют в наборе) — любая NaN/пустое → строка считается битой.
- Порог брака: `BROKEN_ROWS_THRESHOLD_PCT = 20.0`. Если процент битых > порога — ошибка обработки.

FSM — последовательность вопросов и валидации:
1) portfolio_size: int > 0
2) upload_limit: int > 0
3) monthly_uploads: int >= 0
4) acceptance_rate: float в диапазоне [0, 100]
5) content_type (callback): маппинг в БД enum: {AI→MIXED, PHOTO/ILLUSTRATION/VECTOR→PHOTOS, VIDEO→VIDEOS}.

Правила транзакций:
- `CSVAnalysis` создается со статусом PENDING до начала FSM.
- После сбора всех ответов — статус PROCESSING и запись пользовательских параметров в ту же строку анализа.
- Списывать `limits.analytics_used += 1` только ПОСЛЕ успешной обработки и сохранения `AnalyticsReport`.

Очередность сообщений при успешной обработке:
1) `LEXICON_RU['final_analytics_report']` — агрегаты
2) `LEXICON_RU['analytics_explanation_title']`
3) `LEXICON_RU['sold_portfolio_report']`
4) `LEXICON_RU['new_works_report']`
5) `LEXICON_RU['upload_limit_report']`
6) `LEXICON_RU['analytics_closing_message']` + кнопка `LEXICON_COMMANDS_RU['back_to_main_menu']`

Хранение `analytics_message_ids` в `CSVAnalysis` (через запятую) для последующего удаления при возврате назад.


### Часть A1: Алгоритмы расчета KPI и формирование отчета

Обозначения (из результата парсинга):
- S = число продаж (rows_used),
- R = сумма выручки (USD) = sum(royalty_usd),
- U = число уникальных ассетов с продажей,
- A = acceptance_rate (из FSM),
- P = portfolio_size (из FSM),
- ML = monthly_uploads (из FSM),
- UL = upload_limit (из FSM).

Формулы:
- Средний доход на продажу: `avg_revenue_per_sale = R / S`, если S>0, иначе 0.
- % портфеля, который продался: `portfolio_sold_percent = (S / max(P,1)) * 100` (используется S, т.к. отражает активность продаж за месяц).
- Доля продаж новых работ: вычисляется из датафрейма по бизнес-правилу «новые работы за 3 месяца»: отношение продаж по ассетам с датой загрузки/идентификатором, подходящим под правило «новизны», к общему S. Точная реализация — через `KPICalculator.calculate_new_works_sales_percent(df_clean)`.
- Использование лимита загрузки: `upload_limit_usage = (ML / max(UL,1)) * 100`, усечение [0,100].

Пороговые интерпретации (примерные градации из лексикона):
- sold_portfolio: <1, [1;2), [2;3), [3;5), ≥5 — тексты `sold_portfolio_*`.
- new_works: <10, [10;20), [20;30), [30;85), [85;100] — тексты `new_works_*`.
- upload_limit: ≤30, (30;60], (60;80], (80;95], (95;100] — тексты `upload_limit_*`.

Формирование отчета:
- Архивный отчет `report_text_html` должен содержать объединенный блок: заголовок агрегатов и три секции интерпретаций (примеры в `FixedReportGenerator.generate_combined_report_for_archive`).
- Все отображаемые тексты берутся из `LEXICON_RU` с подстановками.

#### Точная реализация KPICalculator.calculate_new_works_sales_percent

Цель: вычислить долю продаж новых работ за период относительно всех продаж периода.

Вход: очищенный датафрейм `df_clean` с колонками как минимум: `sale_datetime_utc`, `asset_id`.

Правила и шаги:
1) Определить окно «новизны» — последние 3 календарных месяца относительно максимальной даты продаж в `df_clean`.
   - `max_dt = df_clean['sale_datetime_utc'].max()` (naive/UTC одинаково, важно сравнение)
   - `threshold = max_dt - relativedelta(months=3)` (или 90 дней, но предпочтительно месяцы)
2) Группировать продажи по `asset_id`, взять минимальную дату продажи каждого ассета:
   - `first_sale_per_asset = df_clean.groupby('asset_id')['sale_datetime_utc'].min()`
3) Считать ассет «новым», если его первая продажа ≥ `threshold`.
   - `new_asset_ids = {a for a, dt in first_sale_per_asset.items() if dt >= threshold}`
4) Подсчитать общее число продаж периода: `S = len(df_clean)`.
5) Подсчитать число продаж по «новым» ассетам:
   - `S_new = len(df_clean[df_clean['asset_id'].isin(new_asset_ids)])`
6) Возвратить процент: `pct = round((S_new / S) * 100, 2)` при `S>0`, иначе `0.0`.

Примечания:
- Если колонка с датой загрузки отсутствует, используем «первая продажа ассета» как прокси для «принятия за последние 3 месяца» — это устойчивая эвристика для Adobe Stock.
- При отсутствии дат у части строк эти строки исключаются как «битые» на этапе `_drop_broken`.

Проверка полноты прочих расчетов:
- `rows_used` = количество валидных строк продаж после фильтрации — достаточно определено.
- `total_revenue_usd` = сумма по `royalty_usd` — корректно при очистке валюты.
- `unique_assets_sold` = число уникальных `asset_id` — не используется в финальном отчете, но может пригодиться в админке.
- `avg_revenue_per_sale` = `R / S` — определено с защитой при `S=0`.
- `portfolio_sold_percent` = `(S / P) * 100` — требует валидного `P>0`; в FSM валидация есть.
- `upload_limit_usage` = `(ML / UL) * 100` — требует `UL>0`; в FSM валидация есть.
- Пороговые тексты для трех метрик задокументированы и сопоставлены ключам `LEXICON_RU`.

Вывод: текущих данных и формул достаточно для 100% воспроизведения расчетов и сообщений.


### Часть C: Админ-панель (FastAPI)

`admin_panel/main.py`:
- FastAPI-приложение, `SessionMiddleware` (секрет — из `ADMIN_SECRET_KEY`), монтирование статики и шаблонов.
- `sqladmin.Admin` с моделями: `User`, `Limits`, `CSVAnalysis`, `AnalyticsReport`, `ThemeRequest`, `SystemMessage` (в чистой версии убрать `Subscription`, `VideoLesson`, `LLMSettings`, `GlobalTheme`/`UserIssuedTheme`, если они не используются).
- Роуты: `dashboard`, `themes`, `placeholders`.

Аутентификация `admin_panel/auth.py`:
- `AdminAuth` — логин по `telegram_id` (username) и флагу `is_admin` в БД. Сессионные cookie.

Эндпоинты (`admin_panel/views`):
- `GET /dashboard` → шаблон `simple_dashboard.html` (демо-версия статистики).
  - Назначение: обзорные метрики.
  - Логика: может дергать `admin_panel/services.get_dashboard_stats`.

- `GET /themes` → шаблон `themes.html`.
  - Назначение: управление темами и настройками cooldown.
  - Логика: просмотр выданных тем (`ThemeRequest` со статусом ISSUED/READY), настройка cooldown сообщения через `SystemMessage(key="themes_cooldown_message")` и значения cooldown через `Limits.theme_cooldown_days`.

- `POST /themes/update`
  - Назначение: обновление `interval_days` и `themes_cooldown_message`.
  - Логика: сохранить `SystemMessage(key="themes_cooldown_message")`, а также обновить поле `Limits.theme_cooldown_days` для выбранных пользователей (или дефолт на уровне приложения).

- Остальные разделы — placeholder-страницы (`/portfolio-analytics`, `/calendar`, `/profile`, `/faq`, `/admins`, `/user-management`, `/broadcast`, `/referral`) рендерят `placeholder.html`.

Тексты в админке: если есть пользовательские сообщения — хранить в `SystemMessage` (а не в коде) и подтягивать в UI. В боте — всегда из `bot/lexicon/lexicon_ru.py`.


### Часть D: Фоновые задачи (Dramatiq)

`workers/actors.py`:
- Инициализация `RedisBroker` с `REDIS_URL` (приоритет env, затем settings). Жесткая проверка валидности URL.
- Актеры:
  - `process_csv_file(file_path: str, user_id: int)` — обработка CSV (демо-заглушка; в чистой версии вызывать ядро аналитики и сохранять результат в БД).
  - `send_notification(user_id: int, message: str)` — отправка уведомлений пользователю (демо-заглушка; в чистой версии дергать бота/канал уведомлений).
  - `generate_report(user_id: int, report_type: str)` — генерация отчета (демо-заглушка; в чистой версии вызывать `FixedReportGenerator`).
  - `cleanup_temp_files()` — очистка временных файлов.

Примечания:
- Инициализация брокера предусмотрена для форкнутых процессов, переменная окружения `REDIS_URL` пробрасывается в дочерние процессы.


## 5. Интеграция лексикона (обязательно)

Все тексты сообщений и кнопок ДОЛЖНЫ храниться и браться из `bot/lexicon/lexicon_ru.py`:
- Примеры для бота:
  - Приветствие/онбординг: `LEXICON_RU['start_promo']`, `LEXICON_RU['start_howto']`.
  - Главное меню: `LEXICON_RU['main_menu_message']`.
  - Аналитика: `LEXICON_RU['analytics_intro']`, `LEXICON_RU['analytics_csv_instruction']`, `LEXICON_RU['final_analytics_report']`, `LEXICON_RU['analytics_explanation_title']`, `LEXICON_RU['sold_portfolio_report']`, `LEXICON_RU['new_works_report']`, `LEXICON_RU['upload_limit_report']`, `LEXICON_RU['analytics_closing_message']`, `LEXICON_RU['limits_analytics_exhausted']`.
  - Темы: `LEXICON_RU['themes_intro_free']`, `LEXICON_RU['themes_intro_pro_ultra']`, `LEXICON_RU['themes_list_free']`, `LEXICON_RU['themes_list_pro_ultra']`, `LEXICON_RU['themes_cooldown']`.
  - Профиль: `LEXICON_RU['profile_*']`, админ-тарифы: `LEXICON_RU['admin_tariff_*']`.
- Кнопки из `LEXICON_COMMANDS_RU`: например, `['analytics']`, `['themes']`, `['calendar']`, `['lessons']`, `['profile']`, `['faq']`, `['tg_channel']`, `['get_themes']`, `['archive_themes']`, `['back_to_main_menu']`, `['new_analysis']`, `['upgrade_pro']`, `['upgrade_ultra']`, `['admin_manage_tariff']` и др.
- Для админ-панели тексты, настраиваемые через UI, хранить в `SystemMessage` (например, `themes_cooldown_message`) и использовать там, где это уместно; все бот-сообщения — строго через лексикон.


## 6. Рекомендации по «чистой» реализации

Зависимости (предварительный аудит `requirements.txt`):
- Оставить:
  - aiogram, sqlalchemy, alembic, asyncpg/aiosqlite, redis, pandas, numpy, fastapi, uvicorn, sqladmin, jinja2, python-multipart, pydantic, pydantic-settings, structlog, httpx, dramatiq, apscheduler (если используется в `core.notifications.scheduler`).
- Пересмотреть/исключить, если не используются:
  - python-telegram-bot (не нужен),
  - flask, flask-admin, flask-sqlalchemy, flask-wtf (заменить на FastAPI health),
  - celery (не используется),
  - ydata-profiling, plotly, pillow, playwright, lxml, beautifulsoup4, aiohttp — удалить, если нет фактического использования,
  - LLM-библиотеки (openai, anthropic, google-generativeai) — удалить,
  - sentry-sdk[flask] — убрать или заменить на универсальный sentry-sdk при необходимости.

Файлы/папки к упрощению:
- Удалить `api/healthcheck.py` (Flask) и заменить на маленький FastAPI `api/health.py` с `/health`.
- Полностью удалить LLM-слой: `core/ai`, `config/ai.py`, модель `LLMSettings`.
- Сохранить только реально используемые handlers/routers/keyboard-фабрики. Все тексты — централизовать в `lexicon_ru.py`.
- Проверить `docs/` и «*_COMPLETE.md» артефакты — оставить как внешнюю документацию, но не включать в минимально необходимый собранный артефакт.

Инварианты:
- Все сообщения и тексты кнопок — только из `bot/lexicon/lexicon_ru.py`.
- Все новые тексты, появляющиеся в коде, немедленно выносить в `LEXICON_RU`/`LEXICON_COMMANDS_RU` и обращаться к ключам.
- Виртуальное окружение обязательно для разработки, тестов и сборки.
- Поддержать PostgreSQL на Railway; не ломать enum-типы (совместимость с миграциями Alembic).

Миграция/деплой:
- Переменные окружения: `BOT_TOKEN`, `DATABASE_URL`, `REDIS_URL`, `ADMIN_SECRET_KEY`.
- Alembic upgrade перед запуском приложений.
- Запуск: отдельные процессы для бота, админки FastAPI; воркеры Dramatiq.


## 7. Деплой на Railway (подробно)

Архитектура сервисов Railway:
- Один проект Railway с тремя службами:
  - bot-service: процесс Telegram-бота (aiogram)
  - admin-service: FastAPI админ-панель (uvicorn)
  - worker-service: Dramatiq воркеры (фоновые задачи)
- Подключенные плагины: PostgreSQL (DATABASE_URL), Redis (REDIS_URL).

Необходимые переменные окружения:
- BOT_TOKEN — токен бота от @BotFather (только bot-service).
- DATABASE_URL — строка подключения к Railway PostgreSQL.
- REDIS_URL — URL Redis (из Railway Redis плагина).
- ADMIN_SECRET_KEY — секрет для сессий админки (admin-service).
- LOG_LEVEL=INFO, DEBUG=false — по необходимости.

Команды запуска (Procfile):
```
bot: python -m bot.main
admin: uvicorn admin_panel.main:app --host 0.0.0.0 --port 8000
worker: dramatiq workers.actors --processes 1 --threads 4 --watch .
```

Шаги деплоя:
1) Подключить репозиторий к Railway.
2) В Variables задать: BOT_TOKEN, DATABASE_URL, REDIS_URL, ADMIN_SECRET_KEY.
3) Создать службы:
   - bot-service: `python -m bot.main`.
   - admin-service: `uvicorn admin_panel.main:app --host 0.0.0.0 --port 8000`.
   - worker-service: `dramatiq workers.actors --processes 1 --threads 4 --watch .`.
4) Выполнить миграции (однократно): `alembic upgrade head`.
5) Проверить логи: бот запущен, admin отвечает на /dashboard, воркер подключен к Redis.

Секреты/безопасность:
- Не коммитить токены; хранить только в Railway Variables.
- Ограничить публичный доступ только к admin-service (порт 8000), бот/воркер — без публичного HTTP.


## Приложение: Псевдопроцессы и последовательности

1) Поток «Загрузка CSV → Отчет»:
```python
User clicks analytics → sees intro (LEXICON_RU['analytics_intro']).
User uploads CSV → CSVAnalysis(PENDING) + FSM questions.
On final content_type → set CSVAnalysis(PROCESSING) → reply LEXICON_RU['processing_csv'].
AdvancedCSVProcessor.process_csv() → FixedReportGenerator.generate_monthly_report().
Save AnalyticsReport + CSVAnalysis(COMPLETED), charge limits.analytics_used += 1.
Send sequence of messages using LEXICON_RU keys.
Store analytics_message_ids for later cleanup; back button deletes them and returns main menu.
```

2) Поток «Получить темы недели»:
```python
User opens themes → cooldown check → intro text by tariff.
On generate → check limits and cooldown.
Pick N themes from READY excluding already issued names.
Save ThemeRequest(ISSUED) + update Limits (themes_used, last_theme_request_at).
Reply with LEXICON_RU['themes_list_free'|'themes_list_pro_ultra'] and menu.
```

3) Админ-поток «Управление тарифом (сам себе)»:
```python
/admin → admin menu.
"Управление тарифом" → клавиатура с вариантами (TEST_PRO/FREE/PRO/ULTRA).
Action(admin_set_tariff, param=TYPE) → обновить User.subscription_type, expires_at, Limits totals, used=0.
Ответ: LEXICON_RU['admin_tariff_success'].
```


---

Короткий чеклист при переносе:
- Восстановить директории/модули как описано в разделе Архитектуры.
- Поднять конфиг, БД (миграции), Redis, Dramatiq.
- Перенести модели 1:1, сохранить enum’ы и каскады.
- Переподключить все тексты к `lexicon_ru.py` (проверить, что в коде нет “захардкоженных” сообщений; если есть — вынести ключи).
- Прогнать путь CSV→отчет и Темы→cooldown→выдача.
- Админка: логин, просмотр, настройка тем/cooldown, sqladmin views.


## Приложение B: Клавиатуры и callback-схемы (подробно)

Именование callback-data:
- Используются data-строки и Pydantic-like структуры `CallbackData` (напр. `ThemesCallback`, `ProfileCallbackData`, `CommonCallbackData`, `ActionCallback`).
- Общий формат: `"<namespace>[:]<action>[_<params>]"` для простых строк, либо сериализация через фабрики aiogram 3.x.

Основные callback-и и действия:
- Главное меню:
  - `"main_menu"` — открывает главное меню.
- Аналитика:
  - `"analytics"` — вход в раздел.
  - `"analytics_start"` — показать подсказку загрузки CSV.
  - `"analytics_show_csv_guide"` — инструкция CSV.
  - `"analytics_show_intro"` — вернуться к intro.
  - `"analytics_show_reports"` — список отчетов.
  - `"view_report_<id>"` — открыть отчет с id.
  - `"new_analysis"` — начать новый анализ.
  - `"analytics_report_back_<csv_analysis_id>"` — удалить цепочку сообщений отчета и вернуться в меню.
- Темы:
  - `ThemesCallback(action="generate")` — сгенерировать/выдать темы.
  - `ThemesCallback(action="archive")` — открыть архив (последняя подборка).
  - `ThemesCallback(action="archive_page", page=<int>)` — пагинация архива.
- Профиль:
  - `ProfileCallbackData(action="limits_help")` — экран про лимиты.
  - `ProfileCallbackData(action="back_to_profile")` — назад в профиль.
  - `ProfileCallbackData(action="show_offer")` — оффер тарифа.
  - `ProfileCallbackData(action="compare_free_pro")` — сравнить FREE vs PRO.
  - `ProfileCallbackData(action="compare_pro_ultra")` — сравнить PRO vs ULTRA.
  - `ProfileCallbackData(action="show_free_offer")` — оффер из FREE.
- Админ:
  - `ActionCallback(action="admin_set_tariff", param=<TEST_PRO|FREE|PRO|ULTRA>)`

Клавиатуры (примерные фабрики):
- Главное меню: `get_main_menu_keyboard(subscription_type)` — кнопки из `LEXICON_COMMANDS_RU` (analytics/themes/calendar/lessons/profile/faq/tg_channel/invite_friend) и/или inline.
- Аналитика:
  - `get_analytics_intro_keyboard(has_reports: bool)` — показать загрузку CSV и, если есть, кнопку «Показать отчеты».
  - `get_analytics_list_keyboard(reports, can_create_new, subscription_type)` — список отчетов + «Новый анализ».
  - `get_analytics_report_view_keyboard(all_reports, active_report_id, subscription_type)` — навигация по отчетам.
- Темы:
  - `get_themes_menu_keyboard(has_archive: bool)` — «Получить темы», «Архив тем», «Назад».
  - `create_cooldown_keyboard(subscription_type)` — показать кнопки возврата/перехода в профиль.
- Профиль: набор фабрик `get_profile_*_keyboard()` согласно тарифам.

Все надписи кнопок брать из `LEXICON_COMMANDS_RU`.


## Приложение C: Горизонтальная навигация (замена сообщений)

Требование: все экраны разделов работают «по горизонтали» — без нагромождения вертикальной ленты. Реализуется через редактирование текста/клавиатур предыдущего сообщения вместо отправки нового.

Механика:
- Используется утилита `bot.utils.safe_edit.safe_edit_message(callback, text, reply_markup, parse_mode)` для безопасного редактирования сообщения, обработка `TelegramBadRequest`.
- Все входы по callback’ам должны вызывать `safe_edit_message`, а не `answer` (кроме специальных цепочек аналитики, где требуется серия отдельных сообщений отчета).
- Возврат в главное меню/назад также делает `safe_edit_message` с заменой текста и клавиатуры.
- Для FSM вопросов мы удаляем предыдущий вопрос и сообщение пользователя, показывая только один «активный» вопрос.
- Для цепочки аналитики после генерации отчета отправляются несколько сообщений (вертикально), но затем они связаны «кнопкой назад», которая удаляет все сообщения по их `message_id` из `CSVAnalysis.analytics_message_ids` и возвращает пользователя в «горизонтальный» экран.

Инвариант: в разделах меню и подэкранах всегда один активный экран — достигается заменой (edit_message) вместо отправки новых сообщений.


### Примеры payload’ов и точные схемы клавиатур по экранам

1) Главное меню (`get_main_menu_keyboard(subscription_type)`)
- Inline-сетка (2–3 ряда; может отличаться, допускается адаптация под количество кнопок):
  - Ряд 1: `[ analytics ]  [ themes ]`
  - Ряд 2: `[ calendar ]  [ lessons ]`
  - Ряд 3: `[ profile ]  [ faq ]`
  - Ряд 4: `[ tg_channel ]  [ invite_friend ]`
- Примеры callback data:
  - `"analytics"`, `"themes"`, `"calendar"`, `"lessons"`, `"profile"`, `"faq"`, `"tg_channel"`

2) Аналитика — intro (`get_analytics_intro_keyboard(has_reports: bool)`) и CSV-гайд
- Intro (нет отчётов):
  - Ряд 1: `[ how_to_export_csv ]` (payload: `"analytics_show_csv_guide"`)
  - Ряд 2: `[ back_to_main_menu ]` (payload: `"main_menu"`)
- Intro (есть отчёты):
  - Ряд 1: `[ show_reports ]` (payload: `"analytics_show_reports"`)
  - Ряд 2: `[ how_to_export_csv ]` (payload: `"analytics_show_csv_guide"`)
  - Ряд 3: `[ back_to_main_menu ]` (payload: `"main_menu"`)
- CSV-гайд (`get_csv_instruction_keyboard()`):
  - Ряд 1: `[ back_to_main_menu ]` (payload: `"main_menu"`)

3) Аналитика — список отчётов (`get_analytics_list_keyboard(reports, can_create_new, subscription_type)`)
- Динамические ряды с отчётами:
  - Каждый ряд: `[ 📊 Отчет за {period_human_ru} ]` → payload: `"view_report_<report_id>"`
- Нижние ряды:
  - Если `can_create_new`: `[ new_analysis ]` → `"new_analysis"`
  - `[ back_to_main_menu ]` → `"main_menu"`

4) Аналитика — просмотр отчёта (`get_analytics_report_view_keyboard(all_reports, active_report_id, subscription_type)`)
- Навигация по отчётам (пример):
  - Ряд 1: `[ ◀️ ] [ №{i}/{n} ] [ ▶️ ]` → стрелки генерируют `"view_report_<prev_id>"` / `"view_report_<next_id>"`, центр `"noop"`
  - Ряд 2: `[ back_to_main_menu ]` → `"main_menu"`
- Для финального сообщения отчёта (последнее из серии):
  - Ряд 1: `[ back_to_main_menu ]` → payload: `"analytics_report_back_<csv_analysis_id>"` (это очищает все message_ids отчёта)

5) Темы — меню (`get_themes_menu_keyboard(has_archive: bool)`) и cooldown
- Обычный экран (есть архив):
  - Ряд 1: `[ get_themes ]` → `ThemesCallback(action="generate")`
  - Ряд 2: `[ archive_themes ]` → `ThemesCallback(action="archive")`
  - Ряд 3: `[ back_to_main_menu ]` → `"main_menu"`
- Без архива:
  - Ряд 1: `[ get_themes ]`
  - Ряд 2: `[ back_to_main_menu ]`
- Экран cooldown (`create_cooldown_keyboard(subscription_type)`):
  - Ряд 1: `[ back_to_main_menu ]` → `"main_menu"`

6) Темы — архив и пагинация (`create_archive_navigation_keyboard(page, total_pages, subscription_type)`)
- Ряд 1: `[ ◀️ ] [ {page+1}/{total_pages} ] [ ▶️ ]`
  - ◀️: `ThemesCallback(action="archive_page", page=page-1)` (если page>0, иначе `"noop"`)
  - ▶️: `ThemesCallback(action="archive_page", page=page+1)` (если page<total_pages-1, иначе `"noop"`)
- Ряд 2: `[ back_to_main_menu ]` → `"main_menu"`

7) Профиль — экраны и клавиатуры
- TEST_PRO (`get_profile_test_pro_keyboard()`):
  - Ряд 1: `[ button_limits_help ]` → `ProfileCallbackData(action="limits_help")`
  - Ряд 2: `[ button_subscribe ]` → `ProfileCallbackData(action="show_offer")`
  - Ряд 3: `[ back_to_main_menu ]` → `CommonCallbackData(action="main_menu")`
- FREE (`get_profile_free_keyboard()`):
  - Ряд 1: `[ button_compare_free_pro ]` → `ProfileCallbackData(action="compare_free_pro")`
  - Ряд 2: `[ button_subscribe ]` → `ProfileCallbackData(action="show_free_offer")`
  - Ряд 3: `[ back_to_main_menu ]`
- PRO (`get_profile_pro_keyboard()`):
  - Ряд 1: `[ button_compare_pro_ultra ]` → `ProfileCallbackData(action="compare_pro_ultra")`
  - Ряд 2: `[ back_to_main_menu ]`
- ULTRA (`get_profile_ultra_keyboard()`):
  - Ряд 1: `[ back_to_main_menu ]`
- Экран «лимиты» (`get_profile_limits_help_keyboard()`):
  - Ряд 1: `[ button_back_profile ]` → `ProfileCallbackData(action="back_to_profile")`

8) Админ — основное меню и управление тарифом
- Админ-меню:
  - Ряд 1: `[ "📊 Статистика" ]` → `"admin_stats"`
  - Ряд 2: `[ "📢 Рассылка" ]` → `"admin_broadcast"`  |  `[ "⚙️ Система" ]` → `"admin_system"`
  - Ряд 3: `[ admin_manage_tariff ]` → `"admin_manage_tariff"`  |  `[ "📈 Здоровье" ]` → `"admin_health"`
  - Ряд 4: `[ back_to_main_menu ]` → `"main_menu"`
- Управление тарифом (`get_admin_tariff_keyboard()`):
  - Ряд 1: `[ admin_tariff_set_test_pro ]` → `ActionCallback(action="admin_set_tariff", param="TEST_PRO")`
  - Ряд 2: `[ admin_tariff_set_free ]` → `ActionCallback(action="admin_set_tariff", param="FREE")`
  - Ряд 3: `[ admin_tariff_set_pro ]` → `ActionCallback(action="admin_set_tariff", param="PRO")`
  - Ряд 4: `[ admin_tariff_set_ultra ]` → `ActionCallback(action="admin_set_tariff", param="ULTRA")`
  - Ряд 5: `[ button_back_to_admin ]` → `"admin_back"`


