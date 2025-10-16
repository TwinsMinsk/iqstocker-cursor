#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IQStocker — CSV Processor (per PRD/TЗ)

Функциональность:
- Парсинг CSV (без шапки, 9 колонок), UTF-8, разделитель запятая
- Нормализация типов: UTC datetime, currency -> float, категории -> lower
- Валидации: "один календарный месяц", доля "битых" строк <= 20%
- Метрики: total_sales_count, total_revenue_usd, unique_assets_sold, avg_revenue_per_sale
- Разрезы: по license_plan и media_type
- Топы ассетов: по выручке и по количеству продаж (топ-10)
- Экспорт: JSON/CSV, тексты M-03/M-04; опционально SQL DDL + UPSERT сид

Python >= 3.10, зависимости: pandas
"""

from __future__ import annotations
import argparse
import json
import os
import re
import sys
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# ----------------------------- Config & Constants -----------------------------

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
ALLOWED_MEDIA   = {"photos", "videos", "illustrations"}

# Порог брака (битые строки) — 20% (если больше, отклоняем файл)
BROKEN_ROWS_THRESHOLD_PCT = 20.0

# FREE режим для M-04 показывает 3 позиции
TOP_FREE_K = 3

# ----------------------------- Data Structures --------------------------------

@dataclass
class ProcessResult:
    # Основные агрегаты/валидации
    period_month: str                     # 'YYYY-MM-01'
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

    # Для текстовых отчетов
    period_human_ru: str


# ----------------------------- Helpers ----------------------------------------

def _to_amount(series: pd.Series) -> pd.Series:
    """
    Очистка валюты до float:
    "$0.99" / "0,99" / "  0.99 USD " -> 0.99
    """
    s = series.astype(str)
    s = s.str.replace(r"(USD|EUR|PLN|RUB|RUR|₽|€|\$|zł|руб\.?)", "", regex=True, flags=re.IGNORECASE)
    s = s.str.replace(r"\s", "", regex=True)
    s = s.str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def _month_human_ru(year: int, month: int) -> str:
    months = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }
    return f"{months[month]} {year}"


def _read_and_normalize(path: str) -> pd.DataFrame:
    """
    Читает CSV по нашему «входному контракту» и нормализует поля.
    - Без заголовка (header=None), запятая, UTF-8
    - Имена колонок -> EXPECTED_COLS
    - Типы: datetime(UTC), asset_id -> str, royalty_usd -> float
    - Категории -> lower().strip()
    """
    df = pd.read_csv(
        path,
        encoding="utf-8",
        sep=",",
        header=None,
        names=EXPECTED_COLS,
        engine="python"
    )

    # Типы
    df["sale_datetime_utc"] = pd.to_datetime(df["sale_datetime_utc"], utc=True, errors="coerce")
    df["asset_id"] = df["asset_id"].astype(str).str.strip()
    df["royalty_usd"] = _to_amount(df["royalty_usd"])

    # Категории
    for c in ["license_plan", "media_type", "size_label", "contributor_name"]:
        df[c] = df[c].astype(str).str.strip().str.lower()

    # Тексты
    for c in ["asset_title", "filename"]:
        df[c] = df[c].astype(str).str.strip()

    return df


def _validate_month(df: pd.DataFrame) -> Tuple[str, str]:
    """
    Проверка «одного календарного месяца».
    Возвращает:
      - period_month (строка 'YYYY-MM-01')
      - period_human_ru ('Июль 2025')
    Бросает ValueError при нарушении.
    """
    months = df["sale_datetime_utc"].dt.to_period("M").astype(str).unique().tolist()
    if len(months) != 1:
        raise ValueError(f"E-04: файл должен содержать ровно один календарный месяц, найдено: {months}")
    ym = months[0]  # 'YYYY-MM'
    y, m = ym.split("-")
    period_month = f"{y}-{m}-01"
    human = _month_human_ru(int(y), int(m))
    return period_month, human


def _drop_broken(df: pd.DataFrame) -> Tuple[pd.DataFrame, int, float]:
    """
    Выбрасывает «битые» строки (NaT/NaN/пустой asset_id в критических полях).
    Возвращает (df_clean, broken_rows, broken_pct).
    """
    total = len(df)
    crit = df[["sale_datetime_utc", "asset_id", "royalty_usd"]]
    broken_mask = crit.isna().any(axis=1) | (df["asset_id"].eq(""))
    broken_rows = int(broken_mask.sum())
    broken_pct = round((broken_rows / total * 100) if total else 0.0, 2)
    df_clean = df.loc[~broken_mask].copy()

    if broken_pct > BROKEN_ROWS_THRESHOLD_PCT:
        raise ValueError(f"E-03: доля «битых» строк {broken_pct}% превышает {BROKEN_ROWS_THRESHOLD_PCT}%")

    return df_clean, broken_rows, broken_pct


def _compute_metrics(df_clean: pd.DataFrame, rows_total: int, broken_rows: int, broken_pct: float,
                     period_month: str, period_human_ru: str) -> ProcessResult:
    """
    Считает KPI, разрезы и топы. Возвращает ProcessResult.
    """
    # Базовые KPI
    total_sales_count = int(len(df_clean))
    total_revenue_usd = float(df_clean["royalty_usd"].sum())
    unique_assets_sold = int(df_clean["asset_id"].nunique())
    avg_revenue_per_sale = float(total_revenue_usd / total_sales_count) if total_sales_count else 0.0

    # Разрезы
    by_license = (
        df_clean.groupby("license_plan", dropna=False)
        .agg(sales_count=("royalty_usd", "size"), revenue_usd=("royalty_usd", "sum"))
        .reset_index()
        .sort_values(["revenue_usd", "sales_count"], ascending=[False, False])
    )

    by_media_type = (
        df_clean.groupby("media_type", dropna=False)
        .agg(sales_count=("royalty_usd", "size"), revenue_usd=("royalty_usd", "sum"))
        .reset_index()
        .sort_values(["revenue_usd", "sales_count"], ascending=[False, False])
    )

    # Топы по ассетам
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

    # Даты
    date_min = df_clean["sale_datetime_utc"].min()
    date_max = df_clean["sale_datetime_utc"].max()
    date_min_iso = date_min.isoformat() if pd.notna(date_min) else None
    date_max_iso = date_max.isoformat() if pd.notna(date_max) else None

    return ProcessResult(
        period_month=period_month,
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
        period_human_ru=period_human_ru,
    )


def _ensure_outdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _write_json(path: str, obj) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _emit_outputs(result: ProcessResult, outdir: str, emit_sql: bool) -> Dict[str, str]:
    """
    Сохраняет JSON/CSV + тексты M-03/M-04; опционально SQL схему и сид.
    Возвращает словарь {name: path}.
    """
    _ensure_outdir(outdir)
    paths: Dict[str, str] = {}

    # -------- JSON --------
    summary_json = {
        "period_month": result.period_month,
        "rows_total": result.rows_total,
        "broken_rows": result.broken_rows,
        "broken_pct": result.broken_pct,
        "rows_used": result.rows_used,
        "total_revenue_usd": result.total_revenue_usd,
        "unique_assets_sold": result.unique_assets_sold,
        "avg_revenue_per_sale": result.avg_revenue_per_sale,
        "date_min_utc": result.date_min_utc,
        "date_max_utc": result.date_max_utc,
    }
    _write_json(os.path.join(outdir, "analysis_summary.json"), summary_json)
    paths["analysis_summary.json"] = os.path.join(outdir, "analysis_summary.json")

    license_json = [
        {
            "license_plan": r["license_plan"],
            "sales_count": int(r["sales_count"]),
            "revenue_usd": round(float(r["revenue_usd"]), 2),
        }
        for _, r in result.sales_by_license.iterrows()
    ]
    _write_json(os.path.join(outdir, "breakdown_license.json"), license_json)
    paths["breakdown_license.json"] = os.path.join(outdir, "breakdown_license.json")

    media_json = [
        {
            "media_type": r["media_type"],
            "sales_count": int(r["sales_count"]),
            "revenue_usd": round(float(r["revenue_usd"]), 2),
        }
        for _, r in result.sales_by_media_type.iterrows()
    ]
    _write_json(os.path.join(outdir, "breakdown_media_type.json"), media_json)
    paths["breakdown_media_type.json"] = os.path.join(outdir, "breakdown_media_type.json")

    top_rev_json = [
        {
            "rank": i + 1,
            "asset_id": str(r["asset_id"]),
            "asset_title": r["asset_title"],
            "total_sales": int(r["total_sales"]),
            "total_revenue": round(float(r["total_revenue"]), 2),
        }
        for i, r in result.top10_by_revenue.iterrows()
    ]
    _write_json(os.path.join(outdir, "top_assets_by_revenue.json"), top_rev_json)
    paths["top_assets_by_revenue.json"] = os.path.join(outdir, "top_assets_by_revenue.json")

    top_sales_json = [
        {
            "rank": i + 1,
            "asset_id": str(r["asset_id"]),
            "asset_title": r["asset_title"],
            "total_sales": int(r["total_sales"]),
            "total_revenue": round(float(r["total_revenue"]), 2),
        }
        for i, r in result.top10_by_sales.iterrows()
    ]
    _write_json(os.path.join(outdir, "top_assets_by_sales.json"), top_sales_json)
    paths["top_assets_by_sales.json"] = os.path.join(outdir, "top_assets_by_sales.json")

    # -------- CSV (удобно для ручной проверки) --------
    result.sales_by_license.to_csv(os.path.join(outdir, "sales_by_license.csv"), index=False)
    result.sales_by_media_type.to_csv(os.path.join(outdir, "sales_by_media_type.csv"), index=False)
    result.top10_by_revenue.to_csv(os.path.join(outdir, "top_10_assets_by_revenue.csv"), index=False)
    result.top10_by_sales.to_csv(os.path.join(outdir, "top_10_assets_by_sales.csv"), index=False)
    paths["sales_by_license.csv"] = os.path.join(outdir, "sales_by_license.csv")
    paths["sales_by_media_type.csv"] = os.path.join(outdir, "sales_by_media_type.csv")
    paths["top_10_assets_by_revenue.csv"] = os.path.join(outdir, "top_10_assets_by_revenue.csv")
    paths["top_10_assets_by_sales.csv"] = os.path.join(outdir, "top_10_assets_by_sales.csv")

    # -------- Текстовые отчеты (M-03/M-04 FREE) --------
    m03_text = f"""📊 Аналитика за {result.period_human_ru}

