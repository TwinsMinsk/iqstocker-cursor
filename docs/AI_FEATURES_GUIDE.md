# IQStocker Bot - AI Features Guide

## Обзор новых AI функций

IQStocker Bot теперь включает продвинутые AI функции для анализа портфолио, прогнозирования продаж и персонализированных рекомендаций.

## 🚀 Новые возможности

### 1. Прогнозирование продаж (SalesPredictor)
- **Прогноз продаж на следующий месяц** с использованием машинного обучения
- **Анализ трендов роста** для выявления паттернов развития
- **Рекомендации по стратегии загрузки** на основе исторических данных
- **Сезонный анализ** для понимания сезонных колебаний

### 2. Персонализированные рекомендации (RecommendationEngine)
- **Умные рекомендации тем** на основе успешных работ пользователя
- **Анализ поведения пользователя** для создания профиля предпочтений
- **Поиск похожих пользователей** для групповых инсайтов
- **Анализ паттернов успеха** для выявления факторов успеха

### 3. Анализ рынка (MarketAnalyzer)
- **Глобальные тренды** на основе данных всех пользователей
- **Сезонный анализ** популярных тем по месяцам
- **Прогнозирование будущих трендов** с использованием кластеризации
- **Обзор рынка** с метриками здоровья индустрии

### 4. Расширенная аналитика (AdvancedMetrics)
- **ROI по темам** - доходность инвестиций в каждую тему
- **Conversion rates** новых vs старых работ
- **Portfolio diversity index** - индекс разнообразия портфолио
- **Time-to-sale метрики** - время до первой продажи
- **Revenue per upload** - доходность на загрузку

### 5. Benchmark система (BenchmarkEngine)
- **Сравнение с индустриальными стандартами**
- **Percentile ranking** - позиция пользователя среди всех
- **Benchmark по типам подписки** для справедливого сравнения
- **Отслеживание целей** с прогрессом выполнения

## 🔧 Технические компоненты

### AI Infrastructure
- **AICacheManager** - кэширование результатов AI для производительности
- **AIRateLimiter** - контроль лимитов API запросов
- **AIPerformanceMonitor** - мониторинг производительности AI

### Database Optimizations
- **PostgreSQL оптимизация** с правильными pool settings
- **Композитные индексы** для быстрых запросов
- **Health monitoring** для отслеживания состояния БД

## 📊 API Endpoints

### AI Performance
- `GET /api/ai/performance` - метрики производительности AI
- `GET /api/ai/cache/status` - статус кэша
- `GET /api/ai/rate-limits` - статус лимитов

### AI Analytics
- `GET /api/ai/predictions/{user_id}` - прогнозы для пользователя
- `GET /api/ai/recommendations/{user_id}` - рекомендации для пользователя
- `GET /api/ai/market-trends` - текущие тренды рынка
- `GET /api/ai/market-overview` - обзор рынка

### Advanced Analytics
- `GET /api/advanced/metrics/{user_id}` - расширенные метрики
- `GET /api/benchmark/user/{user_id}` - сравнение с бенчмарками
- `GET /api/benchmark/industry` - индустриальные бенчмарки
- `GET /api/benchmark/subscription/{type}` - бенчмарки по подписке

### AI Management
- `POST /api/ai/cache/clear` - очистка кэша
- `POST /api/ai/rate-limits/clear` - сброс лимитов
- `GET /api/ai/queue/status` - статус очереди запросов
- `GET /api/ai/costs/summary` - сводка по затратам

## 🎯 Использование в Bot

### Analytics Handler
```python
# Генерация расширенного отчета с AI инсайтами
report_generator = ReportGenerator()
enhanced_report = await report_generator.generate_enhanced_report(
    csv_analysis_id, sales_data, portfolio_size, 
    upload_limit, monthly_uploads, acceptance_rate
)

# Отчет включает:
# - Базовые метрики
# - AI прогнозы и инсайты
# - Advanced метрики
# - Benchmark сравнения
```

