"""Broadcast system for admin messages."""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from config.database import SessionLocal
from database.models import User, SubscriptionType, BroadcastMessage
from core.notifications.notification_manager import get_notification_manager


class BroadcastManager:
    """Manager for broadcast messages and admin functions."""

    def __init__(self, bot=None):
        self.bot = bot
        self.db = SessionLocal()
        self.notification_manager = get_notification_manager(bot)

    def __del__(self):
        """Close database session."""
        if hasattr(self, 'db'):
            self.db.close()

    async def send_broadcast(
        self,
        message: str,
        subscription_type: Optional[SubscriptionType] = None,
        admin_user_id: int = None
    ) -> Dict[str, Any]:
        """Send broadcast message to users."""

        try:
            # Get target users
            query = self.db.query(User)
            if subscription_type:
                query = query.filter(User.subscription_type == subscription_type)

            users = query.all()
            total_users = len(users)

            if total_users == 0:
                return {
                    "success": False,
                    "message": "No users found for broadcast",
                    "sent_count": 0,
                    "total_users": 0
                }

            # Send messages
            sent_count = 0
            failed_count = 0

            for user in users:
                try:
                    success = await self.notification_manager.send_notification(
                        user.telegram_id,
                        message
                    )
                    if success:
                        sent_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    print(f"Error sending to user {user.telegram_id}: {e}")
                    failed_count += 1

                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)

            # Save broadcast record
            broadcast_record = BroadcastMessage(
                message=message,
                subscription_type=subscription_type.value if subscription_type else None,
                recipients_count=total_users,
                sent_count=sent_count,
                failed_count=failed_count,
                admin_user_id=admin_user_id,
                sent_at=datetime.now(timezone.utc)
            )
            self.db.add(broadcast_record)
            self.db.commit()

            return {
                "success": True,
                "message": f"Broadcast sent successfully",
                "sent_count": sent_count,
                "failed_count": failed_count,
                "total_users": total_users,
                "broadcast_id": broadcast_record.id
            }

        except Exception as e:
            print(f"Error sending broadcast: {e}")
            self.db.rollback()
            return {
                "success": False,
                "message": f"Error sending broadcast: {e}",
                "sent_count": 0,
                "total_users": 0
            }

    def get_broadcast_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get broadcast message history."""

        try:
            broadcasts = self.db.query(BroadcastMessage).order_by(
                desc(BroadcastMessage.sent_at)
            ).limit(limit).all()

            return [
                {
                    "id": broadcast.id,
                    "message": broadcast.message[:100] + "..." if len(broadcast.message) > 100 else broadcast.message,
                    "subscription_type": broadcast.subscription_type,
                    "recipients_count": broadcast.recipients_count,
                    "sent_count": broadcast.sent_count,
                    "failed_count": broadcast.failed_count,
                    "sent_at": broadcast.sent_at.strftime("%d.%m.%Y %H:%M"),
                    "success_rate": round((broadcast.sent_count / broadcast.recipients_count * 100), 1) if broadcast.recipients_count > 0 else 0
                }
                for broadcast in broadcasts
            ]

        except Exception as e:
            print(f"Error getting broadcast history: {e}")
            return []

    def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics for admin panel."""

        try:
            # Total users
            total_users = self.db.query(User).count()

            # Users by subscription type
            subscription_stats = {}
            for subscription_type in SubscriptionType:
                count = self.db.query(User).filter(User.subscription_type == subscription_type).count()
                subscription_stats[subscription_type.value] = count

            # Recent users (last 30 days)
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            recent_users = self.db.query(User).filter(User.created_at >= thirty_days_ago).count()

            # Active users (with limits used)
            active_users = self.db.query(User).join(User.limits).filter(
                User.limits.has(
                    (User.limits.analytics_used > 0) |
                    (User.limits.themes_used > 0) |
                    (User.limits.top_themes_used > 0)
                )
            ).count()

            return {
                "total_users": total_users,
                "subscription_stats": subscription_stats,
                "recent_users": recent_users,
                "active_users": active_users,
                "last_updated": datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M")
            }

        except Exception as e:
            print(f"Error getting user statistics: {e}")
            return {}

    def update_new_works_parameter(self, months: int) -> bool:
        """Update the 'new works' parameter for analytics."""

        try:
            # This would typically update a configuration table
            # For now, we'll just log the change
            print(f"Updated new works parameter to {months} months")

            # In a real implementation, you would:
            # 1. Update a config table
            # 2. Invalidate cached analytics
            # 3. Notify users if needed

            return True

        except Exception as e:
            print(f"Error updating new works parameter: {e}")
            return False

    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status."""

        try:
            # Database connection test
            db_healthy = True
            try:
                self.db.execute("SELECT 1")
            except Exception:
                db_healthy = False

            # Bot status
            bot_healthy = self.bot is not None

            # Recent errors (simplified)
            recent_errors = 0  # Would be implemented with proper error tracking

            return {
                "database": "healthy" if db_healthy else "unhealthy",
                "bot": "healthy" if bot_healthy else "unhealthy",
                "recent_errors": recent_errors,
                "last_check": datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M")
            }

        except Exception as e:
            print(f"Error checking system health: {e}")
            return {
                "database": "unknown",
                "bot": "unknown",
                "recent_errors": 0,
                "last_check": datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M")
            }


# Global broadcast manager instance
broadcast_manager = None


def get_broadcast_manager(bot=None) -> BroadcastManager:
    """Get global broadcast manager instance."""
    global broadcast_manager
    if broadcast_manager is None:
        broadcast_manager = BroadcastManager(bot)
    return broadcast_manager
