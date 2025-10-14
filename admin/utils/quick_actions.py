"""
Quick Actions Module for IQStocker Admin Panel
Provides bulk operations and export functionality
"""

import csv
import io
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from config.database import SessionLocal
from database.models import (
    User, Subscription, Limits, CSVAnalysis, AnalyticsReport,
    TopTheme, ThemeRequest, GlobalTheme, VideoLesson, CalendarEntry, BroadcastMessage
)


class QuickActions:
    """Handles bulk operations and data exports"""
    
    def __init__(self):
        self.db: Session = SessionLocal()
    
    def bulk_update_subscription(self, user_ids: List[int], subscription_type: str, duration_days: int = 30) -> Dict[str, Any]:
        """Update subscription for multiple users"""
        try:
            updated_count = 0
            errors = []
            
            for user_id in user_ids:
                try:
                    # Get user
                    user = self.db.query(User).filter(User.id == user_id).first()
                    if not user:
                        errors.append(f"User {user_id} not found")
                        continue
                    
                    # Update user subscription
                    user.subscription_type = subscription_type
                    user.subscription_expires_at = datetime.utcnow() + timedelta(days=duration_days)
                    
                    # Create subscription record
                    subscription = Subscription(
                        user_id=user_id,
                        subscription_type=subscription_type,
                        started_at=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(days=duration_days),
                        payment_id=f"bulk_update_{datetime.utcnow().timestamp()}"
                    )
                    self.db.add(subscription)
                    
                    # Update limits based on subscription type
                    limits = self.db.query(Limits).filter(Limits.user_id == user_id).first()
                    if limits:
                        self._update_limits_for_subscription(limits, subscription_type)
                    
                    updated_count += 1
                    
                except Exception as e:
                    errors.append(f"Error updating user {user_id}: {str(e)}")
            
            self.db.commit()
            
            return {
                'success': True,
                'updated_count': updated_count,
                'total_requested': len(user_ids),
                'errors': errors
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                'success': False,
                'error': str(e),
                'updated_count': 0
            }
    
    def bulk_reset_limits(self, user_ids: List[int]) -> Dict[str, Any]:
        """Reset limits for multiple users"""
        try:
            updated_count = 0
            errors = []
            
            for user_id in user_ids:
                try:
                    limits = self.db.query(Limits).filter(Limits.user_id == user_id).first()
                    if limits:
                        limits.analytics_used = 0
                        limits.themes_used = 0
                        limits.top_themes_used = 0
                        updated_count += 1
                    else:
                        errors.append(f"Limits not found for user {user_id}")
                        
                except Exception as e:
                    errors.append(f"Error resetting limits for user {user_id}: {str(e)}")
            
            self.db.commit()
            
            return {
                'success': True,
                'updated_count': updated_count,
                'total_requested': len(user_ids),
                'errors': errors
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                'success': False,
                'error': str(e),
                'updated_count': 0
            }
    
    def export_users_csv(self, filters: Dict[str, Any] = None) -> str:
        """Export users to CSV"""
        try:
            query = self.db.query(User)
            
            # Apply filters
            if filters:
                if 'subscription_type' in filters:
                    query = query.filter(User.subscription_type == filters['subscription_type'])
                if 'created_after' in filters:
                    query = query.filter(User.created_at >= filters['created_after'])
                if 'created_before' in filters:
                    query = query.filter(User.created_at <= filters['created_before'])
                if 'is_active' in filters:
                    if filters['is_active']:
                        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                        query = query.filter(User.last_activity_at >= thirty_days_ago)
            
            users = query.all()
            
            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'ID', 'Telegram ID', 'Username', 'First Name', 'Last Name',
                'Subscription Type', 'Subscription Expires At', 'Created At',
                'Last Activity At', 'Is Active'
            ])
            
            # Write data
            for user in users:
                writer.writerow([
                    user.id,
                    user.telegram_id,
                    user.username or '',
                    user.first_name or '',
                    user.last_name or '',
                    user.subscription_type.value if hasattr(user.subscription_type, 'value') else str(user.subscription_type),
                    user.subscription_expires_at.isoformat() if user.subscription_expires_at else '',
                    user.created_at.isoformat(),
                    user.last_activity_at.isoformat() if user.last_activity_at else '',
                    'Yes' if user.last_activity_at and user.last_activity_at >= datetime.utcnow() - timedelta(days=30) else 'No'
                ])
            
            return output.getvalue()
            
        except Exception as e:
            raise Exception(f"Error exporting users: {str(e)}")
    
    def export_analytics_csv(self, filters: Dict[str, Any] = None) -> str:
        """Export analytics data to CSV"""
        try:
            query = self.db.query(CSVAnalysis)
            
            # Apply filters
            if filters:
                if 'user_id' in filters:
                    query = query.filter(CSVAnalysis.user_id == filters['user_id'])
                if 'status' in filters:
                    query = query.filter(CSVAnalysis.status == filters['status'])
                if 'created_after' in filters:
                    query = query.filter(CSVAnalysis.created_at >= filters['created_after'])
                if 'created_before' in filters:
                    query = query.filter(CSVAnalysis.created_at <= filters['created_before'])
            
            analyses = query.all()
            
            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'ID', 'User ID', 'File Path', 'Status', 'Created At',
                'Processed At', 'Total Sales', 'Total Revenue', 'Portfolio Sold %'
            ])
            
            # Write data
            for analysis in analyses:
                # Get analytics report if exists
                report = self.db.query(AnalyticsReport).filter(
                    AnalyticsReport.csv_analysis_id == analysis.id
                ).first()
                
                writer.writerow([
                    analysis.id,
                    analysis.user_id,
                    analysis.file_path,
                    analysis.status,
                    analysis.created_at.isoformat(),
                    analysis.processed_at.isoformat() if analysis.processed_at else '',
                    report.total_sales if report else '',
                    report.total_revenue if report else '',
                    report.portfolio_sold_percent if report else ''
                ])
            
            return output.getvalue()
            
        except Exception as e:
            raise Exception(f"Error exporting analytics: {str(e)}")
    
    def export_themes_csv(self, filters: Dict[str, Any] = None) -> str:
        """Export theme data to CSV"""
        try:
            query = self.db.query(TopTheme)
            
            # Apply filters
            if filters:
                if 'csv_analysis_id' in filters:
                    query = query.filter(TopTheme.csv_analysis_id == filters['csv_analysis_id'])
                if 'min_sales' in filters:
                    query = query.filter(TopTheme.sales_count >= filters['min_sales'])
                if 'min_revenue' in filters:
                    query = query.filter(TopTheme.revenue >= filters['min_revenue'])
            
            themes = query.all()
            
            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'ID', 'CSV Analysis ID', 'Theme Name', 'Sales Count',
                'Revenue', 'Rank', 'Created At'
            ])
            
            # Write data
            for theme in themes:
                writer.writerow([
                    theme.id,
                    theme.csv_analysis_id,
                    theme.theme_name,
                    theme.sales_count,
                    theme.revenue,
                    theme.rank,
                    theme.created_at.isoformat()
                ])
            
            return output.getvalue()
            
        except Exception as e:
            raise Exception(f"Error exporting themes: {str(e)}")
    
    def send_bulk_notification(self, user_ids: List[int], message: str, notification_type: str = 'info') -> Dict[str, Any]:
        """Send notification to multiple users"""
        try:
            sent_count = 0
            errors = []
            
            for user_id in user_ids:
                try:
                    user = self.db.query(User).filter(User.id == user_id).first()
                    if not user:
                        errors.append(f"User {user_id} not found")
                        continue
                    
                    # Create broadcast message record
                    broadcast = BroadcastMessage(
                        text=message,
                        recipients_count=1,
                        sent_at=datetime.utcnow(),
                        created_at=datetime.utcnow()
                    )
                    self.db.add(broadcast)
                    
                    # In a real implementation, you would send the actual notification here
                    # For now, we just log it
                    print(f"Sending notification to user {user_id}: {message}")
                    
                    sent_count += 1
                    
                except Exception as e:
                    errors.append(f"Error sending notification to user {user_id}: {str(e)}")
            
            self.db.commit()
            
            return {
                'success': True,
                'sent_count': sent_count,
                'total_requested': len(user_ids),
                'errors': errors
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                'success': False,
                'error': str(e),
                'sent_count': 0
            }
    
    def bulk_delete_analyses(self, analysis_ids: List[int]) -> Dict[str, Any]:
        """Delete multiple CSV analyses"""
        try:
            deleted_count = 0
            errors = []
            
            for analysis_id in analysis_ids:
                try:
                    analysis = self.db.query(CSVAnalysis).filter(CSVAnalysis.id == analysis_id).first()
                    if analysis:
                        # Delete related records first
                        self.db.query(AnalyticsReport).filter(
                            AnalyticsReport.csv_analysis_id == analysis_id
                        ).delete()
                        self.db.query(TopTheme).filter(
                            TopTheme.csv_analysis_id == analysis_id
                        ).delete()
                        
                        # Delete the analysis
                        self.db.delete(analysis)
                        deleted_count += 1
                    else:
                        errors.append(f"Analysis {analysis_id} not found")
                        
                except Exception as e:
                    errors.append(f"Error deleting analysis {analysis_id}: {str(e)}")
            
            self.db.commit()
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'total_requested': len(analysis_ids),
                'errors': errors
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                'success': False,
                'error': str(e),
                'deleted_count': 0
            }
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        try:
            total_users = self.db.query(User).count()
            
            # Subscription distribution
            subscription_stats = self.db.query(
                User.subscription_type,
                self.db.query(User).filter(User.subscription_type == User.subscription_type).count().label('count')
            ).group_by(User.subscription_type).all()
            
            # Active users (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            active_users = self.db.query(User).filter(
                User.last_activity_at >= thirty_days_ago
            ).count()
            
            # New users (last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            new_users = self.db.query(User).filter(
                User.created_at >= seven_days_ago
            ).count()
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'new_users_7d': new_users,
                'subscription_distribution': {
                    sub_type.value if hasattr(sub_type, 'value') else str(sub_type): count
                    for sub_type, count in subscription_stats
                }
            }
            
        except Exception as e:
            raise Exception(f"Error getting user statistics: {str(e)}")
    
    def _update_limits_for_subscription(self, limits: Limits, subscription_type: str):
        """Update limits based on subscription type"""
        from config.settings import settings
        
        if subscription_type == 'FREE':
            limits.analytics_total = settings.free_analytics_limit
            limits.themes_total = settings.free_themes_limit
            limits.top_themes_total = 0
        elif subscription_type == 'TEST_PRO':
            limits.analytics_total = settings.test_pro_analytics_limit
            limits.themes_total = settings.test_pro_themes_limit
            limits.top_themes_total = 0
        elif subscription_type == 'PRO':
            limits.analytics_total = settings.pro_analytics_limit
            limits.themes_total = settings.pro_themes_limit
            limits.top_themes_total = settings.pro_top_themes_limit
        elif subscription_type == 'ULTRA':
            limits.analytics_total = settings.ultra_analytics_limit
            limits.themes_total = settings.ultra_themes_limit
            limits.top_themes_total = settings.ultra_top_themes_limit
        
        # Reset used counters
        limits.analytics_used = 0
        limits.themes_used = 0
        limits.top_themes_used = 0
    
    def close(self):
        """Close database session"""
        if self.db:
            self.db.close()
