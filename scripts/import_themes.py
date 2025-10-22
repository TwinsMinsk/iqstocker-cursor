"""DEPRECATED: Use the admin panel to import themes.

One-off script to import themes from a CSV file into AdminTheme.

Usage (inside venv):
  python -m scripts.import_themes --path uploads/themes.csv --column theme --delimiter ,
"""

import csv
import argparse
from pathlib import Path

from config.database import SessionLocal
from database.models import GlobalTheme


def import_themes(csv_path: str, column: str | None, delimiter: str) -> int:
    db = SessionLocal()
    inserted = 0
    seen: set[str] = set()
    try:
        path = Path(csv_path)
        if not path.exists():
            print(f"CSV not found: {csv_path}")
            return 0

        with path.open('r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=delimiter) if column else csv.reader(f, delimiter=delimiter)

            if column:
                for row in reader:  # type: ignore
                    raw = (row.get(column) or '').strip()
                    if not raw:
                        continue
                    theme = raw[:255]
                    if theme in seen:
                        continue
                    seen.add(theme)
                    # upsert-like: ignore duplicates
                    if not db.query(GlobalTheme).filter_by(theme_name=theme).first():
                        db.add(GlobalTheme(theme_name=theme))
                        inserted += 1
            else:
                for row in reader:  # type: ignore
                    if not row:
                        continue
                    raw = (row[0] or '').strip()
                    if not raw:
                        continue
                    theme = raw[:255]
                    if theme in seen:
                        continue
                    seen.add(theme)
                    if not db.query(GlobalTheme).filter_by(theme_name=theme).first():
                        db.add(GlobalTheme(theme_name=theme))
                        inserted += 1

        if inserted:
            db.commit()
        print(f"Imported {inserted} themes (new)")
        return inserted
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', default='uploads/themes.csv')
    parser.add_argument('--column', default='theme')
    parser.add_argument('--delimiter', default=',')
    args = parser.parse_args()

    import_themes(args.path, args.column, args.delimiter)


if __name__ == '__main__':
    main()


