# Исправление ошибки кодировки Unicode

## Проблема
При запуске скрипта миграции в Windows PowerShell возникала ошибка:
```
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f680' in position 0: character maps to <undefined>
```

## Причина
Эмодзи (🚀, 📖, ✅, ❌ и др.) не могут быть отображены в кодировке cp1251, которая используется по умолчанию в Windows PowerShell.

## Решение
Убраны все эмодзи из скриптов и заменены на обычный текст:

### Обновленные файлы:
1. **`scripts/data/import_themes_to_supabase.py`** - убраны все эмодзи
2. **`scripts/data/verify_themes_migration.py`** - убраны все эмодзи  
3. **`migrate_themes.py`** - убраны все эмодзи

### Примеры замен:
- `🚀 Начинаем импорт` → `Запуск импорта`
- `📖 Читаем CSV файл` → `Читаем CSV файл`
- `✅ Успешно импортировано` → `УСПЕХ: Успешно импортировано`
- `❌ ОШИБКА` → `ОШИБКА`

## Теперь можно запускать:
```bash
python migrate_themes.py
```

Скрипт должен работать без ошибок кодировки в Windows PowerShell.