📈 Общие показатели:
- Всего продаж: {result.rows_used}
- Общая выручка: ${result.total_revenue_usd}
- Уникальных ассетов продано: {result.unique_assets_sold}
- Средний доход с продажи (RPS): ${result.avg_revenue_per_sale}

📁 По типу контента:
""" + "\n".join(
        f"- {r['media_type']}: {int(r['sales_count'])} продаж / ${round(float(r['revenue_usd']),2)}"
        for _, r in result.sales_by_media_type.iterrows()
    ) + "\n\n📜 По типу лицензии:\n" + "\n".join(
        f"- {r['license_plan']}: {int(r['sales_count'])} продаж / ${round(float(r['revenue_usd']),2)}"
        for _, r in result.sales_by_license.iterrows()
    )
    with open(os.path.join(outdir, "report_M03_analytics.txt"), "w", encoding="utf-8") as f:
        f.write(m03_text)
    paths["report_M03_analytics.txt"] = os.path.join(outdir, "report_M03_analytics.txt")

    top3 = result.top10_by_revenue.head(TOP_FREE_K)
    lines = [
        f"{i+1}) {row['asset_title']} — ${round(float(row['total_revenue']),2)} / {int(row['total_sales'])} продаж"
        for i, (_, row) in enumerate(top3.iterrows())
    ]
    m04_text = f"""🏆 Топ тем за {result.period_human_ru} (FREE)

