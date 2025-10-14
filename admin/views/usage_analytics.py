"""Usage Analytics view for feature usage and content analytics."""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from config.database import SessionLocal
from database.models import (
    User, Subscription, Limits, CSVAnalysis, AnalyticsReport,
    TopTheme, ThemeRequest, GlobalTheme, VideoLesson, CalendarEntry, BroadcastMessage
)


class UsageAnalytics:
    """Usage analytics engine for feature usage and content analysis."""

    def __init__(self):
        self.db: Session = SessionLocal()

    def get_feature_usage_metrics(self) -> Dict[str, Any]:
        """Get feature usage metrics."""
        
        # CSV Analysis usage
        csv_analyses_count = self.db.query(CSVAnalysis).count()
        csv_analyses_by_status = (
            self.db.query(
                CSVAnalysis.status,
                func.count(CSVAnalysis.id).label('count')
            )
            .group_by(CSVAnalysis.status)
            .all()
        )
        
        # Theme requests usage
        theme_requests_count = self.db.query(ThemeRequest).count()
        theme_requests_by_user = (
            self.db.query(
                ThemeRequest.user_id,
                func.count(ThemeRequest.id).label('count')
            )
            .group_by(ThemeRequest.user_id)
            .order_by(desc('count'))
            .limit(10)
            .all()
        )
        
        # Video lessons usage (assuming views_count field exists)
        video_lessons_count = self.db.query(VideoLesson).count()
        # Since views_count doesn't exist, we'll use a placeholder
        total_video_views = 0  # Placeholder until views_count is added to model
        
        # Calendar usage
        calendar_entries_count = self.db.query(CalendarEntry).count()
        calendar_by_source = (
            self.db.query(
                CalendarEntry.source,
                func.count(CalendarEntry.id).label('count')
            )
            .group_by(CalendarEntry.source)
            .all()
        )
        
        # Broadcast messages usage
        broadcast_messages_count = self.db.query(BroadcastMessage).count()
        total_recipients = (
            self.db.query(func.sum(BroadcastMessage.recipients_count))
            .scalar() or 0
        )
        
        return {
            'csv_analyses': {
                'total': csv_analyses_count,
                'by_status': {status: count for status, count in csv_analyses_by_status}
            },
            'theme_requests': {
                'total': theme_requests_count,
                'top_users': [{'user_id': user_id, 'count': count} for user_id, count in theme_requests_by_user]
            },
            'video_lessons': {
                'total': video_lessons_count,
                'total_views': total_video_views,
                'avg_views_per_lesson': total_video_views / video_lessons_count if video_lessons_count > 0 else 0
            },
            'calendar': {
                'total': calendar_entries_count,
                'by_source': {source: count for source, count in calendar_by_source}
            },
            'broadcasts': {
                'total': broadcast_messages_count,
                'total_recipients': total_recipients,
                'avg_recipients_per_message': total_recipients / broadcast_messages_count if broadcast_messages_count > 0 else 0
            }
        }

    def get_content_analytics(self) -> Dict[str, Any]:
        """Get content analytics metrics."""
        
        # Top themes analysis
        top_themes = (
            self.db.query(
                TopTheme.theme_name,
                func.sum(TopTheme.sales_count).label('total_sales'),
                func.sum(TopTheme.revenue).label('total_revenue'),
                func.count(TopTheme.id).label('appearances')
            )
            .group_by(TopTheme.theme_name)
            .order_by(desc('total_sales'))
            .limit(20)
            .all()
        )
        
        top_themes_list = []
        for theme, sales, revenue, appearances in top_themes:
            top_themes_list.append({
                'theme_name': theme,
                'total_sales': sales,
                'total_revenue': float(revenue) if revenue else 0,
                'appearances': appearances,
                'avg_sales_per_appearance': sales / appearances if appearances > 0 else 0
            })
        
        # Global themes analysis
        global_themes = (
            self.db.query(GlobalTheme)
            .order_by(desc(GlobalTheme.total_sales))
            .limit(10)
            .all()
        )
        
        global_themes_list = []
        for theme in global_themes:
            global_themes_list.append({
                'theme_name': theme.theme_name,
                'total_sales': theme.total_sales,
                'total_revenue': float(theme.total_revenue) if theme.total_revenue else 0,
                'authors_count': theme.authors_count,
                'last_updated': theme.last_updated.isoformat() if theme.last_updated else None
            })
        
        # Analytics reports analysis
        analytics_reports = (
            self.db.query(
                AnalyticsReport.csv_analysis_id,
                AnalyticsReport.total_sales,
                AnalyticsReport.total_revenue,
                AnalyticsReport.portfolio_sold_percent
            )
            .order_by(desc(AnalyticsReport.total_revenue))
            .limit(10)
            .all()
        )
        
        analytics_reports_list = []
        for report in analytics_reports:
            analytics_reports_list.append({
                'csv_analysis_id': report.csv_analysis_id,
                'total_sales': report.total_sales,
                'total_revenue': float(report.total_revenue) if report.total_revenue else 0,
                'portfolio_sold_percent': float(report.portfolio_sold_percent) if report.portfolio_sold_percent else 0
            })
        
        return {
            'top_themes': top_themes_list,
            'global_themes': global_themes_list,
            'analytics_reports': analytics_reports_list
        }

    def get_user_engagement_metrics(self) -> Dict[str, Any]:
        """Get user engagement metrics."""
        
        # Active users (users with recent activity)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        # Since last_activity_at doesn't exist, we'll use created_at as a proxy
        active_users = (
            self.db.query(User)
            .filter(User.created_at >= thirty_days_ago)
            .count()
        )
        
        # Users by subscription type
        users_by_subscription = (
            self.db.query(
                User.subscription_type,
                func.count(User.id).label('count')
            )
            .group_by(User.subscription_type)
            .all()
        )
        
        # Users with CSV analyses
        users_with_csv = (
            self.db.query(func.count(func.distinct(CSVAnalysis.user_id)))
            .scalar() or 0
        )
        
        # Users with theme requests
        users_with_themes = (
            self.db.query(func.count(func.distinct(ThemeRequest.user_id)))
            .scalar() or 0
        )
        
        # Average features used per user
        total_users = self.db.query(User).count()
        csv_analyses_count = self.db.query(CSVAnalysis).count()
        theme_requests_count = self.db.query(ThemeRequest).count()
        avg_csv_per_user = csv_analyses_count / total_users if total_users > 0 else 0
        avg_themes_per_user = theme_requests_count / total_users if total_users > 0 else 0
        
        return {
            'total_users': total_users,
            'active_users_30_days': active_users,
            'users_by_subscription': {sub_type.value: count for sub_type, count in users_by_subscription},
            'users_with_csv': users_with_csv,
            'users_with_themes': users_with_themes,
            'avg_csv_per_user': float(avg_csv_per_user),
            'avg_themes_per_user': float(avg_themes_per_user),
            'engagement_rate': (active_users / total_users) * 100 if total_users > 0 else 0
        }

    def get_usage_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get usage trends over time."""
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # CSV analyses trend
        csv_trend = (
            self.db.query(
                func.strftime('%Y-%m-%d', CSVAnalysis.created_at).label('date'),
                func.count(CSVAnalysis.id).label('count')
            )
            .filter(CSVAnalysis.created_at >= start_date)
            .group_by('date')
            .order_by('date')
            .all()
        )
        
        # Theme requests trend
        themes_trend = (
            self.db.query(
                func.strftime('%Y-%m-%d', ThemeRequest.requested_at).label('date'),
                func.count(ThemeRequest.id).label('count')
            )
            .filter(ThemeRequest.requested_at >= start_date)
            .group_by('date')
            .order_by('date')
            .all()
        )
        
        # User registrations trend
        users_trend = (
            self.db.query(
                func.strftime('%Y-%m-%d', User.created_at).label('date'),
                func.count(User.id).label('count')
            )
            .filter(User.created_at >= start_date)
            .group_by('date')
            .order_by('date')
            .all()
        )
        
        return {
            'csv_analyses_trend': [{'date': date, 'count': count} for date, count in csv_trend],
            'theme_requests_trend': [{'date': date, 'count': count} for date, count in themes_trend],
            'user_registrations_trend': [{'date': date, 'count': count} for date, count in users_trend],
            'period_days': days
        }

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get comprehensive usage summary."""
        return {
            'feature_usage': self.get_feature_usage_metrics(),
            'content_analytics': self.get_content_analytics(),
            'user_engagement': self.get_user_engagement_metrics(),
            'usage_trends': self.get_usage_trends()
        }

    def close(self):
        """Close the database session."""
        self.db.close()