### Themes Handler
```python
# Генерация персонализированных тем с AI
theme_manager = EnhancedThemeManager()
themes = await theme_manager.generate_weekly_themes(
    user_id, subscription_type, count=5
)

# Темы включают:
# - Источник (personal/trending/seasonal)
# - Уровень уверенности
# - Объяснение рекомендации
# - Прогнозируемая производительность
```

## 🔍 Мониторинг и отладка

### AI Performance Monitoring
```python
monitor = AIPerformanceMonitor()
performance = monitor.get_performance_summary("openai", 24)

# Метрики включают:
# - Время ответа
# - Success rate
# - Error rate
# - Cost per request
# - Throughput
```

### Cache Management
```python
cache_manager = AICacheManager()
stats = cache_manager.get_cache_statistics()

# Статистика включает:
# - Общее количество кэшированных элементов
# - Распределение по типам
# - Hit rate
# - Использование памяти
```

### Rate Limiting
```python
rate_limiter = AIRateLimiter()
status = rate_limiter.get_rate_limit_status("openai")

# Статус включает:
# - Текущие лимиты
# - Оставшиеся запросы
# - Время сброса
# - Статус очереди
```

## 🚀 Production Deployment

### Environment Variables
```bash
# AI Configuration
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Database (PostgreSQL for production)
DATABASE_URL=postgresql://user:pass@host:port/db

# Redis for caching
REDIS_URL=redis://host:port/db

# Rate Limiting
AI_RATE_LIMIT_PER_MINUTE=60
AI_RATE_LIMIT_PER_HOUR=1000
```

### Docker Configuration
```dockerfile
# Оптимизированный Dockerfile для production
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python healthcheck.py

# Run application
CMD ["python", "bot/main.py"]
```

## 📈 Метрики и KPI

### AI Performance KPIs
- **Response Time**: < 2 секунды для AI запросов
- **Success Rate**: > 95% успешных AI операций
- **Cache Hit Rate**: > 80% для часто используемых данных
- **Cost per Request**: < $0.01 за AI запрос

### Business KPIs
- **Prediction Accuracy**: точность прогнозов продаж
- **Recommendation Relevance**: релевантность рекомендаций тем
- **User Engagement**: увеличение использования AI функций
- **Revenue Impact**: влияние AI на доходы пользователей

## 🧪 Тестирование

### Unit Tests
```bash
# Запуск тестов AI компонентов
pytest tests/test_ai_components.py -v

# Запуск интеграционных тестов
pytest tests/test_ai_integration.py -v
```

### Test Coverage
- **SalesPredictor**: тестирование прогнозов и трендов
- **RecommendationEngine**: тестирование рекомендаций
- **MarketAnalyzer**: тестирование анализа рынка
- **AdvancedMetrics**: тестирование расширенных метрик
- **BenchmarkEngine**: тестирование сравнений

## 🔧 Troubleshooting

### Common Issues

1. **AI API Rate Limits**
   - Проверьте статус лимитов: `GET /api/ai/rate-limits`
   - Очистите лимиты для тестирования: `POST /api/ai/rate-limits/clear`

2. **Cache Issues**
   - Проверьте статус кэша: `GET /api/ai/cache/status`
   - Очистите кэш: `POST /api/ai/cache/clear`

3. **Performance Issues**
   - Проверьте метрики производительности: `GET /api/ai/performance`
   - Мониторьте время ответа и success rate

4. **Database Connection**
   - Проверьте health check: `GET /health`
   - Убедитесь в правильности DATABASE_URL

### Debug Mode
```python
# Включение debug режима для AI компонентов
import logging
logging.basicConfig(level=logging.DEBUG)

# Детальное логирование AI операций
from core.ai.sales_predictor import SalesPredictor
predictor = SalesPredictor()
prediction = predictor.predict_next_month_sales(user_id)
```

## 📚 Дополнительные ресурсы

- [AI Components API Reference](docs/ai_api_reference.md)
- [Database Schema](docs/database_schema.md)
- [Deployment Guide](docs/deployment_guide.md)
- [Performance Tuning](docs/performance_tuning.md)

## 🤝 Поддержка

Для вопросов по AI функциям обращайтесь к:
- Техническая документация: `/docs` endpoint
- API документация: `/admin/docs` (требует авторизации)
- Логи системы: `logs/` директория
