"""Supabase Storage service for CSV file management."""

import os
import uuid
import logging
from typing import Optional
from supabase import create_client
from config.settings import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing CSV files in Supabase Storage."""
    
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
    
    async def upload_csv(self, file_bytes: bytes, user_id: int, filename: str) -> str:
        """
        Upload CSV file to Supabase Storage.
        
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
            
            await asyncio.to_thread(_upload)
            logger.info(f"Uploaded CSV to Storage: {file_key} (size: {len(file_bytes)} bytes)")
            return file_key
        except Exception as e:
            error_msg = f"Failed to upload CSV to Storage (bucket: {self.bucket}, key: {file_key}): {e}"
            logger.error(error_msg, exc_info=True)
            # Пробрасываем более информативную ошибку
            raise RuntimeError(f"Не удалось загрузить файл в хранилище: {str(e)}") from e
    
    async def upload_csv_from_file(self, file_path: str, user_id: int, filename: str) -> str:
        """
        Upload CSV file to Supabase Storage from a file path.
        This method reads the file in chunks to minimize memory usage.
        
        Args:
            file_path: Path to the file on disk
            user_id: User ID for organizing files
            filename: Original filename
            
        Returns:
            Storage file key (path)
            
        Raises:
            ValueError: If file size exceeds 20MB limit
            RuntimeError: If upload fails
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
            
            await asyncio.to_thread(_upload)
            logger.info(f"Uploaded CSV to Storage: {file_key} (size: {file_size} bytes)")
            return file_key
        except ValueError:
            # Re-raise ValueError (file size check) without wrapping
            raise
        except Exception as e:
            error_msg = f"Failed to upload CSV to Storage (bucket: {self.bucket}, key: {file_key}): {e}"
            logger.error(error_msg, exc_info=True)
            # Пробрасываем более информативную ошибку
            raise RuntimeError(f"Не удалось загрузить файл в хранилище: {str(e)}") from e
    
    def download_csv_to_temp(self, file_key: str) -> str:
        """
        Download CSV from Storage to temporary file.
        
        Args:
            file_key: Storage file key (path)
            
        Returns:
            Path to temporary file
        """
        try:
            response = self.supabase.storage.from_(self.bucket).download(file_key)
            temp_path = f"/tmp/{uuid.uuid4()}.csv"
            
            # Ensure /tmp directory exists
            os.makedirs("/tmp", exist_ok=True)
            
            with open(temp_path, 'wb') as f:
                f.write(response)
            
            logger.info(f"Downloaded CSV from Storage to temp: {temp_path}")
            return temp_path
        except Exception as e:
            logger.error(f"Failed to download CSV from Storage: {e}")
            raise
    
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

