"""Resource monitoring for bot performance tracking."""

import logging
import psutil
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """Мониторинг использования ресурсов."""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.memory_threshold_mb = 400  # Alert at 400MB (из 512MB)
        self.cpu_threshold_percent = 80
    
    def log_current_usage(self) -> dict:
        """Логирование текущего использования ресурсов."""
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        cpu_percent = self.process.cpu_percent(interval=0.1)
        
        logger.info(f"Resources: RAM={memory_mb:.1f}MB CPU={cpu_percent:.1f}%")
        
        # Алерты
        if memory_mb > self.memory_threshold_mb:
            logger.warning(f"HIGH MEMORY: {memory_mb:.1f}MB / 512MB")
        
        if cpu_percent > self.cpu_threshold_percent:
            logger.warning(f"HIGH CPU: {cpu_percent:.1f}%")
        
        return {
            "memory_mb": memory_mb,
            "cpu_percent": cpu_percent,
            "timestamp": datetime.now().isoformat()
        }
    
    def check_db_connections(self, session):
        """Проверка количества активных DB соединений."""
        try:
            from sqlalchemy import text
            result = session.execute(text(
                "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
            ))
            active_connections = result.scalar()
            logger.info(f"Active DB connections: {active_connections}")
            
            if active_connections > 4:
                logger.warning(f"High connection count: {active_connections}/5 (Supabase limit)")
            
            return active_connections
        except Exception as e:
            logger.error(f"Failed to check DB connections: {e}")
            return None

