# Процедура тестирования модуля "Топ тем"

## Подготовка

1. **Активировать виртуальное окружение**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

2. **Убедиться, что Dramatiq workers запущены**
   ```bash
   python scripts/start_workers.py
   ```

3. **Иметь тестовый CSV-файл с данными продаж**
   - Файл должен содержать колонки: `Asset ID`, `Title`, `Sales`, `Revenue`
   - Пример файла: `uploads/test_final_analysis.csv`

4. **Настроить прокси (опционально)**
   - Отредактировать файл `proxies.txt`
   - Добавить прокси в формате: `http://user:pass@host:port`
   - Один прокси на строку, комментарии начинаются с `#`

## Шаг 1: Запуск пайплайна

### Создание CSV анализа через админку:
1. Открыть админку: `http://localhost:8000/admin`
2. Перейти в раздел "CSV Analysis"
3. Загрузить тестовый CSV-файл
4. Запустить анализ

### Или программно:
```python
from workers.theme_actors import scrape_and_categorize_themes

# Замените <ID> на реальный ID анализа
csv_analysis_id = 1
scrape_and_categorize_themes.send(csv_analysis_id)
```

## Шаг 2: Мониторинг логов

Следить за логами в `logs/bot.log` или консоли Dramatiq worker:

### Основные события пайплайна:
- `theme_pipeline_started` - начало обработки с параметрами пользователя
- `top_assets_extracted` - извлечение топ-ассетов из CSV
- `asset_scraping_started` - начало скрапинга каждого ассета
- `using_proxy` - использование прокси (если настроено)
- `scraping_initiated` - инициализация скрапинга с URL
- `page_response_received` - получение ответа от страницы
- `tags_extraction_strategy_success` - успешное извлечение тегов
- `asset_tags_scraped` - успешный скрапинг тегов с образцом
- `llm_request_prepared` - подготовка запроса к LLM
- `llm_categorization_success` - успешная категоризация тем
- `top_themes_saved` - сохранение результатов в БД
- `global_themes_update_started` - начало обновления глобальной базы
- `global_theme_created` / `global_theme_updated` - создание/обновление тем
- `global_theme_delta` - детали изменений в глобальных темах

### Пример успешного лога:
```
2024-01-15 10:30:01 INFO theme_pipeline_started csv_analysis_id=1 user_id=123 file_path=uploads/test.csv
2024-01-15 10:30:02 INFO top_assets_extracted csv_analysis_id=1 count=10
2024-01-15 10:30:03 DEBUG asset_scraping_started asset_id=12345 title="Business Meeting" url=https://stock.adobe.com/images/business-meeting/12345
2024-01-15 10:30:04 INFO using_proxy asset_id=12345 proxy=proxy.example.com:8080
2024-01-15 10:30:05 INFO scraping_initiated asset_id=12345 url=https://... user_agent=Mozilla/5.0...
2024-01-15 10:30:06 DEBUG page_response_received asset_id=12345 status=200 content_type=text/html
2024-01-15 10:30:07 DEBUG tags_extraction_strategy_success strategy=data-testid tags_found=8 tags_sample=["business", "meeting", "office"]
2024-01-15 10:30:08 INFO asset_tags_scraped asset_id=12345 tags_count=8 tags_sample=["business", "meeting", "office", "corporate", "team"]
2024-01-15 10:30:10 DEBUG llm_request_prepared provider=GeminiProvider assets_count=10 total_tags=85 total_sales=1500 total_revenue=4500.00
2024-01-15 10:30:15 INFO llm_categorization_success themes_count=5 themes_list=["Business Technology", "Corporate Lifestyle", "Office Environment"] model=gemini-1.5-pro processing_ms=4500
2024-01-15 10:30:16 INFO top_themes_saved csv_analysis_id=1 themes_saved=5 top_theme="Business Technology"
2024-01-15 10:30:17 INFO global_themes_update_started csv_analysis_id=1
2024-01-15 10:30:18 INFO global_theme_created theme_name="Business Technology" sales=300 revenue=900.00
2024-01-15 10:30:19 DEBUG global_theme_delta theme_name="Business Technology" sales_added=300 revenue_added=900.00 new_total_sales=300 new_total_revenue=900.00
```

## Шаг 3: Проверка результатов в БД

### Проверка TopTheme:

```sql
SELECT * FROM top_themes WHERE csv_analysis_id = <ID> ORDER BY rank;
```

