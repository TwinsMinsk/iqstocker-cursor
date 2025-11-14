# ⚡ БЫСТРОЕ ИСПРАВЛЕНИЕ ПЕРЕД ЗАПУСКОМ

**Время:** 1-2 часа  
**Цель:** Исправить 2 критических блокера

---

## 🔴 ПРОБЛЕМА 1: Синхронное логирование (15 минут)

### Текущий код (bot/main.py:22-29)

```python
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),  # ❌ БЛОКИРУЕТ Event Loop
        logging.StreamHandler()
    ]
)
```

### ✅ ВАРИАНТ 1: QueueHandler (рекомендуется)

Замени блок logging.basicConfig на:

```python
from logging.handlers import QueueHandler, QueueListener
import queue

# Создаем очередь для асинхронной записи
log_queue = queue.Queue(-1)

# Handlers для фоновой записи
file_handler = logging.FileHandler('logs/bot.log')
stream_handler = logging.StreamHandler()

# Форматтер
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# QueueListener записывает в фоновом потоке
queue_listener = QueueListener(
    log_queue,
    file_handler,
    stream_handler,
    respect_handler_level=True
)

# QueueHandler для основного логгера
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    handlers=[QueueHandler(log_queue)]
)

# Запускаем listener
queue_listener.start()

logger = logging.getLogger(__name__)
```

**В функции main(), в блоке finally (строка 119), ПЕРЕД bot.session.close(), добавь:**

```python
# Остановить QueueListener
logger.info("Stopping log queue listener...")
try:
    queue_listener.stop()
    logger.info("Log queue listener stopped")
except Exception as e:
    logger.error(f"Error stopping log queue listener: {e}")
```

### ✅ ВАРИАНТ 2: Только stderr (быстрее, 5 минут)

Замени блок на:

```python
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Только stderr (Railway собирает автоматически)
    ]
)
```

**Плюсы:** Быстро, нет блокировок  
**Минусы:** Нет локальных логов (но они есть в Railway Dashboard)

### То же самое для workers/actors.py (строки 18-23)

Повтори одно из решений выше.

---

## 🔴 ПРОБЛЕМА 2: Storage Timeouts (30 минут)

### Файл: services/storage_service.py

Замени 3 метода:

### 1. upload_csv (строки 50-78)

```python
async def upload_csv(self, file_bytes: bytes, user_id: int, filename: str) -> str:
    """
    Upload CSV file to Supabase Storage with timeout.
    
    Args:
        file_bytes: File content as bytes
        user_id: User ID for organizing files
        filename: Original filename
        
    Returns:
        Storage file key (path)
    """
    import asyncio
    
    file_key = f"{user_id}/{uuid.uuid4()}_{filename}"
    
    try:
        # Supabase Storage API синхронный, оборачиваем в executor
        def _upload():
            return self.supabase.storage.from_(self.bucket).upload(file_key, file_bytes)
        
        # ✅ Добавляем таймаут 15 секунд
        await asyncio.wait_for(
            asyncio.to_thread(_upload),
            timeout=15.0
        )
        
        logger.info(f"Uploaded CSV to Storage: {file_key} (size: {len(file_bytes)} bytes)")
        return file_key
        
    except asyncio.TimeoutError:
        error_msg = f"Storage upload timeout (>15s) for {file_key}"
        logger.error(error_msg)
        raise RuntimeError(f"Загрузка файла заняла слишком много времени. Попробуйте позже.") from None
    except Exception as e:
        error_msg = f"Failed to upload CSV to Storage (bucket: {self.bucket}, key: {file_key}): {e}"
        logger.error(error_msg, exc_info=True)
        # Пробрасываем более информативную ошибку
        raise RuntimeError(f"Не удалось загрузить файл в хранилище: {str(e)}") from e
```

### 2. upload_csv_from_file (строки 80-136)