""" + ("\n".join(lines) if lines else "—")
    with open(os.path.join(outdir, "report_M04_top_themes_FREE.txt"), "w", encoding="utf-8") as f:
        f.write(m04_text)
    paths["report_M04_top_themes_FREE.txt"] = os.path.join(outdir, "report_M04_top_themes_FREE.txt")

    # -------- SQL (опционально) --------
    if emit_sql:
        analysis_id = str(uuid.uuid4())
        schema_sql = f"""-- === IQStocker Analytics Schema (PostgreSQL) ===
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'license_plan_enum') THEN
        CREATE TYPE license_plan_enum AS ENUM ('custom','subscription');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'media_type_enum') THEN
        CREATE TYPE media_type_enum AS ENUM ('photos','videos','illustrations');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ranking_metric_enum') THEN
        CREATE TYPE ranking_metric_enum AS ENUM ('revenue','sales');
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS analyses (
    id UUID PRIMARY KEY,
    period_month DATE NOT NULL,
    rows_total INTEGER NOT NULL,
    broken_rows INTEGER NOT NULL,
    broken_pct NUMERIC(5,2) NOT NULL,
    rows_used INTEGER NOT NULL,
    total_revenue_usd NUMERIC(12,2) NOT NULL CHECK (total_revenue_usd >= 0),
    unique_assets_sold INTEGER NOT NULL,
    avg_revenue_per_sale NUMERIC(12,4) NOT NULL CHECK (avg_revenue_per_sale >= 0),
    date_min TIMESTAMPTZ NOT NULL,
    date_max TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (period_month)
);

