"""Advanced CSV processor based on iqstocker_process_csv.py."""

import json
import os
import re
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import pandas as pd

# Expected columns for Adobe Stock CSV
EXPECTED_COLS = [
    "sale_datetime_utc",  # ISO8601 UTC: 2025-07-31T23:08:22+00:00
    "asset_id",           # int-like ID as string
    "asset_title",        # text
    "license_plan",       # {'custom','subscription'}
    "royalty_usd",        # currency like "$0.99" -> 0.99
    "media_type",         # {'photos','videos','illustrations'}
    "filename",           # text
    "contributor_name",   # short text (e.g. 'HelenP')
    "size_label",         # {'XXL','HD1080'} (может расширяться)
]

ALLOWED_LICENSE = {"custom", "subscription"}
ALLOWED_MEDIA = {"photos", "videos", "illustrations"}

# Порог брака (битые строки) — 20%
BROKEN_ROWS_THRESHOLD_PCT = 20.0


@dataclass
class AdvancedProcessResult:
    """Advanced processing result with detailed metrics."""
    
    # Основные метрики
    period_month: str
    period_human_ru: str
    rows_total: int
    broken_rows: int
    broken_pct: float
    rows_used: int
    total_revenue_usd: float
    unique_assets_sold: int
    avg_revenue_per_sale: float
    date_min_utc: Optional[str]
    date_max_utc: Optional[str]
    
    # Разрезы
    sales_by_license: pd.DataFrame
    sales_by_media_type: pd.DataFrame
    
    # Топы
    top10_by_revenue: pd.DataFrame
    top10_by_sales: pd.DataFrame
    
    # Дополнительные метрики для бота
    portfolio_sold_percent: float
    new_works_sales_percent: float
    acceptance_rate: float
    upload_limit_usage: float


