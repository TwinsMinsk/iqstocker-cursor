# Руководство по мульти-модельному LLM-сервису

## Обзор

Мульти-модельный LLM-сервис IQStocker предоставляет гибкую архитектуру для работы с различными языковыми моделями (OpenAI GPT-4o, Google Gemini 2.5 Flash-Lite, Anthropic Claude 3.5 Sonnet) для анализа и категоризации тем стокового контента.

## Архитектура

### Основные компоненты

```
core/ai/
├── llm_service.py          # Фабрика для создания провайдеров
├── prompts.py              # Централизованные промпты
└── providers/
    ├── base.py             # Абстрактный базовый класс
    ├── gemini_provider.py  # Google Gemini провайдер
    ├── openai_provider.py  # OpenAI провайдер
    └── claude_provider.py  # Anthropic Claude провайдер
```

### Модели базы данных

- **LLMSettings**: Хранение настроек провайдеров с шифрованием API-ключей
- **AssetDetails**: Кэш тегов ассетов Adobe Stock
- **TopTheme**: Результаты категоризации тем
- **GlobalTheme**: Агрегированная статистика тем

## Использование

### Базовое использование

```python
from core.ai.llm_service import LLMServiceFactory
from sqlalchemy.orm import Session

# Получение активного провайдера из БД
db = SessionLocal()
provider = LLMServiceFactory.get_active_provider(db)

# Категоризация тем
tags_by_asset = {
    "123": ["business", "office", "meeting"],
    "456": ["technology", "computer", "coding"]
}
sales_data = {
    "123": {"sales": 10, "revenue": 50.0},
    "456": {"sales": 5, "revenue": 25.0}
}

result = await provider.categorize_themes(tags_by_asset, sales_data)
print(f"Найдено тем: {len(result.themes)}")
print(f"Модель: {result.model_used}")
```

### Прямое создание провайдера

```python
from core.ai.providers import GeminiProvider

# Создание провайдера напрямую
provider = GeminiProvider(api_key="your-api-key")
result = await provider.categorize_themes(tags_by_asset, sales_data)
```

## Добавление нового провайдера

### 1. Создание класса провайдера

```python
# core/ai/providers/new_provider.py
from .base import AbstractLLMProvider, ThemeCategorizationResult

class NewProvider(AbstractLLMProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key, "new-model-name")
        # Инициализация клиента
    
    async def categorize_themes(self, tags_by_asset, sales_data):
        # Реализация категоризации
        pass
    
    async def generate_personal_themes(self, user_top_themes, count=5):
        # Реализация генерации тем
        pass
```

### 2. Обновление фабрики

```python
# core/ai/llm_service.py
from .providers.new_provider import NewProvider

class LLMServiceFactory:
    @staticmethod
    def _create_provider(provider_type: LLMProviderType, api_key: str):
        if provider_type == LLMProviderType.NEW:
            return NewProvider(api_key)
        # ... остальные провайдеры
```

### 3. Обновление модели БД

```python
# database/models/llm_settings.py
class LLMProviderType(str, Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    CLAUDE = "claude"
    NEW = "new"  # Добавить новый тип
```

### 4. Обновление админ-панели

```python
# admin/forms/llm_settings_form.py
provider = SelectField(
    'LLM Провайдер',
    choices=[
        ('gemini', 'Google Gemini 2.5 Flash-Lite'),
        ('openai', 'OpenAI GPT-4o'),
        ('claude', 'Anthropic Claude 3.5 Sonnet'),
        ('new', 'New Provider'),  # Добавить новый выбор
    ]
)
```

## Формат промптов

### Структура промптов

Все промпты находятся в `core/ai/prompts.py` и следуют единому формату:

```python
THEME_CATEGORIZATION_PROMPT = """
Ты эксперт по анализу стокового контента. Проанализируй теги от проданных работ и определи основные коммерческие темы.

ВХОДНЫЕ ДАННЫЕ:
{input_data}

ЗАДАЧА:
1. Для каждой работы определи 1-2 основные коммерческие темы
2. Объедини похожие темы
3. Агрегируй продажи и доход по темам

ФОРМАТ ОТВЕТА (строго JSON):
{
  "themes": [
    {
      "theme": "Business & Corporate",
      "sales": 45,
      "revenue": 123.50,
      "confidence": 0.95,
      "keywords": ["business", "office", "meeting"]
    }
  ]
}
"""
```

### Специфичные промпты для моделей

- **Gemini**: Использует `GEMINI_THEME_CATEGORIZATION_PROMPT` (английский)
- **OpenAI**: Использует `THEME_CATEGORIZATION_PROMPT` (русский)
- **Claude**: Использует `CLAUDE_THEME_CATEGORIZATION_PROMPT` (детальный английский)

## Безопасность

### Шифрование API-ключей

API-ключи шифруются с помощью Fernet (симметричное шифрование):

```python
# Генерация ключа шифрования
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Сохранить в ENCRYPTION_KEY
```

### Переменные окружения

