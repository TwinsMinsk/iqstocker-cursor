"""LLM Settings form for admin panel."""

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


class LLMSettingsForm(FlaskForm):
    """Form for LLM provider settings."""
    
    provider = SelectField(
        'LLM Провайдер',
        choices=[
            ('gemini', 'Google Gemini 2.5 Flash-Lite'),
            ('openai', 'OpenAI GPT-4o'),
            ('claude', 'Anthropic Claude 3.5 Sonnet')
        ],
        validators=[DataRequired()],
        description="Выберите провайдера для анализа тем"
    )
    
    api_key = StringField(
        'API Key',
        validators=[DataRequired(), Length(min=10, max=200)],
        render_kw={
            "type": "password", 
            "placeholder": "sk-... или AIza...",
            "class": "form-control"
        },
        description="API ключ для выбранного провайдера"
    )
    
    submit = SubmitField(
        'Сохранить и активировать',
        render_kw={"class": "btn btn-primary"}
    )
