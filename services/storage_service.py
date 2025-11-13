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
        # Используем settings для получения конфигурации
        supabase_url = settings.supabase_url
        # Для Storage операций нужен SERVICE_ROLE_KEY, а не обычный ключ
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or settings.supabase_key
        
        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_KEY) environment variables must be set. "
                "For Storage operations, SERVICE_ROLE_KEY is recommended."
            )
        
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

