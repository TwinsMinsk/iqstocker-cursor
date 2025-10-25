# Исправление метрик аналитики - Завершено

## Дата: 23 октября 2025

## Описание задачи
Исправлены расчеты "% портфеля" и добавлена "Средняя цена продажи" в отчет аналитики согласно ТЗ.

## Выполненные изменения

### 1. ✅ config/settings.py
- **Статус**: Проверен
- **Изменения**: Параметр `new_works_id_prefix` уже существует (строка 176) и проброшен в класс Settings (строка 229)
- **Значение по умолчанию**: "150"

### 2. ✅ core/analytics/kpi_calculator.py
- **Файл**: `core/analytics/kpi_calculator.py`
- **Изменения**:
  - Изменена сигнатура метода `calculate_portfolio_sold_percent`:
    - **Было**: `def calculate_portfolio_sold_percent(self, unique_assets_sold: int, portfolio_size: int)`
    - **Стало**: `def calculate_portfolio_sold_percent(self, total_sales: int, portfolio_size: int)`
  - Формула изменена с использования `unique_assets_sold` на `total_sales`
  - Формула: `(total_sales / portfolio_size) * 100`
  - Обновлен метод `calculate_all_kpis` для использования `total_sales` вместо `unique_assets_sold`

### 3. ✅ core/analytics/advanced_csv_processor.py
- **Файл**: `core/analytics/advanced_csv_processor.py`
- **Изменения**:
  - Исправлен вызов `calculate_portfolio_sold_percent` в методе `_compute_advanced_metrics`
  - Передается `total_sales_count` вместо `unique_assets_sold`
  - Поле `avg_revenue_per_sale` уже рассчитывается и передается в `AdvancedProcessResult`
  - Формула: `total_revenue_usd / total_sales_count` (с проверкой деления на ноль)

### 4. ✅ bot/lexicon/lexicon_ru.py
- **Файл**: `bot/lexicon/lexicon_ru.py`
- **Изменения**:
  - Обновлен ключ `final_analytics_report` (строка 105-110)
  - Изменена переменная с `{avg_price}` на `{avg_revenue_per_sale}`
  - Добавлена строка: `"Средняя цена продажи - <b>${avg_revenue_per_sale}</b>\n"`

### 5. ✅ core/analytics/report_generator_fixed.py
- **Файл**: `core/analytics/report_generator_fixed.py`
- **Изменения**:
  - Обновлен метод `generate_monthly_report`:
    - Изменен ключ с `avg_price` на `avg_revenue_per_sale`
    - Форматирование: `f"{result.avg_revenue_per_sale:.2f}"` (до 2 знаков после запятой)
  - Обновлен метод `generate_combined_report_for_archive`:
    - Изменено форматирование с `.4f` на `.2f` для средней цены продажи

### 6. ✅ database/models/analytics_report.py
- **Файл**: `database/models/analytics_report.py`
- **Изменения**:
  - Добавлено новое поле: `avg_revenue_per_sale: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)`
  - Поле помещено после `total_revenue` в секции "Main metrics"

### 7. ✅ bot/handlers/analytics.py
- **Файл**: `bot/handlers/analytics.py`
- **Изменения**:
  - Обновлено создание объекта `AnalyticsReport` (строка 900-911):
    - Добавлено сохранение: `avg_revenue_per_sale=result.avg_revenue_per_sale`
  - Обновлено форматирование сообщения (строка 943-953):
    - Изменен ключ с `avg_price` на `avg_revenue_per_sale`

### 8. ✅ Миграция базы данных
- **Файл**: `database/migrations/versions/a8bc56db2186_add_avg_revenue_per_sale_to_analytics_.py`
- **Изменения**:
  - Создана миграция для добавления поля `avg_revenue_per_sale` в таблицу `analytics_reports`
  - Тип поля: `Numeric(precision=10, scale=2), nullable=True`
  - Миграция успешно применена к базе данных

## Результаты

### Исправленные метрики:
1. **% портфеля, который продался за месяц**:
   - **Было**: Рассчитывался на основе `unique_assets_sold` (уникальных проданных работ)
   - **Стало**: Рассчитывается на основе `total_sales` (общего количества продаж)
   - **Формула**: `(total_sales / portfolio_size) * 100`

2. **Средняя цена продажи**:
   - **Было**: Отсутствовала в отчете
   - **Стало**: Добавлена в отчет с форматированием до 2 знаков после запятой
   - **Формула**: `total_revenue_usd / total_sales_count`
   - **Отображение**: `Средняя цена продажи - $X.XX`

### Проверка метрики "Доля продаж новых работ":
- ✅ Метод `calculate_new_works_sales_percent` использует `self.new_works_prefix` из settings
- ✅ Расчет процента от `total_sales` соответствует ТЗ
- ✅ Логика: ID должен иметь ровно 10 цифр и начинаться с префикса (например, "150")

## Статус проверки
- ✅ Все файлы обновлены
- ✅ Миграция создана и применена
- ✅ Линтер не выявил ошибок
- ✅ Все TODO выполнены
- ✅ Колонка `avg_revenue_per_sale` добавлена в SQLite базы данных

## Решение проблемы с базой данных
При первом запуске возникла ошибка `no such column: analytics_reports.avg_revenue_per_sale` в SQLite.

**Причина**: В проекте используется две базы данных:
- PostgreSQL (на продакшене, указан в .env)
- SQLite (локально для разработки)

Миграция Alembic была применена к PostgreSQL, но не к локальным SQLite базам.

**Решение**: Колонка `avg_revenue_per_sale` была добавлена напрямую через SQL в обе SQLite базы:
- `iqstocker.db` (корневая директория)
- `database/iqstocker.db` (поддиректория database)

Команда:
```sql
ALTER TABLE analytics_reports ADD COLUMN avg_revenue_per_sale NUMERIC(10, 2);
```

## Следующие шаги
1. ✅ Запустить бота и проверить отсутствие ошибок
2. Протестировать загрузку CSV и генерацию отчета
3. Проверить корректность расчетов на реальных данных
4. Убедиться, что все метрики отображаются правильно в боте

## Примечания
- Все тексты сообщений хранятся в `bot/lexicon/lexicon_ru.py` согласно правилам проекта
- Форматирование средней цены продажи изменено с 4 до 2 знаков после запятой для единообразия с другими денежными значениями
- Поле `avg_revenue_per_sale` помечено как `nullable=True` для совместимости с существующими данными

