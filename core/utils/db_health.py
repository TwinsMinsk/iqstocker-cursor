"""Database health monitoring for PostgreSQL."""

import time
from typing import Dict, Any, Optional
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool

from config.database import engine, SessionLocal


class DatabaseHealthMonitor:
    """Monitor database health and performance metrics."""
    
    def __init__(self):
        self.engine = engine
        self.session_factory = SessionLocal
    
    def get_connection_pool_status(self) -> Dict[str, Any]:
        """Get connection pool status."""
        try:
            pool = self.engine.pool
            if isinstance(pool, QueuePool):
                return {
                    "pool_size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "invalid": pool.invalid()
                }
            else:
                return {"pool_type": type(pool).__name__}
        except Exception as e:
            return {"error": str(e)}
    
    def get_query_performance(self) -> Dict[str, Any]:
        """Get query performance metrics."""
        try:
            db = self.session_factory()
            
            # Test basic query performance
            start_time = time.time()
            result = db.execute(text("SELECT 1"))
            query_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Get database version
            version_result = db.execute(text("SELECT version()"))
            version = version_result.scalar()
            
            db.close()
            
            return {
                "query_time_ms": round(query_time, 2),
                "database_version": version.split()[0] if version else "Unknown",
                "status": "healthy" if query_time < 100 else "slow"
            }
        except Exception as e:
            return {"error": str(e), "status": "unhealthy"}
    
    def get_table_sizes(self) -> Dict[str, Any]:
        """Get table sizes and row counts."""
        try:
            db = self.session_factory()
            
            # Get table sizes (PostgreSQL specific)
            size_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """)
            
            result = db.execute(size_query)
            tables = []
            
            for row in result:
                tables.append({
                    "table": row.tablename,
                    "size": row.size,
                    "size_bytes": row.size_bytes
                })
            
            db.close()
            
            return {"tables": tables}
        except Exception as e:
            return {"error": str(e)}
    
    def get_active_connections(self) -> Dict[str, Any]:
        """Get active database connections."""
        try:
            db = self.session_factory()
            
            # Get active connections (PostgreSQL specific)
            conn_query = text("""
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """)
            
            result = db.execute(conn_query).fetchone()
            
            db.close()
            
            return {
                "total_connections": result.total_connections,
                "active_connections": result.active_connections,
                "idle_connections": result.idle_connections
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary."""
        return {
            "timestamp": time.time(),
            "connection_pool": self.get_connection_pool_status(),
            "performance": self.get_query_performance(),
            "table_sizes": self.get_table_sizes(),
            "connections": self.get_active_connections()
        }
    
    def is_healthy(self) -> bool:
        """Check if database is healthy."""
        try:
            performance = self.get_query_performance()
            return performance.get("status") == "healthy"
        except:
            return False


def get_db_health() -> Dict[str, Any]:
    """Get database health status."""
    monitor = DatabaseHealthMonitor()
    return monitor.get_health_summary()


def is_db_healthy() -> bool:
    """Quick health check."""
    monitor = DatabaseHealthMonitor()
    return monitor.is_healthy()