CREATE TABLE IF NOT EXISTS analysis_breakdown_license (
    analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    license_plan license_plan_enum NOT NULL,
    sales_count INTEGER NOT NULL,
    revenue_usd NUMERIC(12,2) NOT NULL CHECK (revenue_usd >= 0),
    PRIMARY KEY (analysis_id, license_plan)
);

CREATE TABLE IF NOT EXISTS analysis_breakdown_media_type (
    analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    media_type media_type_enum NOT NULL,
    sales_count INTEGER NOT NULL,
    revenue_usd NUMERIC(12,2) NOT NULL CHECK (revenue_usd >= 0),
    PRIMARY KEY (analysis_id, media_type)
);

CREATE TABLE IF NOT EXISTS analysis_top_assets (
    analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    metric ranking_metric_enum NOT NULL, -- revenue | sales
    rank INTEGER NOT NULL CHECK (rank >= 1),
    asset_id TEXT NOT NULL,
    asset_title TEXT NOT NULL,
    total_sales INTEGER NOT NULL,
    total_revenue NUMERIC(12,2) NOT NULL CHECK (total_revenue >= 0),
    PRIMARY KEY (analysis_id, metric, rank)
);
"""
        seed_lines = []
        seed_lines.append(f"""-- Upsert analysis summary for {result.period_month}
INSERT INTO analyses (id, period_month, rows_total, broken_rows, broken_pct, rows_used, total_revenue_usd, unique_assets_sold, avg_revenue_per_sale, date_min, date_max)
VALUES ('{analysis_id}', '{result.period_month}', {result.rows_total}, {result.broken_rows}, {result.broken_pct}, {result.rows_used}, {result.total_revenue_usd}, {result.unique_assets_sold}, {result.avg_revenue_per_sale}, '{result.date_min_utc}', '{result.date_max_utc}')
ON CONFLICT (period_month) DO UPDATE SET
    rows_total = EXCLUDED.rows_total,
    broken_rows = EXCLUDED.broken_rows,
    broken_pct = EXCLUDED.broken_pct,
    rows_used = EXCLUDED.rows_used,
    total_revenue_usd = EXCLUDED.total_revenue_usd,
    unique_assets_sold = EXCLUDED.unique_assets_sold,
    avg_revenue_per_sale = EXCLUDED.avg_revenue_per_sale,
    date_min = EXCLUDED.date_min,
    date_max = EXCLUDED.date_max
RETURNING id;""")

        for _, r in result.sales_by_license.iterrows():
            lp = r["license_plan"]
            seed_lines.append(f"""
INSERT INTO analysis_breakdown_license (analysis_id, license_plan, sales_count, revenue_usd)
VALUES ('{analysis_id}', '{lp}', {int(r['sales_count'])}, {round(float(r['revenue_usd']),2)})
ON CONFLICT (analysis_id, license_plan) DO UPDATE SET
    sales_count = EXCLUDED.sales_count,
    revenue_usd = EXCLUDED.revenue_usd;""")

        for _, r in result.sales_by_media_type.iterrows():
            mt = r["media_type"]
            seed_lines.append(f"""