class AdvancedCSVProcessor:
    """Advanced CSV processor for Adobe Stock analytics."""
    
    def __init__(self):
        from config.settings import settings
        self.new_works_months = getattr(settings, 'new_works_months', 3)
    
    def _to_amount(self, series: pd.Series) -> pd.Series:
        """Очистка валюты до float."""
        s = series.astype(str)
        s = s.str.replace(r"(USD|EUR|PLN|RUB|RUR|₽|€|\$|zł|руб\.?)", "", regex=True, flags=re.IGNORECASE)
        s = s.str.replace(r"\s", "", regex=True)
        s = s.str.replace(",", ".", regex=False)
        return pd.to_numeric(s, errors="coerce")
    
    def _month_human_ru(self, year: int, month: int) -> str:
        """Конвертация месяца в русский формат."""
        months = {
            1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
            5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
            9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
        }
        return f"{months[month]} {year}"
    
    def _read_and_normalize(self, path: str) -> pd.DataFrame:
        """Читает и нормализует CSV файл."""
        try:
            # Сначала попробуем прочитать как есть
            df = pd.read_csv(
                path,
                encoding="utf-8",
                sep=",",
                header=None,
                names=EXPECTED_COLS,
                engine="python"
            )
        except Exception:
            # Если не получилось, попробуем с заголовком
            df = pd.read_csv(
                path,
                encoding="utf-8",
                sep=",",
                engine="python"
            )
            
            # Проверим, есть ли нужные колонки
            if not all(col in df.columns for col in EXPECTED_COLS):
                # Если колонок нет, попробуем стандартный формат Adobe Stock
                standard_cols = ['Title', 'Asset ID', 'Sales', 'Revenue']
                if all(col in df.columns for col in standard_cols):
                    # Конвертируем в наш формат
                    df = self._convert_standard_format(df)
                else:
                    raise ValueError("Не удалось определить формат CSV файла")
        
        # Нормализация типов
        if 'sale_datetime_utc' in df.columns:
            df["sale_datetime_utc"] = pd.to_datetime(df["sale_datetime_utc"], utc=True, errors="coerce")
        
        if 'asset_id' in df.columns:
            df["asset_id"] = df["asset_id"].astype(str).str.strip()
        
        if 'royalty_usd' in df.columns:
            df["royalty_usd"] = self._to_amount(df["royalty_usd"])
        
        # Нормализация категорий
        for c in ["license_plan", "media_type", "size_label", "contributor_name"]:
            if c in df.columns:
                df[c] = df[c].astype(str).str.strip().str.lower()
        
        # Нормализация текстов
        for c in ["asset_title", "filename"]:
            if c in df.columns:
                df[c] = df[c].astype(str).str.strip()
        
        return df
    
    def _convert_standard_format(self, df: pd.DataFrame) -> pd.DataFrame:
        """Конвертирует стандартный формат Adobe Stock в наш формат."""
        
        # Создаем новый DataFrame с нашими колонками
        new_df = pd.DataFrame()
        
        # Маппинг колонок
        if 'Title' in df.columns:
            new_df['asset_title'] = df['Title']
        if 'Asset ID' in df.columns:
            new_df['asset_id'] = df['Asset ID'].astype(str)
        if 'Sales' in df.columns:
            # Создаем строки для каждой продажи
            sales_data = []
            for _, row in df.iterrows():
                sales_count = int(row['Sales']) if pd.notna(row['Sales']) else 0
                for i in range(sales_count):
                    sales_data.append({
                        'asset_title': row.get('Title', ''),
                        'asset_id': str(row.get('Asset ID', '')),
                        'royalty_usd': float(row.get('Revenue', 0)) / sales_count if sales_count > 0 else 0,
                        'sale_datetime_utc': datetime.utcnow(),  # Примерная дата
                        'license_plan': 'custom',  # По умолчанию
                        'media_type': 'photos',    # По умолчанию
                        'filename': row.get('Title', ''),
                        'contributor_name': 'user',
                        'size_label': 'standard'
                    })
            
            new_df = pd.DataFrame(sales_data)
        
        return new_df
    
    def _validate_month(self, df: pd.DataFrame) -> Tuple[str, str]:
        """Проверка одного календарного месяца."""
        if 'sale_datetime_utc' not in df.columns or df['sale_datetime_utc'].isna().all():
            # Если нет дат, используем текущий месяц
            now = datetime.utcnow()
            period_month = f"{now.year}-{now.month:02d}-01"
            human = self._month_human_ru(now.year, now.month)
            return period_month, human
        
        try:
            # Convert to period, handling timezone issues
            periods = df["sale_datetime_utc"].dt.tz_localize(None).dt.to_period("M").astype(str).unique().tolist()
            if len(periods) != 1:
                # Если несколько месяцев, используем первый
                ym = periods[0]
                y, m = ym.split("-")
                period_month = f"{y}-{m}-01"
                human = self._month_human_ru(int(y), int(m))
                return period_month, human
            
            ym = periods[0]
            y, m = ym.split("-")
            period_month = f"{y}-{m}-01"
            human = self._month_human_ru(int(y), int(m))
            return period_month, human
            
        except Exception:
            # Fallback to current month
            now = datetime.utcnow()
            period_month = f"{now.year}-{now.month:02d}-01"
            human = self._month_human_ru(now.year, now.month)
            return period_month, human
    
    def _drop_broken(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int, float]:
        """Удаляет битые строки."""
        total = len(df)
        
        if total == 0:
            return df, 0, 0.0
        
        # Проверяем критические поля
        critical_fields = []
        if 'sale_datetime_utc' in df.columns and not df['sale_datetime_utc'].isna().all():
            critical_fields.append('sale_datetime_utc')
        if 'asset_id' in df.columns and not df['asset_id'].isna().all():
            critical_fields.append('asset_id')
        if 'royalty_usd' in df.columns and not df['royalty_usd'].isna().all():
            critical_fields.append('royalty_usd')
        
        # Если нет критических полей, считаем все строки валидными
        if not critical_fields:
            return df, 0, 0.0
        
        crit = df[critical_fields]
        broken_mask = crit.isna().any(axis=1)
        
        if 'asset_id' in df.columns:
            broken_mask = broken_mask | (df["asset_id"].eq(""))
        
        broken_rows = int(broken_mask.sum())
        broken_pct = round((broken_rows / total * 100) if total else 0.0, 2)
        df_clean = df.loc[~broken_mask].copy()
        
        if broken_pct > BROKEN_ROWS_THRESHOLD_PCT:
            raise ValueError(f"Доля битых строк {broken_pct}% превышает {BROKEN_ROWS_THRESHOLD_PCT}%")
        
        return df_clean, broken_rows, broken_pct
    
    def _compute_advanced_metrics(
        self, 
        df_clean: pd.DataFrame, 
        rows_total: int, 
        broken_rows: int, 
        broken_pct: float,
        period_month: str, 
        period_human_ru: str,
        portfolio_size: int = 100,
        upload_limit: int = 50,
        monthly_uploads: int = 30,
        acceptance_rate: float = 65.0
    ) -> AdvancedProcessResult:
        """Вычисляет расширенные метрики."""
        
        # Базовые KPI
        total_sales_count = int(len(df_clean))
        total_revenue_usd = float(df_clean["royalty_usd"].sum()) if 'royalty_usd' in df_clean.columns else 0.0
        unique_assets_sold = int(df_clean["asset_id"].nunique()) if 'asset_id' in df_clean.columns else 0
        avg_revenue_per_sale = float(total_revenue_usd / total_sales_count) if total_sales_count else 0.0
        
        # Разрезы по лицензии
        if 'license_plan' in df_clean.columns:
            by_license = (
                df_clean.groupby("license_plan", dropna=False)
                .agg(sales_count=("royalty_usd", "size"), revenue_usd=("royalty_usd", "sum"))
                .reset_index()
                .sort_values(["revenue_usd", "sales_count"], ascending=[False, False])
            )
        else:
            by_license = pd.DataFrame(columns=['license_plan', 'sales_count', 'revenue_usd'])
        
        # Разрезы по типу медиа
        if 'media_type' in df_clean.columns:
            by_media_type = (
                df_clean.groupby("media_type", dropna=False)
                .agg(sales_count=("royalty_usd", "size"), revenue_usd=("royalty_usd", "sum"))
                .reset_index()
                .sort_values(["revenue_usd", "sales_count"], ascending=[False, False])
            )
        else:
            by_media_type = pd.DataFrame(columns=['media_type', 'sales_count', 'revenue_usd'])
        
        # Топы по ассетам
        if 'asset_id' in df_clean.columns and 'asset_title' in df_clean.columns:
            by_asset = (
                df_clean.groupby(["asset_id", "asset_title"], as_index=False)
                .agg(total_sales=("royalty_usd", "size"), total_revenue=("royalty_usd", "sum"))
            )
            
            top10_by_revenue = by_asset.sort_values(
                ["total_revenue", "total_sales"], ascending=[False, False]
            ).head(10).reset_index(drop=True)
            
            top10_by_sales = by_asset.sort_values(
                ["total_sales", "total_revenue"], ascending=[False, False]
            ).head(10).reset_index(drop=True)
        else:
            top10_by_revenue = pd.DataFrame(columns=['asset_id', 'asset_title', 'total_sales', 'total_revenue'])
            top10_by_sales = pd.DataFrame(columns=['asset_id', 'asset_title', 'total_sales', 'total_revenue'])
        
        # Даты
        date_min = None
        date_max = None
        if 'sale_datetime_utc' in df_clean.columns:
            date_min = df_clean["sale_datetime_utc"].min()
            date_max = df_clean["sale_datetime_utc"].max()
        
        date_min_iso = date_min.isoformat() if pd.notna(date_min) else None
        date_max_iso = date_max.isoformat() if pd.notna(date_max) else None
        
        # Дополнительные метрики для бота
        portfolio_sold_percent = (unique_assets_sold / portfolio_size * 100) if portfolio_size > 0 else 0
        
        # Процент новых работ (за последние 3 месяца)
        new_works_sales = 0
        if 'sale_datetime_utc' in df_clean.columns and not df_clean['sale_datetime_utc'].isna().all():
            # Make timezone-aware comparison
            three_months_ago = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=90)
            new_works_mask = df_clean['sale_datetime_utc'] > three_months_ago
            new_works_sales = int(new_works_mask.sum())
        
        new_works_sales_percent = (new_works_sales / total_sales_count * 100) if total_sales_count > 0 else 0
        upload_limit_usage = (monthly_uploads / upload_limit * 100) if upload_limit > 0 else 0
        
        return AdvancedProcessResult(
            period_month=period_month,
            period_human_ru=period_human_ru,
            rows_total=int(rows_total),
            broken_rows=int(broken_rows),
            broken_pct=float(broken_pct),
            rows_used=int(total_sales_count),
            total_revenue_usd=round(total_revenue_usd, 2),
            unique_assets_sold=int(unique_assets_sold),
            avg_revenue_per_sale=round(avg_revenue_per_sale, 4),
            date_min_utc=date_min_iso,
            date_max_utc=date_max_iso,
            sales_by_license=by_license,
            sales_by_media_type=by_media_type,
            top10_by_revenue=top10_by_revenue,
            top10_by_sales=top10_by_sales,
            portfolio_sold_percent=round(portfolio_sold_percent, 2),
            new_works_sales_percent=round(new_works_sales_percent, 2),
            acceptance_rate=acceptance_rate,
            upload_limit_usage=round(upload_limit_usage, 2),
        )
    
    def process_csv(
        self, 
        csv_path: str,
        portfolio_size: int = 100,
        upload_limit: int = 50,
        monthly_uploads: int = 30,
        acceptance_rate: float = 65.0
    ) -> AdvancedProcessResult:
        """Основной метод обработки CSV."""
        
        # Чтение и нормализация
        df = self._read_and_normalize(csv_path)
        
        # Валидация месяца
        period_month, period_human_ru = self._validate_month(df)
        
        # Фильтрация битых строк
        df_clean, broken_rows, broken_pct = self._drop_broken(df)
        
        # Вычисление метрик
        result = self._compute_advanced_metrics(
            df_clean=df_clean,
            rows_total=len(df),
            broken_rows=broken_rows,
            broken_pct=broken_pct,
            period_month=period_month,
            period_human_ru=period_human_ru,
            portfolio_size=portfolio_size,
            upload_limit=upload_limit,
            monthly_uploads=monthly_uploads,
            acceptance_rate=acceptance_rate
        )
        
        return result
    
    def generate_bot_report(self, result: AdvancedProcessResult) -> str:
        """Генерирует отчет для бота."""
        
        # Базовые метрики
        report = f"""📊 **Отчёт за {result.period_human_ru} готов!**

**Основные показатели:**
• **Продаж:** {result.rows_used}
• **Доход:** {result.total_revenue_usd:.2f}$
• **Уникальных ассетов продано:** {result.unique_assets_sold}
• **Средний доход с продажи:** {result.avg_revenue_per_sale:.4f}$
• **% портфеля, который продался:** {result.portfolio_sold_percent}%
• **Доля продаж новых работ:** {result.new_works_sales_percent}%

**Дополнительные показатели:**
• **% приемки:** {result.acceptance_rate}%
• **Использование лимита загрузки:** {result.upload_limit_usage}%

**Разбивка по типу контента:**"""
        
        # Добавляем разбивку по медиа-типам
        if not result.sales_by_media_type.empty:
            for _, row in result.sales_by_media_type.iterrows():
                report += f"\n• {row['media_type'].title()}: {int(row['sales_count'])} продаж / ${round(float(row['revenue_usd']), 2)}"
        else:
            report += "\n• Данные недоступны"
        
        # Добавляем разбивку по лицензиям
        report += "\n\n**Разбивка по лицензиям:**"
        if not result.sales_by_license.empty:
            for _, row in result.sales_by_license.iterrows():
                report += f"\n• {row['license_plan'].title()}: {int(row['sales_count'])} продаж / ${round(float(row['revenue_usd']), 2)}"
        else:
            report += "\n• Данные недоступны"
        
        # Добавляем топ ассетов
        if not result.top10_by_revenue.empty:
            report += "\n\n**Топ-5 ассетов по выручке:**"
            for i, (_, row) in enumerate(result.top10_by_revenue.head(5).iterrows()):
                report += f"\n{i+1}. {row['asset_title']} — ${round(float(row['total_revenue']), 2)} / {int(row['total_sales'])} продаж"
        
        # Добавляем интерпретации
        report += self._generate_interpretations(result)
        
        return report
    
    def _generate_interpretations(self, result: AdvancedProcessResult) -> str:
        """Генерирует интерпретации метрик."""
        
        interpretations = "\n\n**Анализ показателей:**\n"
        
        # Интерпретация портфеля
        if result.portfolio_sold_percent < 1:
            interpretations += f"\n📈 **Портфель:** Если ты только недавно начал работу на стоках - все ок. Дай портфелю время. Но если ты на стоках уже давно - проблема в качестве контента."
        elif 1 <= result.portfolio_sold_percent < 2:
            interpretations += f"\n📈 **Портфель:** Продажи есть, но потенциал полностью не раскрыт. Что делать: Побей триггеров абонентов материала..."
        elif 2.01 <= result.portfolio_sold_percent < 3:
            interpretations += f"\n📈 **Портфель:** Ты на верном пути! Что делать: Продолжай в том же духе. Добавляй больше тем..."
        elif 3 <= result.portfolio_sold_percent < 5:
            interpretations += f"\n📈 **Портфель:** У тебя сильный результат. Что делать: Масштабируй; увеличивай объемы загрузки..."
        else:
            interpretations += f"\n📈 **Портфель:** Работы 🔥, портфель продаётся мощно. Что делать: Поднимай объём производства, сохраняя текущее качество..."
        
        # Интерпретация новых работ
        if result.new_works_sales_percent == 100:
            interpretations += f"\n🆕 **Новые работы:** Всё ок, ты только недавно начал работу, чтобы делать выводы. Что делать: Дай время: продажи набирают обороты первые 2-3 месяца после загрузки."
        elif result.new_works_sales_percent >= 30:
            interpretations += f"\n🆕 **Новые работы:** У тебя всё прекрасно выстроено. Новые работы качественные и прекрасно заходят. Что делать: Просто увеличивай объем загрузки."
        elif 20 <= result.new_works_sales_percent < 30:
            interpretations += f"\n🆕 **Новые работы:** Очень сильный результат. Что делать: Продолжай грузить в том же качестве. Добавляй новые темы."
        elif 10 <= result.new_works_sales_percent < 20:
            interpretations += f"\n🆕 **Новые работы:** Новый контент пошёл в продажи, это хороший знак. Что делать: Увеличь количество тем, чтобы привлечь новых покупателей."
        else:
            interpretations += f"\n🆕 **Новые работы:** Если ты только начал грузить новый контент — всё впереди, не переживай. Но если загружаешь новое уже 3+ месяца, значит проблема в качестве новых работ."
        
        # Интерпретация приемки
        if result.acceptance_rate < 30:
            interpretations += f"\n✅ **Приемка:** Результат слабый. Что делать: Посмотри обучающие видео и разберись, где именно ошибки в качестве..."
        elif 31 <= result.acceptance_rate < 50:
            interpretations += f"\n✅ **Приемка:** Есть над чем работать. Что делать: Пересмотри учебные видеоуроки, чтобы подтянуть слабые места..."
        elif 50 <= result.acceptance_rate < 55:
            interpretations += f"\n✅ **Приемка:** Это стандартный уровень, с которым работает большинство авторов. Что делать: Продолжай грузить, но параллельно смотри аналитику..."
        elif 55 <= result.acceptance_rate < 65:
            interpretations += f"\n✅ **Приемка:** У тебя сильные результаты. Что делать: Масштабируй текущие удачные направления..."
        else:
            interpretations += f"\n✅ **Приемка:** Такая приемка сейчас далеко не у всех. Что делать: Поддерживай качество и увеличивай объём..."
        
        # Интерпретация лимита загрузки
        if result.upload_limit_usage <= 30:
            interpretations += f"\n📤 **Загрузки:** Ты не используешь свой потенциал. Что делать: Загружай больше..."
        elif 30 < result.upload_limit_usage <= 60:
            interpretations += f"\n📤 **Загрузки:** Хорошее начало, но пока не дотягиваешь до оптимального уровня. Что делать: Ставь цель хотя бы 70–80% лимита..."
        elif 60 < result.upload_limit_usage <= 80:
            interpretations += f"\n📤 **Загрузки:** Ты работаешь в хорошем темпе, но есть запас для роста. Что делать: Дотяни до максимума лимита..."
        elif 80 < result.upload_limit_usage <= 95:
            interpretations += f"\n📤 **Загрузки:** Отличный результат, ты близко к максимуму. Что делать: Добей лимит, чтобы использовать потенциал работ 100%."
        else:
            interpretations += f"\n📤 **Загрузки:** Ты выжал из лимита всё, что можно. Что делать: Поддерживай такую систему загрузок и дальше."
        
        interpretations += "\n\n**Заключение:**\nЭто был полный отчёт по твоему портфелю за выбранный период.\nЕсли хочешь посмотреть аналитику за другой месяц — проверь свои лимиты в разделе 👤 Профиль и загрузи новый CSV-файл.\nПока сосредоточься на качестве. Посмотри обучающие материалы, чтобы понять что нужно делать.\nСледи за статистикой - через пару месяцев уже будут первые объективные показатели и ты узнаешь надо ли корректировать что-то в работе."
        
        return interpretations
