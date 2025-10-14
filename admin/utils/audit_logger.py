"""Audit Logger for tracking admin actions."""

import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from config.database import SessionLocal
from database.models.audit_log import AuditLog


class AuditLogger:
    """Handles audit logging for admin actions."""

    def __init__(self):
        self.db: Session = SessionLocal()

    def log_action(
        self,
        admin_username: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        admin_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Log an admin action."""
        
        try:
            audit_log = AuditLog(
                admin_username=admin_username,
                admin_ip=admin_ip,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                request_method=request_method,
                request_path=request_path,
                user_agent=user_agent,
                old_values=old_values,
                new_values=new_values,
                description=description,
                extra_data=extra_data,
                created_at=datetime.utcnow()
            )
            
            self.db.add(audit_log)
            self.db.commit()
            self.db.refresh(audit_log)
            
            return audit_log
            
        except Exception as e:
            self.db.rollback()
            print(f"Error logging audit action: {e}")
            raise

    def log_login(self, admin_username: str, admin_ip: str, user_agent: str) -> AuditLog:
        """Log admin login."""
        return self.log_action(
            admin_username=admin_username,
            action="LOGIN",
            description=f"Admin {admin_username} logged in",
            admin_ip=admin_ip,
            user_agent=user_agent
        )

    def log_logout(self, admin_username: str, admin_ip: str) -> AuditLog:
        """Log admin logout."""
        return self.log_action(
            admin_username=admin_username,
            action="LOGOUT",
            description=f"Admin {admin_username} logged out",
            admin_ip=admin_ip
        )

    def log_create(
        self,
        admin_username: str,
        resource_type: str,
        resource_id: str,
        new_values: Dict[str, Any],
        admin_ip: str = None
    ) -> AuditLog:
        """Log resource creation."""
        return self.log_action(
            admin_username=admin_username,
            action="CREATE",
            resource_type=resource_type,
            resource_id=resource_id,
            new_values=new_values,
            description=f"Created {resource_type} with ID {resource_id}",
            admin_ip=admin_ip
        )

    def log_update(
        self,
        admin_username: str,
        resource_type: str,
        resource_id: str,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        admin_ip: str = None
    ) -> AuditLog:
        """Log resource update."""
        return self.log_action(
            admin_username=admin_username,
            action="UPDATE",
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            description=f"Updated {resource_type} with ID {resource_id}",
            admin_ip=admin_ip
        )

    def log_delete(
        self,
        admin_username: str,
        resource_type: str,
        resource_id: str,
        old_values: Dict[str, Any],
        admin_ip: str = None
    ) -> AuditLog:
        """Log resource deletion."""
        return self.log_action(
            admin_username=admin_username,
            action="DELETE",
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            description=f"Deleted {resource_type} with ID {resource_id}",
            admin_ip=admin_ip
        )

    def log_bulk_action(
        self,
        admin_username: str,
        action: str,
        resource_type: str,
        affected_ids: List[str],
        description: str,
        admin_ip: str = None
    ) -> AuditLog:
        """Log bulk actions."""
        return self.log_action(
            admin_username=admin_username,
            action=f"BULK_{action}",
            resource_type=resource_type,
            description=description,
            extra_data={"affected_ids": affected_ids, "count": len(affected_ids)},
            admin_ip=admin_ip
        )

    def get_audit_logs(
        self,
        admin_username: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Get audit logs with filters."""
        
        query = self.db.query(AuditLog)
        
        if admin_username:
            query = query.filter(AuditLog.admin_username == admin_username)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        return query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()

    def get_admin_activity_summary(self, admin_username: str, days: int = 30) -> Dict[str, Any]:
        """Get activity summary for an admin user."""
        
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        logs = self.db.query(AuditLog).filter(
            AuditLog.admin_username == admin_username,
            AuditLog.created_at >= cutoff_date
        ).all()
        
        # Count actions by type
        action_counts = {}
        for log in logs:
            action_counts[log.action] = action_counts.get(log.action, 0) + 1
        
        # Get recent activity
        recent_logs = logs[:10]  # Last 10 actions
        
        return {
            "total_actions": len(logs),
            "action_counts": action_counts,
            "recent_actions": [log.to_dict() for log in recent_logs],
            "period_days": days
        }

    def close(self):
        """Close the database session."""
        self.db.close()
