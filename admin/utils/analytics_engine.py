"""
Analytics Engine for IQStocker Admin Panel
Provides comprehensive metrics for dashboard and reporting
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from config.database import SessionLocal
from database.models import (
    User, Subscription, Limits, CSVAnalysis, AnalyticsReport,
    TopTheme, ThemeRequest, VideoLesson, CalendarEntry, BroadcastMessage
)


class AnalyticsEngine:
    """Main analytics engine for calculating metrics and KPIs"""
    
    def __init__(self):
        self.db: Session = SessionLocal()
    
    def get_user_metrics(self) -> Dict[str, Any]:
        """Get comprehensive user metrics"""
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)
        
        # Total users
        total_users = self.db.query(User).count()
        
        # Active users (logged in within last 30 days)
        active_users = self.db.query(User).filter(
            User.last_activity_at >= thirty_days_ago
        ).count()
        
        # New users (registered in last 30 days)
        new_users_30d = self.db.query(User).filter(
            User.created_at >= thirty_days_ago
        ).count()
        
        # New users (registered in last 7 days)
        new_users_7d = self.db.query(User).filter(
            User.created_at >= seven_days_ago
        ).count()
        
        # Subscription distribution
        subscription_dist = self.db.query(
            User.subscription_type,
            func.count(User.id).label('count')
        ).group_by(User.subscription_type).all()
        
        subscription_distribution = {
            sub_type.value if hasattr(sub_type, 'value') else str(sub_type): count
            for sub_type, count in subscription_dist
        }
        
        # User growth over time (last 12 months)
        growth_data = []
        for i in range(12):
            month_start = now - timedelta(days=30 * (i + 1))
            month_end = now - timedelta(days=30 * i)
            
            users_in_month = self.db.query(User).filter(
                and_(
                    User.created_at >= month_start,
                    User.created_at < month_end
                )
            ).count()
            
            growth_data.append({
                'month': month_start.strftime('%Y-%m'),
                'users': users_in_month
            })
        
        growth_data.reverse()  # Show oldest to newest
        
        return {
            'total': total_users,
            'active': active_users,
            'new_30d': new_users_30d,
            'new_7d': new_users_7d,
            'subscription_distribution': subscription_distribution,
            'growth_data': growth_data,
            'activity_rate': (active_users / total_users * 100) if total_users > 0 else 0
        }
    
    def get_financial_metrics(self) -> Dict[str, Any]:
        """Get financial metrics and revenue data"""
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        
        # Total subscriptions
        total_subscriptions = self.db.query(Subscription).count()
        
        # Active subscriptions (not expired)
        active_subscriptions = self.db.query(Subscription).filter(
            Subscription.expires_at > now
        ).count()
        
        # Revenue by subscription type (estimated based on subscription counts)
        # Note: In a real implementation, you'd have actual payment data
        subscription_revenue = {
            'FREE': 0,
            'TEST_PRO': active_subscriptions * 0,  # Free trial
            'PRO': active_subscriptions * 10,       # Estimated $10/month
            'ULTRA': active_subscriptions * 25      # Estimated $25/month
        }
        
        total_revenue = sum(subscription_revenue.values())
        
        # Monthly recurring revenue (MRR)
        mrr = total_revenue
        
        # Average revenue per user (ARPU)
        total_users = self.db.query(User).count()
        arpu = total_revenue / total_users if total_users > 0 else 0
        
        # Conversion rates
        free_users = self.db.query(User).filter(
            User.subscription_type == 'FREE'
        ).count()
        
        paid_users = self.db.query(User).filter(
            User.subscription_type.in_(['PRO', 'ULTRA'])
        ).count()
        
        conversion_rate = (paid_users / total_users * 100) if total_users > 0 else 0
        
        # Churn rate (users who didn't renew)
        expired_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.expires_at < now,
                Subscription.expires_at >= thirty_days_ago
            )
        ).count()
        
        churn_rate = (expired_subscriptions / total_subscriptions * 100) if total_subscriptions > 0 else 0
        
        # Revenue trends (last 6 months)
        revenue_trends = []
        for i in range(6):
            month_start = now - timedelta(days=30 * (i + 1))
            month_end = now - timedelta(days=30 * i)
            
            # Simplified revenue calculation
            month_subscriptions = self.db.query(Subscription).filter(
                and_(
                    Subscription.started_at >= month_start,
                    Subscription.started_at < month_end
                )
            ).count()
            
            month_revenue = month_subscriptions * 15  # Average subscription value
            
            revenue_trends.append({
                'month': month_start.strftime('%Y-%m'),
                'revenue': month_revenue
            })
        
        revenue_trends.reverse()
        
        return {
            'total_revenue': total_revenue,
            'mrr': mrr,
            'arpu': arpu,
            'conversion_rate': conversion_rate,
            'churn_rate': churn_rate,
            'subscription_revenue': subscription_revenue,
            'revenue_trends': revenue_trends,
            'active_subscriptions': active_subscriptions,
            'total_subscriptions': total_subscriptions
        }
    
    def get_usage_metrics(self) -> Dict[str, Any]:
        """Get usage metrics for features and content"""
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        
        # CSV analyses
        total_analyses = self.db.query(CSVAnalysis).count()
        analyses_30d = self.db.query(CSVAnalysis).filter(
            CSVAnalysis.created_at >= thirty_days_ago
        ).count()
        
        # Theme requests
        total_theme_requests = self.db.query(ThemeRequest).count()
        theme_requests_30d = self.db.query(ThemeRequest).filter(
            ThemeRequest.requested_at >= thirty_days_ago
        ).count()
        
        # Top themes popularity
        popular_themes = self.db.query(
            TopTheme.theme_name,
            func.count(TopTheme.id).label('count'),
            func.sum(TopTheme.sales_count).label('total_sales')
        ).group_by(TopTheme.theme_name).order_by(
            func.count(TopTheme.id).desc()
        ).limit(10).all()
        
        popular_themes_data = [
            {
                'theme': theme,
                'requests': count,
                'sales': total_sales or 0
            }
            for theme, count, total_sales in popular_themes
        ]
        
        # Video lessons
        total_video_lessons = self.db.query(VideoLesson).count()
        pro_video_lessons = self.db.query(VideoLesson).filter(
            VideoLesson.is_pro_only == True
        ).count()
        
        # Calendar entries
        total_calendar_entries = self.db.query(CalendarEntry).count()
        ai_generated_calendars = self.db.query(CalendarEntry).filter(
            CalendarEntry.source == 'ai'
        ).count()
        
        # Broadcast messages
        total_broadcasts = self.db.query(BroadcastMessage).count()
        broadcasts_30d = self.db.query(BroadcastMessage).filter(
            BroadcastMessage.created_at >= thirty_days_ago
        ).count()
        
        # Feature adoption rates
        users_with_analyses = self.db.query(User).join(CSVAnalysis).distinct().count()
        users_with_themes = self.db.query(User).join(ThemeRequest).distinct().count()
        
        total_users = self.db.query(User).count()
        
        feature_adoption = {
            'csv_analyses': (users_with_analyses / total_users * 100) if total_users > 0 else 0,
            'theme_requests': (users_with_themes / total_users * 100) if total_users > 0 else 0
        }
        
        return {
            'csv_analyses': {
                'total': total_analyses,
                'last_30d': analyses_30d
            },
            'theme_requests': {
                'total': total_theme_requests,
                'last_30d': theme_requests_30d
            },
            'popular_themes': popular_themes_data,
            'video_lessons': {
                'total': total_video_lessons,
                'pro_only': pro_video_lessons
            },
            'calendar_entries': {
                'total': total_calendar_entries,
                'ai_generated': ai_generated_calendars
            },
            'broadcasts': {
                'total': total_broadcasts,
                'last_30d': broadcasts_30d
            },
            'feature_adoption': feature_adoption
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system health and performance metrics"""
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        
        # Recent activity
        recent_analyses = self.db.query(CSVAnalysis).filter(
            CSVAnalysis.created_at >= one_hour_ago
        ).count()
        
        recent_themes = self.db.query(ThemeRequest).filter(
            ThemeRequest.requested_at >= one_hour_ago
        ).count()
        
        # Error rates (if you have error logging)
        # This would be implemented with actual error tracking
        
        # Database performance
        db_size_query = self.db.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
        db_size = db_size_query.scalar() if db_size_query else "Unknown"
        
        return {
            'recent_activity': {
                'analyses_last_hour': recent_analyses,
                'themes_last_hour': recent_themes
            },
            'database_size': db_size,
            'system_status': 'healthy'  # Would be determined by actual health checks
        }
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get all metrics for dashboard display"""
        return {
            'users': self.get_user_metrics(),
            'financial': self.get_financial_metrics(),
            'usage': self.get_usage_metrics(),
            'system': self.get_system_metrics(),
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def close(self):
        """Close database session"""
        if self.db:
            self.db.close()
