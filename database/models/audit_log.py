"""Audit Log model for tracking admin actions."""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from config.database import Base


class AuditLog(Base):
    """Audit Log model for tracking admin actions."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    
    # Admin user info
    admin_username = Column(String(100), nullable=False)
    admin_ip = Column(String(45), nullable=True)  # IPv6 support
    
    # Action details
    action = Column(String(100), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT, etc.
    resource_type = Column(String(100), nullable=True)  # User, Subscription, etc.
    resource_id = Column(String(100), nullable=True)  # ID of the affected resource
    
    # Request details
    request_method = Column(String(10), nullable=True)  # GET, POST, PUT, DELETE
    request_path = Column(String(500), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Changes tracking
    old_values = Column(JSON, nullable=True)  # Previous values
    new_values = Column(JSON, nullable=True)  # New values
    
    # Additional context
    description = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)  # Additional data (renamed from metadata)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
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
