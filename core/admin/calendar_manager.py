"""Calendar manager with AI generation and manual control."""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from database.models import CalendarEntry
from config.database import SessionLocal
import openai
from config.settings import settings


class CalendarManager:
    """Manages calendar entries with AI generation and manual editing."""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        """Close database session."""
        if hasattr(self, 'db'):
            self.db.close()
    
    async def generate_calendar_for_month(
        self, 
        month: int, 
        year: int,
        use_ai: bool = True
    ) -> CalendarEntry:
        """Generate calendar entry using AI or templates."""
        
        if use_ai and settings.openai_api_key:
            return await self._generate_with_ai(month, year)
        else:
            return self._generate_from_template(month, year)
    
    async def _generate_with_ai(self, month: int, year: int) -> CalendarEntry:
        """Generate calendar using AI."""
        
        month_name = self._get_month_name_ru(month)
        
        prompt = f"""
        Create a seasonal stock photography calendar for {month_name} {year}.
        
        Provide:
        1. Season description (2-3 sentences in Russian)
        2. 4-5 themes to upload NOW (current hot topics)
        3. 4-5 themes to PREPARE (will be relevant in 1-2 months)
        
        Format as JSON:
        {{
            "description": "...",
            "load_now": ["theme1", "theme2", ...],
            "prepare": ["theme1", "theme2", ...]
        }}
        
        Consider: holidays, seasons, market trends, cultural events.
        All text in Russian with emojis.
        """
        
        try:
            client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a stock photography market expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            data = json.loads(response.choices[0].message.content)
            
            return CalendarEntry(
                month=month,
                year=year,
                description=data["description"],
                load_now_themes=data["load_now"],
                prepare_themes=data["prepare"],
                source='ai',
                created_at=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            print(f"Error generating calendar with AI: {e}")
            # Fallback to template
            return self._generate_from_template(month, year)
    
    def _generate_from_template(self, month: int, year: int) -> CalendarEntry:
        """Generate calendar from predefined templates."""
        
        description = self._get_season_description(month)
        load_now_themes = self._get_load_now_themes(month)
        prepare_themes = self._get_prepare_themes(month)
        
        return CalendarEntry(
            month=month,
            year=year,
            description=description,
            load_now_themes=load_now_themes,
            prepare_themes=prepare_themes,
            source='template',
            created_at=datetime.now(timezone.utc)
        )
    
    def update_calendar_entry(
        self,
        entry_id: int,
        description: Optional[str] = None,
        load_now_themes: Optional[List[str]] = None,
        prepare_themes: Optional[List[str]] = None
    ) -> bool:
        """Manually update calendar entry."""
        
        entry = self.db.query(CalendarEntry).filter(
            CalendarEntry.id == entry_id
        ).first()
        
        if not entry:
            return False
        
        if description:
            entry.description = description
        if load_now_themes:
            entry.load_now_themes = load_now_themes
        if prepare_themes:
            entry.prepare_themes = prepare_themes
        
        # Mark as manually edited
        entry.source = 'manual'
        
        self.db.commit()
        return True
    
    def get_calendar_entry(self, month: int, year: int) -> Optional[CalendarEntry]:
        """Get calendar entry for specific month and year."""
        
        return self.db.query(CalendarEntry).filter(
            CalendarEntry.month == month,
            CalendarEntry.year == year
        ).order_by(CalendarEntry.created_at.desc()).first()
    
    def list_calendar_entries(self, limit: int = 12) -> List[CalendarEntry]:
        """List recent calendar entries."""
        
        return self.db.query(CalendarEntry).order_by(
            CalendarEntry.year.desc(),
            CalendarEntry.month.desc()
        ).limit(limit).all()
    
    def _get_month_name_ru(self, month: int) -> str:
        """Get Russian month name."""
        months = {
            1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
            5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
            9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
        }
        return months.get(month, "Неизвестный месяц")
    
    def _get_season_description(self, month: int) -> str:
        """Get season description based on month."""
        if month in [12, 1, 2]:
            return "Зима — время уютных сюжетов, праздников и зимних активностей. Идеально для создания атмосферных работ."
        elif month in [3, 4, 5]:
            return "Весна — период обновления и роста. Отличное время для съемки природы, новых начинаний и весенних праздников."
        elif month in [6, 7, 8]:
            return "Лето — горячий сезон для стоков! Много активностей на свежем воздухе, отпусков и летних праздников."
        else:  # 9, 10, 11
            return "Осень — горячий сезон для стоков: много праздников, уютных сюжетов и первых зимних заготовок."
    
    def _get_load_now_themes(self, month: int) -> List[str]:
        """Get themes to load now based on month."""
        themes_by_month = {
            1: ["🎄 Новогодние праздники", "❄️ Зимние сцены", "🏔️ Зимний спорт", "☕ Уютные моменты"],
            2: ["💝 День Святого Валентина", "❄️ Зимние пейзажи", "🏠 Домашний уют", "📚 Образование"],
            3: ["🌸 Весенние сцены", "🌱 Природа пробуждается", "🎓 Выпускные", "🏃 Весенние активности"],
            4: ["🐰 Пасха", "🌸 Весенние цветы", "🌱 Садоводство", "🏃 Весенний спорт"],
            5: ["👩 День матери", "🌸 Весенние праздники", "🌱 Садоводство", "🏃 Весенние активности"],
            6: ["👨 День отца", "☀️ Летние сцены", "🏖️ Отпуск", "🌻 Летние цветы"],
            7: ["🇺🇸 День независимости", "☀️ Летние активности", "🏖️ Пляж", "🌻 Летние праздники"],
            8: ["🏖️ Летний отдых", "☀️ Летние сцены", "🌻 Летние цветы", "🏃 Летний спорт"],
            9: ["🎓 Начало учебного года", "🍂 Осенние сцены", "🍎 Сбор урожая", "🏃 Осенние активности"],
            10: ["🎃 Хэллоуин", "🍂 Осенние сцены", "🍎 Сбор урожая", "🛍️ Осенние распродажи"],
            11: ["🦃 День благодарения", "🍂 Осенние сцены", "🛍️ Черная пятница", "🍎 Сбор урожая"],
            12: ["🎄 Рождество", "❄️ Зимние сцены", "🎁 Подарки", "☕ Праздничная атмосфера"]
        }
        return themes_by_month.get(month, ["🎯 Общие темы"])
    
    def _get_prepare_themes(self, month: int) -> List[str]:
        """Get themes to prepare for next 1-2 months."""
        themes_by_month = {
            1: ["💝 День Святого Валентина", "🌸 Весенние сцены", "🎓 Образование", "🌱 Природа"],
            2: ["🌸 Весенние сцены", "🐰 Пасха", "🌱 Садоводство", "🏃 Весенние активности"],
            3: ["🐰 Пасха", "🌸 Весенние цветы", "🌱 Садоводство", "👩 День матери"],
            4: ["👩 День матери", "🌸 Весенние праздники", "🌱 Садоводство", "👨 День отца"],
            5: ["👨 День отца", "☀️ Летние сцены", "🏖️ Отпуск", "🌻 Летние цветы"],
            6: ["☀️ Летние активности", "🏖️ Пляж", "🌻 Летние праздники", "🇺🇸 День независимости"],
            7: ["🏖️ Летний отдых", "☀️ Летние сцены", "🌻 Летние цветы", "🎓 Начало учебного года"],
            8: ["🎓 Начало учебного года", "🍂 Осенние сцены", "🍎 Сбор урожая", "🎃 Хэллоуин"],
            9: ["🎃 Хэллоуин", "🍂 Осенние сцены", "🦃 День благодарения", "🛍️ Черная пятница"],
            10: ["🦃 День благодарения", "🛍️ Черная пятница", "🎄 Рождество", "❄️ Зимние сцены"],
            11: ["🎄 Рождество", "❄️ Зимние сцены", "🎁 Подарки", "☕ Праздничная атмосфера"],
            12: ["💝 День Святого Валентина", "❄️ Зимние сцены", "🏔️ Зимний спорт", "☕ Уютные моменты"]
        }
        return themes_by_month.get(month, ["🎯 Общие темы"])
