"""Audit Log model for tracking admin actions."""

from datetime import datetime
from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from config.database import Base


class AuditLog(Base):
    """Audit Log model for tracking admin actions."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    log_id: Mapped[str] = mapped_column(
        String(36), 
        default=lambda: str(uuid.uuid4()), 
        unique=True, 
        index=True
    )
    
    # Admin user info
    admin_username: Mapped[str] = mapped_column(String(100))
    admin_ip: Mapped[str] = mapped_column(String(45), nullable=True)  # IPv6 support
    
    # Action details
    action: Mapped[str] = mapped_column(String(100))  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT, etc.
    resource_type: Mapped[str] = mapped_column(String(100), nullable=True)  # User, Subscription, etc.
    resource_id: Mapped[str] = mapped_column(String(100), nullable=True)  # ID of the affected resource
    
    # Request details
    request_method: Mapped[str] = mapped_column(String(10), nullable=True)  # GET, POST, PUT, DELETE
    request_path: Mapped[str] = mapped_column(String(500), nullable=True)
    user_agent: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Changes tracking
    old_values: Mapped[dict] = mapped_column(JSON, nullable=True)  # Previous values
    new_values: Mapped[dict] = mapped_column(JSON, nullable=True)  # New values
    
    # Additional context
    description: Mapped[str] = mapped_column(Text, nullable=True)
    extra_data: Mapped[dict] = mapped_column(JSON, nullable=True)  # Additional data (renamed from metadata)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, admin={self.admin_username})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'log_id': self.log_id,
            'admin_username': self.admin_username,
            'admin_ip': self.admin_ip,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'request_method': self.request_method,
            'request_path': self.request_path,
            'user_agent': self.user_agent,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'description': self.description,
            'extra_data': self.extra_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
