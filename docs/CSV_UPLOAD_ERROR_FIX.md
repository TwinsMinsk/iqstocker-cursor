# 🔧 Исправление ошибки "Ошибка при загрузке файла: {error}"

## 🔴 Проблема

При загрузке CSV файла в разделе "Аналитика портфеля" пользователь видел сообщение:
```
Ошибка при загрузке файла: {error}
```

**Причина:**
1. В лексиконе есть ключ `csv_upload_error` со значением `"Ошибка при загрузке файла: {error}"`
2. В коде использовался `.get()` без форматирования, поэтому `{error}` выводился буквально
3. Реальная ошибка не логировалась, что затрудняло диагностику

---

## ✅ Исправления

### 1. **Исправлено форматирование ошибки в `bot/handlers/analytics.py`**

**До:**
```python
except Exception as e:
    await message.answer(
        LEXICON_RU.get('csv_upload_error', f'Ошибка при загрузке файла: {str(e)}')
    )
```

**После:**
```python
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Error uploading CSV file: {str(e)}", exc_info=True)
    
    # Форматируем сообщение об ошибке
    error_msg = LEXICON_RU.get('csv_upload_error', f'Ошибка при загрузке файла: {str(e)}')
    if '{error}' in error_msg:
        error_msg = error_msg.format(error=str(e))
    await message.answer(error_msg)
```

**Что изменилось:**
- ✅ Добавлено логирование ошибки с полным traceback
- ✅ Исправлено форматирование сообщения об ошибке
- ✅ Теперь пользователь увидит реальную причину ошибки

---

### 2. **Улучшен `StorageService` в `services/storage_service.py`**

**Изменения:**

1. **Использование settings вместо прямого `os.getenv()`:**
   ```python
   supabase_url = settings.supabase_url
   supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or settings.supabase_key
   ```

2. **Правильный ключ для Storage:**
   - Используется `SUPABASE_SERVICE_ROLE_KEY` (если доступен)
   - Fallback на `SUPABASE_KEY` если service role key не установлен
   - **Важно:** Для Storage операций рекомендуется использовать SERVICE_ROLE_KEY

3. **Улучшенная обработка ошибок:**
   ```python
   try:
       self.supabase = create_client(supabase_url, supabase_key)
       self.bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "csv-files")
       logger.info(f"StorageService initialized with bucket: {self.bucket}")
   except Exception as e:
       logger.error(f"Failed to initialize Supabase Storage client: {e}")
       raise ValueError(f"Failed to initialize Supabase Storage: {e}") from e
   ```

4. **Правильная async обработка:**
   ```python
   async def upload_csv(self, file_bytes: bytes, user_id: int, filename: str) -> str:
       # Supabase Storage API синхронный, оборачиваем в executor
       def _upload():
           return self.supabase.storage.from_(self.bucket).upload(file_key, file_bytes)
       
       await asyncio.to_thread(_upload)
   ```

---

## 🔍 Возможные причины ошибки

### 1. **Отсутствуют переменные окружения**

**Проверь в Railway Dashboard → Shared Variables:**
- ✅ `SUPABASE_URL` - URL твоего Supabase проекта
- ✅ `SUPABASE_SERVICE_ROLE_KEY` - Service Role Key (рекомендуется для Storage)
- ✅ `SUPABASE_KEY` - Anon Key (fallback, если SERVICE_ROLE_KEY не установлен)
- ✅ `SUPABASE_STORAGE_BUCKET` - Имя bucket (по умолчанию: `csv-files`)

### 2. **Неправильный ключ Supabase**

**Для Storage операций нужен SERVICE_ROLE_KEY, а не Anon Key!**

**Как найти SERVICE_ROLE_KEY:**
1. Supabase Dashboard → Settings → API
2. Найди **"service_role"** секцию
3. Скопируй **"service_role key"** (НЕ "anon public" key!)

**В Railway:**
```bash
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 3. **Неправильная политика Storage**

**Проверь Supabase Storage Policy:**
1. Supabase Dashboard → Storage → `csv-files` bucket
2. Policies → должна быть policy для записи файлов

**Минимальная policy для записи:**
```sql
bucket_id = 'csv-files'
```

См. подробную инструкцию: `docs/SUPABASE_POLICY_FIX.md`

### 4. **Bucket не существует**

**Проверь:**
1. Supabase Dashboard → Storage
2. Убедись, что bucket `csv-files` существует
3. Если нет - создай его:
   - Name: `csv-files`
   - Public: `false` (приватный bucket)

---

## 🧪 Проверка после исправления

### 1. **Проверь логи Railway**

После деплоя проверь логи Bot service:

**Должно появиться:**
```
StorageService initialized with bucket: csv-files
Uploaded CSV to Storage: <user_id>/<uuid>_<filename>.csv (size: <N> bytes)
```

**Если ошибка:**
```
Failed to initialize Supabase Storage client: ...
Failed to upload CSV to Storage: ...
```

### 2. **Протестируй загрузку CSV**

1. Открой бота в Telegram
2. Перейди в "📊 Аналитика портфеля"
3. Загрузи тестовый CSV файл
4. **Ожидаемый результат:**
   - ✅ Файл принимается
   - ✅ Появляется сообщение "Файл получен: ..."
   - ✅ Задаётся вопрос о размере портфеля

**Если ошибка:**
- Теперь ты увидишь **реальную причину** ошибки вместо `{error}`
- Проверь логи Railway для деталей

---

## 📝 Чек-лист для Railway

Убедись, что в Railway установлены все переменные:

- [ ] `SUPABASE_URL` - URL проекта (например: `https://xxxxx.supabase.co`)
- [ ] `SUPABASE_SERVICE_ROLE_KEY` - Service Role Key (для Storage операций)
- [ ] `SUPABASE_KEY` - Anon Key (fallback, опционально)
- [ ] `SUPABASE_STORAGE_BUCKET` - Имя bucket (по умолчанию: `csv-files`)

**Где найти:**
- Supabase Dashboard → Settings → API
- `SUPABASE_URL`: Project URL
- `SUPABASE_SERVICE_ROLE_KEY`: service_role key (секретный!)
- `SUPABASE_KEY`: anon public key

---

## 🎯 Итоговые изменения

| Файл | Изменение | Результат |
|------|-----------|-----------|
| `bot/handlers/analytics.py` | Исправлено форматирование ошибки + логирование | Пользователь видит реальную ошибку |
| `services/storage_service.py` | Использование settings + правильный ключ + async обработка | Более надёжная работа с Supabase Storage |

---

## 💡 Дополнительные рекомендации

### 1. **Мониторинг ошибок**

После деплоя следи за логами:
- Railway Dashboard → Bot service → Logs
- Ищи строки: `Error uploading CSV file:`

### 2. **Тестирование**

Протестируй с разными файлами:
- ✅ Маленький CSV (< 1MB)
- ✅ Средний CSV (1-5MB)
- ✅ CSV с разными форматами данных

### 3. **Если проблема остаётся**

1. **Проверь логи Railway** - теперь там будет полный traceback ошибки
2. **Проверь переменные окружения** - все ли установлены правильно
3. **Проверь Supabase Storage Policy** - см. `docs/SUPABASE_POLICY_FIX.md`
4. **Проверь bucket** - существует ли `csv-files` bucket

---

**Дата создания**: 13.11.2025  
**Версия**: 1.0  
**Статус**: Готово к тестированию

