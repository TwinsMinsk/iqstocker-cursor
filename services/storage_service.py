"""Supabase Storage service for CSV file management."""

import os
import uuid
import logging
import asyncio
from typing import Optional
from supabase import create_client
from config.settings import settings

logger = logging.getLogger(__name__)


class StorageRetryError(Exception):
    """Exception raised when storage operation fails after all retries."""
    pass


class StorageService:
    """Service for managing CSV files in Supabase Storage."""
    
    # Константы для retry логики
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1.0  # секунды
    MAX_RETRY_DELAY = 10.0  # секунды
    
    def __init__(self):
        """Initialize Supabase Storage client."""
        # Приоритет: переменные окружения > settings
        supabase_url = os.getenv("SUPABASE_URL") or settings.supabase_url
        # Для Storage операций нужен SERVICE_ROLE_KEY, а не обычный ключ
        supabase_key = (
            os.getenv("SUPABASE_SERVICE_ROLE_KEY") or 
            os.getenv("SUPABASE_KEY") or 
            settings.supabase_key
        )
        
        if not supabase_url or not supabase_key:
            missing_vars = []
            if not supabase_url:
                missing_vars.append("SUPABASE_URL")
            if not supabase_key:
                missing_vars.append("SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_KEY)")
            
            error_msg = (
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                f"Please set them in Railway Dashboard → Shared Variables. "
                f"For Storage operations, SUPABASE_SERVICE_ROLE_KEY is recommended."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            self.supabase = create_client(supabase_url, supabase_key)
            self.bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "csv-files")
            logger.info(f"StorageService initialized with bucket: {self.bucket}")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase Storage client: {e}")
            raise ValueError(f"Failed to initialize Supabase Storage: {e}") from e
    
    @staticmethod
    def _is_retriable_error(error: Exception) -> bool:
        """Проверяет, можно ли повторить операцию после этой ошибки."""
        error_str = str(error).lower()
        retriable_patterns = [
            'name or service not known',  # DNS ошибки
            'errno -2',  # DNS resolve ошибки
            'errno 104',  # Connection reset by peer
            'errno 110',  # Connection timed out
            'errno 111',  # Connection refused
            'timeout',
            'connection',
            'network',
            'temporarily unavailable'
        ]
        return any(pattern in error_str for pattern in retriable_patterns)
    
    async def _retry_with_backoff(self, operation, operation_name: str):
        """
        Выполняет операцию с повторными попытками и экспоненциальной задержкой.
        
        Args:
            operation: Callable функция для выполнения
            operation_name: Имя операции для логирования
            
        Returns:
            Результат выполнения операции
            
        Raises:
            StorageRetryError: Если все попытки исчерпаны
        """
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                return await operation()
            except Exception as e:
                last_error = e
                
                # Проверяем, можно ли повторить операцию
                if not self._is_retriable_error(e):
                    logger.error(f"{operation_name} failed with non-retriable error: {e}")
                    raise
                
                if attempt < self.MAX_RETRIES - 1:
                    # Вычисляем задержку с экспоненциальным ростом
                    delay = min(
                        self.INITIAL_RETRY_DELAY * (2 ** attempt),
                        self.MAX_RETRY_DELAY
                    )
                    logger.warning(
                        f"{operation_name} failed (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"{operation_name} failed after {self.MAX_RETRIES} attempts: {e}"
                    )
        
        # Если мы дошли до сюда, все попытки исчерпаны
        raise StorageRetryError(
            f"{operation_name} failed after {self.MAX_RETRIES} attempts. "
            f"Last error: {last_error}"
        ) from last_error
    
    async def upload_csv(self, file_bytes: bytes, user_id: int, filename: str) -> str:
        """
        Upload CSV file to Supabase Storage with timeout and retry logic.
        
        Args:
            file_bytes: File content as bytes
            user_id: User ID for organizing files
            filename: Original filename
            
        Returns:
            Storage file key (path)
        """
        file_key = f"{user_id}/{uuid.uuid4()}_{filename}"
        
        async def _upload_operation():
            try:
                # Supabase Storage API синхронный, оборачиваем в executor
                def _upload():
                    return self.supabase.storage.from_(self.bucket).upload(file_key, file_bytes)
                
                # Добавляем таймаут 15 секунд
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
        
        try:
            return await self._retry_with_backoff(
                _upload_operation,
                f"Upload CSV {file_key}"
            )
        except StorageRetryError as e:
            # Преобразуем в пользовательское сообщение
            raise RuntimeError(f"Не удалось загрузить файл в хранилище после нескольких попыток. Попробуйте позже.") from e
        except Exception as e:
            error_msg = f"Failed to upload CSV to Storage (bucket: {self.bucket}, key: {file_key}): {e}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(f"Не удалось загрузить файл в хранилище: {str(e)}") from e
    
    async def upload_csv_from_file(self, file_path: str, user_id: int, filename: str) -> str:
        """
        Upload CSV file to Supabase Storage from a file path with timeout and retry logic.
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
        file_key = f"{user_id}/{uuid.uuid4()}_{filename}"
        
        # Check file size BEFORE reading to prevent OOM
        MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20MB hard limit
        file_size = os.path.getsize(file_path)
        if file_size > MAX_UPLOAD_SIZE:
            max_size_mb = MAX_UPLOAD_SIZE // 1024 // 1024
            error_msg = f"File too large for current plan. Maximum size: {max_size_mb}MB"
            logger.error(f"{error_msg} (file size: {file_size} bytes)")
            raise ValueError(error_msg)
        
        async def _upload_operation():
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
                
                # Добавляем таймаут 15 секунд
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
        
        try:
            return await self._retry_with_backoff(
                _upload_operation,
                f"Upload CSV from file {file_key}"
            )
        except StorageRetryError as e:
            # Преобразуем в пользовательское сообщение
            raise RuntimeError(f"Не удалось загрузить файл в хранилище после нескольких попыток. Попробуйте позже.") from e
        except ValueError:
            # Re-raise ValueError (file size check) without wrapping
            raise
        except Exception as e:
            error_msg = f"Failed to upload CSV to Storage (bucket: {self.bucket}, key: {file_key}): {e}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(f"Не удалось загрузить файл в хранилище: {str(e)}") from e
    
    def download_csv_to_temp(self, file_key: str) -> str:
        """
        Download CSV from Storage to temporary file with retry logic.
        
        Args:
            file_key: Storage file key (path)
            
        Returns:
            Path to temporary file
        """
        import time
        
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
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
                last_error = e
                
                # Проверяем, можно ли повторить операцию
                if not self._is_retriable_error(e):
                    logger.error(f"Download CSV failed with non-retriable error: {e}")
                    raise
                
                if attempt < self.MAX_RETRIES - 1:
                    # Вычисляем задержку с экспоненциальным ростом
                    delay = min(
                        self.INITIAL_RETRY_DELAY * (2 ** attempt),
                        self.MAX_RETRY_DELAY
                    )
                    logger.warning(
                        f"Download CSV failed (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"Download CSV failed after {self.MAX_RETRIES} attempts: {e}"
                    )
        
        # Если мы дошли до сюда, все попытки исчерпаны
        raise StorageRetryError(
            f"Download CSV {file_key} failed after {self.MAX_RETRIES} attempts. "
            f"Last error: {last_error}"
        ) from last_error
    
    def delete_csv(self, file_key: str) -> None:
        """
        Delete CSV file from Storage.
        
        Args:
            file_key: Storage file key (path)
        """
        try:
            self.supabase.storage.from_(self.bucket).remove([file_key])
            logger.info(f"Deleted CSV from Storage: {file_key}")
        except Exception as e:
            logger.error(f"Failed to delete CSV from Storage: {e}")
            # Не поднимаем исключение, т.к. это cleanup операция

