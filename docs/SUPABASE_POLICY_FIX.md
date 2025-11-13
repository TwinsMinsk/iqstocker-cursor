# 🔧 Исправление Supabase Storage Policy

## Проблема
При создании политики в Supabase UI появляется ошибка:
```
Error adding policy: syntax error at or near ";"
```

## Причина
В поле **Policy definition** не нужно писать полный SQL с `CREATE POLICY`, `USING`, `WITH CHECK` и точкой с запятой. Supabase UI ожидает только **условное выражение** (expression).

---

## ✅ Правильное решение

### Шаг 1: Создай политику через UI

1. Открой https://supabase.com/dashboard/project/tqydndcvjqigxvjmaacj/storage/buckets/csv-files
2. Перейди в раздел **Policies**
3. Нажми **"New policy"** или **"Add policy"**
4. Заполни форму:

**Policy name:**
```
Service Role Full Access
```

**Allowed operation:**
- ✅ SELECT
- ✅ INSERT
- ✅ UPDATE
- ✅ DELETE

**Target roles:**
```
service_role
```

**Policy definition:**

В поле **USING** напиши только:
```sql
bucket_id = 'csv-files'
```

В поле **WITH CHECK** напиши только:
```sql
bucket_id = 'csv-files'
```

**НЕ ПИШИ:**
- ❌ `CREATE POLICY`
- ❌ `ON storage.objects`
- ❌ `FOR ALL`
- ❌ Точку с запятой (`;`)

5. Нажми **"Save policy"** или **"Review"** → **"Save policy"**

---

### Шаг 2: Проверка

После создания политики:

1. Перейди в **Storage** → **csv-files** → **Policies**
2. Должна появиться политика **"Service Role Full Access"**
3. Проверь, что для неё указаны все операции: SELECT, INSERT, UPDATE, DELETE

---

## 🔄 Альтернативный способ (через SQL Editor)

Если UI не работает, можно создать политику через **SQL Editor**:

1. Открой https://supabase.com/dashboard/project/tqydndcvjqigxvjmaacj/sql/new
2. Вставь этот SQL:

```sql
-- Удалить старую политику (если есть)
DROP POLICY IF EXISTS "Service Role Full Access" ON storage.objects;

-- Создать новую политику
CREATE POLICY "Service Role Full Access"
ON storage.objects
FOR ALL
TO service_role
USING (bucket_id = 'csv-files')
WITH CHECK (bucket_id = 'csv-files');
```

3. Нажми **"Run"**

---

## 📝 Пояснение

**Почему `service_role` и не нужны сложные политики?**

- `service_role` key (который ты используешь в боте) имеет права администратора
- RLS (Row Level Security) не применяется к `service_role` by design
- Эта политика нужна только для формального compliance, но на практике `service_role` обходит все политики

**Важно:**
- В `SUPABASE_KEY` (переменная окружения) должен быть именно **service_role** key, а не **anon** key
- **service_role** key находится в Supabase Dashboard → Settings → API → **service_role** (secret)

---

## ✅ Проверка корректности настройки

После создания политики, проверь загрузку файла:

```python
from supabase import create_client

supabase = create_client(
    "https://tqydndcvjqigxvjmaacj.supabase.co",
    "твой_service_role_key"  # НЕ anon key!
)

# Тестовая загрузка
test_data = b"test,data\n1,2"
response = supabase.storage.from_("csv-files").upload("test/test.csv", test_data)
print(response)  # Должен быть успешный ответ

# Удалить тестовый файл
supabase.storage.from_("csv-files").remove(["test/test.csv"])
```

Если работает — настройка корректна! 🎉

---

**Дата создания**: 2024-11-13  
**Проект**: IQStocker Bot  
**Bucket**: `csv-files`