**Проверить:**
- Корректные названия тем (не пустые, осмысленные)
- Ранжирование (rank от 1 до N, без пропусков)
- Суммы продаж и доходов (положительные числа)
- Связь с правильным csv_analysis_id

### Проверка GlobalTheme:

```sql
SELECT theme_name, total_sales, total_revenue, authors_count, last_updated 
FROM global_themes 
WHERE theme_name IN (SELECT theme_name FROM top_themes WHERE csv_analysis_id = <ID>);
```

**Проверить:**
- **Анонимность**: нет привязки к конкретному пользователю
- **Агрегация**: значения соответствуют данным из TopTheme
- **authors_count >= 1**: минимум один автор для каждой темы
- **last_updated**: время обновления актуальное

### Проверка AssetDetails (кеш):

```sql
SELECT asset_id, title, tags, scraped_at, adobe_url 
FROM asset_details 
WHERE asset_id IN (SELECT DISTINCT asset_id FROM csv_analyses WHERE id = <ID>);
```

**Проверить:**
- Теги извлечены и сохранены
- URL корректно сформированы
- Время скрапинга актуальное

## Шаг 4: Повторный запуск для проверки агрегации

### Тест агрегации данных:

1. **Запустить пайплайн для другого пользователя** с пересекающимися темами
2. **Проверить, что в GlobalTheme:**
   - `total_sales` и `total_revenue` увеличились
   - `authors_count` увеличился на 1
   - `last_updated` обновился

### Пример тестового сценария:

```python
# Первый запуск
csv_analysis_id_1 = 1  # Пользователь A, темы: ["Business", "Nature"]
scrape_and_categorize_themes.send(csv_analysis_id_1)

# Второй запуск
csv_analysis_id_2 = 2  # Пользователь B, темы: ["Business", "Technology"]
scrape_and_categorize_themes.send(csv_analysis_id_2)

# Проверка агрегации
# Тема "Business" должна иметь authors_count=2
# Тема "Nature" должна иметь authors_count=1
# Тема "Technology" должна иметь authors_count=1
```

## Шаг 5: Проверка обработки ошибок

### Тест с невалидными данными:

1. **CSV без обязательных колонок**
2. **Пустой CSV файл**
3. **Ассеты с невалидными ID**
4. **Отсутствие LLM провайдера**

### Ожидаемое поведение:
- Логирование ошибок с подробностями
- Graceful degradation (не падение системы)
- Корректное обновление статуса анализа

## Шаг 6: Проверка производительности

### Мониторинг метрик:

1. **Время выполнения пайплайна** (цель: < 10 минут для 10 ассетов)
2. **Использование памяти** (цель: стабильное потребление)
3. **Количество запросов к Adobe Stock** (цель: минимизация)
4. **Успешность скрапинга** (цель: > 80%)

### Команды для мониторинга:

```bash
# Проверка логов на ошибки
grep -i "error\|failed" logs/bot.log

# Подсчет успешных скрапингов
grep -c "asset_tags_scraped" logs/bot.log

# Проверка времени выполнения
grep "theme_pipeline_started\|theme_categorization_completed" logs/bot.log
```

## Устранение неполадок

### Частые проблемы:

1. **"No active LLM provider configured"**
   - Решение: Настроить LLM провайдера в админке

2. **"proxy_file_not_found"**
   - Решение: Создать файл `proxies.txt` или оставить пустым

3. **"scraping_asset_failed"**
   - Решение: Проверить доступность Adobe Stock, настроить прокси

4. **"llm_categorization_failed"**
   - Решение: Проверить API ключи, лимиты провайдера

### Команды диагностики:

```bash
# Проверка статуса workers
ps aux | grep dramatiq

# Проверка подключения к БД
python -c "from config.database import SessionLocal; print('DB OK')"

# Проверка настроек
python -c "from config.settings import settings; print(f'Proxy file: {settings.proxy_file}')"
```

## Заключение

После успешного прохождения всех шагов модуль "Топ тем" готов к продакшену:

✅ **Расширенное логирование** - полная прозрачность процесса  
✅ **Unit-тесты** - проверенная логика агрегации  
✅ **Поддержка прокси** - защита от блокировок  
✅ **Документация** - четкие процедуры тестирования  

Система обеспечивает надежную работу в продакшене с возможностью детальной отладки.
