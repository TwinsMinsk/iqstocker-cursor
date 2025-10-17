"""Centralized prompts for LLM providers."""

THEME_CATEGORIZATION_PROMPT = """
Ты эксперт по анализу стокового контента. Проанализируй теги от проданных работ и определи основные коммерческие темы.

ВХОДНЫЕ ДАННЫЕ:
{input_data}

ЗАДАЧА:
1. Для каждой работы определи 1-2 основные коммерческие темы
2. Объедини похожие темы (например, "Business Meeting" и "Corporate Office" → "Business & Corporate")
3. Агрегируй продажи и доход по темам

ФОРМАТ ОТВЕТА (строго JSON):
{{
  "themes": [
    {{
      "theme": "Business & Corporate",
      "sales": 45,
      "revenue": 123.50,
      "confidence": 0.95,
      "keywords": ["business", "office", "meeting"]
    }}
  ]
}}

ПРАВИЛА:
- Темы должны быть широкими и коммерчески привлекательными
- Используй английские названия
- Сортируй по revenue (убывание)
- Максимум 10 тем
- Убедись, что JSON валидный
"""

PERSONAL_THEMES_PROMPT = """
На основе успешных тем пользователя: {user_themes}

Сгенерируй {count} новых тем, которые:
1. Логически связаны с успешными темами
2. Учитывают текущие сезонные тренды
3. Имеют высокий коммерческий потенциал

Формат ответа (JSON):
{{
  "themes": ["Theme 1", "Theme 2", ...]
}}

ПРАВИЛА:
- Используй английские названия
- Темы должны быть конкретными и actionable
- Учитывай сезонность (осень 2025)
- Максимум {count} тем
"""

# Gemini-specific prompts (more structured)
GEMINI_THEME_CATEGORIZATION_PROMPT = """
You are a stock photography expert. Analyze the tags from sold works and identify main commercial themes.

INPUT DATA:
{input_data}

TASK:
1. For each work, identify 1-2 main commercial themes
2. Group similar themes (e.g., "Business Meeting" and "Corporate Office" → "Business & Corporate")
3. Aggregate sales and revenue by themes

RESPONSE FORMAT (strict JSON):
{{
  "themes": [
    {{
      "theme": "Business & Corporate",
      "sales": 45,
      "revenue": 123.50,
      "confidence": 0.95,
      "keywords": ["business", "office", "meeting"]
    }}
  ]
}}

RULES:
- Themes should be broad and commercially attractive
- Use English names
- Sort by revenue (descending)
- Maximum 10 themes
- Ensure valid JSON format
"""

# Claude-specific prompts (more detailed)
CLAUDE_THEME_CATEGORIZATION_PROMPT = """
You are an expert stock photography analyst. Your task is to analyze asset tags and sales data to identify the most profitable commercial themes.

INPUT DATA:
{input_data}

ANALYSIS REQUIREMENTS:
1. Identify 1-2 primary commercial themes for each asset
2. Group similar themes together (e.g., "Business Meeting" + "Corporate Office" = "Business & Corporate")
3. Calculate aggregated sales and revenue for each theme
4. Provide confidence scores based on data quality

OUTPUT FORMAT (valid JSON only):
{{
  "themes": [
    {{
      "theme": "Business & Corporate",
      "sales": 45,
      "revenue": 123.50,
      "confidence": 0.95,
      "keywords": ["business", "office", "meeting"]
    }}
  ]
}}

QUALITY STANDARDS:
- Themes must be commercially viable and broad
- Use professional English terminology
- Sort themes by revenue (highest first)
- Maximum 10 themes
- Confidence scores: 0.0-1.0
- Keywords: 3-5 most relevant terms per theme
"""