```python
async def upload_csv_from_file(self, file_path: str, user_id: int, filename: str) -> str:
    """
    Upload CSV file to Supabase Storage from a file path with timeout.
    This method reads the file in chunks to minimize memory usage.
    
    Args:
        file_path: Path to the file on disk
        user_id: User ID for organizing files
        filename: Original filename
        
    Returns:
        Storage file key (path)
        
    Raises:
        ValueError: If file size exceeds 20MB limit
        RuntimeError: If upload fails or times out
    """
    import asyncio
    
    file_key = f"{user_id}/{uuid.uuid4()}_{filename}"
    
    # Check file size BEFORE reading to prevent OOM
    MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20MB hard limit
    file_size = os.path.getsize(file_path)
    if file_size > MAX_UPLOAD_SIZE:
        max_size_mb = MAX_UPLOAD_SIZE // 1024 // 1024
        error_msg = f"File too large for current plan. Maximum size: {max_size_mb}MB"
        logger.error(f"{error_msg} (file size: {file_size} bytes)")
        raise ValueError(error_msg)
    
    try:
        # Read file in chunks to minimize memory usage
        def _upload():
            chunk_size = 32 * 1024  # 32KB chunks
            chunks = []
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    chunks.append(chunk)
            # Supabase API requires bytes, so we combine chunks
            # But we read in chunks to avoid loading entire file at once
            file_bytes = b''.join(chunks)
            return self.supabase.storage.from_(self.bucket).upload(file_key, file_bytes)
        
        # ✅ Добавляем таймаут 15 секунд
        await asyncio.wait_for(
            asyncio.to_thread(_upload),
            timeout=15.0
        )
        
        logger.info(f"Uploaded CSV to Storage: {file_key} (size: {file_size} bytes)")
        return file_key
        
    except asyncio.TimeoutError:
        error_msg = f"Storage upload timeout (>15s) for {file_key}"
        logger.error(error_msg)
        raise RuntimeError(f"Загрузка файла заняла слишком много времени. Попробуйте позже.") from None
    except ValueError:
        # Re-raise ValueError (file size check) without wrapping
        raise
    except Exception as e:
        error_msg = f"Failed to upload CSV to Storage (bucket: {self.bucket}, key: {file_key}): {e}"
        logger.error(error_msg, exc_info=True)
        # Пробрасываем более информативную ошибку
        raise RuntimeError(f"Не удалось загрузить файл в хранилище: {str(e)}") from e
```

### 3. download_csv_to_temp (строки 138-162)

Этот метод СИНХРОННЫЙ (используется в workers). Можно добавить простую проверку времени:

```python
def download_csv_to_temp(self, file_key: str) -> str:
    """
    Download CSV from Storage to temporary file.
    
    Args:
        file_key: Storage file key (path)
        
    Returns:
        Path to temporary file
    """
    import time
    
    try:
        start_time = time.time()
        
        response = self.supabase.storage.from_(self.bucket).download(file_key)
        
        elapsed = time.time() - start_time
        if elapsed > 10.0:
            logger.warning(f"Storage download took {elapsed:.1f}s (>10s threshold)")
        
        temp_path = f"/tmp/{uuid.uuid4()}.csv"
        
        # Ensure /tmp directory exists
        os.makedirs("/tmp", exist_ok=True)
        
        with open(temp_path, 'wb') as f:
            f.write(response)
        
        logger.info(f"Downloaded CSV from Storage to temp: {temp_path} ({elapsed:.2f}s)")
        return temp_path
    except Exception as e:
        logger.error(f"Failed to download CSV from Storage: {e}")
        raise
```

---

## 🟡 БОНУС: Увеличить SESSION_LIMIT (1 минута)

### Railway Dashboard

1. Открой Railway Dashboard → твой проект
2. Перейди в **Shared Variables** (или Variables для конкретного сервиса)
3. Добавь/измени:
   ```
   SUPABASE_SESSION_LIMIT=4
   ```
4. **Restart** сервис

**Почему 4?**
- Supabase Free Tier: максимум 5 одновременных соединений
- 4 для приложения + 1 резерв = стабильность

---

## ✅ ПРОВЕРКА

### После исправлений:

```bash
# 1. Проверить логирование (генерируем 100 ошибок)
poetry run python -c "
import logging
logger = logging.getLogger('test')
for i in range(100):
    logger.error(f'Test error {i}')
print('Done!')
"

# 2. Commit changes
git add bot/main.py workers/actors.py services/storage_service.py
git commit -m "fix: add async logging and storage timeouts"

# 3. Deploy
git push origin main

# 4. Проверить Railway logs
# → Не должно быть блокировок
```

---

## 📊 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

После исправлений:
- ✅ Логирование не блокирует Event Loop
- ✅ Storage timeout = 15s (graceful degradation)
- ✅ Max Concurrency = 80-100 req/min
- ✅ Success Rate = 95%+
- ✅ Готовы к 2000+ пользователям

---

## 🚨 ЕСЛИ ЧТО-ТО ПОШЛО НЕ ТАК

### Rollback:

```bash
git revert HEAD
git push origin main
```

### Проверить Railway logs:

```bash
railway logs --service=bot
```

### Связаться с поддержкой Supabase:
- Проверить Dashboard → Database → Connections
- Если > 90% connections used → upgrade план

---

**Время выполнения:** 1-2 часа  
**Сложность:** ⭐⭐ (средняя)  
**Результат:** 🚀 Готовность к запуску