INSERT INTO analysis_breakdown_media_type (analysis_id, media_type, sales_count, revenue_usd)
VALUES ('{analysis_id}', '{mt}', {int(r['sales_count'])}, {round(float(r['revenue_usd']),2)})
ON CONFLICT (analysis_id, media_type) DO UPDATE SET
    sales_count = EXCLUDED.sales_count,
    revenue_usd = EXCLUDED.revenue_usd;""")

        for i, r in result.top10_by_revenue.iterrows():
            seed_lines.append(f"""
INSERT INTO analysis_top_assets (analysis_id, metric, rank, asset_id, asset_title, total_sales, total_revenue)
VALUES ('{analysis_id}', 'revenue', {i+1}, '{str(r['asset_id']).replace("'", "''")}', '{str(r['asset_title']).replace("'", "''")}', {int(r['total_sales'])}, {round(float(r['total_revenue']),2)})
ON CONFLICT (analysis_id, metric, rank) DO UPDATE SET
    asset_id = EXCLUDED.asset_id,
    asset_title = EXCLUDED.asset_title,
    total_sales = EXCLUDED.total_sales,
    total_revenue = EXCLUDED.total_revenue;""")

        for i, r in result.top10_by_sales.iterrows():
            seed_lines.append(f"""
INSERT INTO analysis_top_assets (analysis_id, metric, rank, asset_id, asset_title, total_sales, total_revenue)
VALUES ('{analysis_id}', 'sales', {i+1}, '{str(r['asset_id']).replace("'", "''")}', '{str(r['asset_title']).replace("'", "''")}', {int(r['total_sales'])}, {round(float(r['total_revenue']),2)})
ON CONFLICT (analysis_id, metric, rank) DO UPDATE SET
    asset_id = EXCLUDED.asset_id,
    asset_title = EXCLUDED.asset_title,
    total_sales = EXCLUDED.total_sales,
    total_revenue = EXCLUDED.total_revenue;""")

        schema_path = os.path.join(outdir, "iqstocker_schema.sql")
        seed_path = os.path.join(outdir, f"iqstocker_seed_{result.period_month}.sql")
        with open(schema_path, "w", encoding="utf-8") as f:
            f.write(schema_sql)
        with open(seed_path, "w", encoding="utf-8") as f:
            f.write("-- analysis_id: " + analysis_id + "\n\n")
            f.write("\n".join(seed_lines))
        paths["iqstocker_schema.sql"] = schema_path
        paths[os.path.basename(seed_path)] = seed_path

    return paths


# ----------------------------- CLI & Main -------------------------------------

def process(input_csv: str, outdir: str, emit_sql: bool) -> Dict[str, str]:
    df = _read_and_normalize(input_csv)

    # Валидация «один месяц»
    period_month, period_human_ru = _validate_month(df)

    # Фильтрация «битых» строк
    df_clean, broken_rows, broken_pct = _drop_broken(df)

    # Метрики/агрегации/топы
    result = _compute_metrics(
        df_clean=df_clean,
        rows_total=len(df),
        broken_rows=broken_rows,
        broken_pct=broken_pct,
        period_month=period_month,
        period_human_ru=period_human_ru,
    )

    # Экспорт
    paths = _emit_outputs(result, outdir, emit_sql=emit_sql)
    return paths


def main():
    parser = argparse.ArgumentParser(description="IQStocker CSV Processor")
    parser.add_argument("--input", "-i", required=True, help="Путь к входному CSV (без шапки, 9 колонок)")
    parser.add_argument("--outdir", "-o", default="./out", help="Каталог для вывода артефактов")
    parser.add_argument("--emit-sql", action="store_true", help="Сгенерировать SQL схему и UPSERT сид")
    args = parser.parse_args()

    try:
        paths = process(args.input, args.outdir, emit_sql=args.emit_sql)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(2)

    print("OK. Артефакты:")
    for name, p in paths.items():
        print(f" - {name}: {p}")


if __name__ == "__main__":
    main()