```bash
# Один из ключей LLM
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Ключ шифрования для БД
ENCRYPTION_KEY=your_32_byte_base64_key
```

## Мониторинг и логирование

### Структурированное логирование

Все операции логируются с помощью `structlog`:

```python
logger.info(
    "llm_request_completed",
    provider="gemini-2.5-flash-lite",
    themes_count=5,
    processing_time_ms=1200
)
```

### Метрики в БД

- `requests_count`: Количество запросов к провайдеру
- `last_used_at`: Время последнего использования
- `processing_time_ms`: Время обработки запроса

## ⚠️ ВАЖНОЕ ОБНОВЛЕНИЕ

**Функция глубокого анализа тем была удалена из системы.**

Модули `workers/theme_actors.py` и `core/parser/adobe_stock_playwright.py` больше не существуют.

Топ-темы теперь берутся напрямую из CSV-файла без фоновой обработки через LLM и скрапинг Adobe Stock.

## Текущая функциональность LLM

LLM-сервис остается доступным для других функций системы, но больше не используется для анализа тем портфеля.

### Доступные провайдеры:
- Gemini (Google)
- OpenAI (GPT)
- Claude (Anthropic)

### Настройка через админ-панель:
1. Перейти на `/llm-settings`
2. Выбрать провайдера
3. Ввести API-ключ
4. Активировать провайдера

## Что было удалено

- ❌ Скрапинг тегов с Adobe Stock через Playwright
- ❌ LLM-категоризация тем портфеля
- ❌ Фоновые задачи Dramatiq для анализа тем
- ❌ Модуль `workers/theme_actors.py`
- ❌ Модуль `core/parser/adobe_stock_playwright.py`

## Тестирование

### Запуск тестов

```bash
# Все тесты LLM-сервиса
pytest tests/unit/test_llm_service.py -v

# Конкретный тест
pytest tests/unit/test_llm_service.py::TestGeminiProvider::test_categorize_themes_success -v
```

### Мокирование API

```python
# Пример мокирования Gemini API
mock_response = Mock()
mock_response.text = '{"themes": [...]}'

with patch.object(provider.model, 'generate_content_async', return_value=mock_response):
    result = await provider.categorize_themes(tags_by_asset, sales_data)
```

## Troubleshooting

### Частые проблемы

#### 1. "No active LLM provider configured"

**Причина**: В БД нет активного провайдера.

**Решение**: Настроить провайдера через админ-панель `/llm-settings`.

#### 2. "Failed to parse JSON response"

**Причина**: Модель вернула невалидный JSON.

**Решение**: 
- Проверить промпт на корректность
- Убедиться в правильности API-ключа
- Проверить лимиты API

#### 3. "ENCRYPTION_KEY environment variable not set"

**Причина**: Не установлена переменная окружения для шифрования.

**Решение**: Добавить `ENCRYPTION_KEY` в `.env` файл.

#### 4. Ошибки скрапинга Adobe Stock

**Причина**: Изменение структуры сайта или блокировка IP.

**Решение**:
- Обновить селекторы в парсере
- Использовать прокси
- Проверить User-Agent

### Логи для отладки

```python
# Включить детальное логирование
import structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

## Производительность

### Оптимизация запросов

1. **Кэширование**: Теги ассетов кэшируются в БД
2. **Батчинг**: Обработка нескольких ассетов за один запрос
3. **Асинхронность**: Все операции выполняются асинхронно
4. **Таймауты**: Установлены разумные таймауты для API

### Мониторинг производительности

```python
# Время обработки запроса
processing_time_ms = int((time.time() - start_time) * 1000)

# Количество обработанных ассетов
total_processed = len(tags_by_asset)

# Статистика использования
settings.requests_count += 1
settings.last_used_at = datetime.utcnow()
```

## Расширение функциональности

### Добавление новых методов

```python
class AbstractLLMProvider(ABC):
    @abstractmethod
    async def analyze_trends(self, data: Dict) -> Dict:
        """Анализ трендов."""
        pass
    
    @abstractmethod
    async def generate_keywords(self, theme: str) -> List[str]:
        """Генерация ключевых слов для темы."""
        pass
```

### Интеграция с другими сервисами

```python
# Интеграция с аналитикой
from core.analytics.advanced_csv_processor import AdvancedCSVProcessor

processor = AdvancedCSVProcessor()
result = processor.process_csv(csv_path)

# Запуск LLM-анализа
provider = LLMServiceFactory.get_active_provider(db)
themes = await provider.categorize_themes(tags_by_asset, sales_data)
```

## Заключение

Мульти-модельный LLM-сервис предоставляет гибкую и расширяемую архитектуру для работы с различными языковыми моделями. Система поддерживает:

- Легкое переключение между провайдерами
- Безопасное хранение API-ключей
- Централизованное управление через админ-панель
- Структурированное логирование и мониторинг
- Асинхронную обработку в фоновых задачах
- Кэширование для оптимизации производительности

Для получения дополнительной информации обращайтесь к исходному коду или создавайте issues в репозитории проекта.
