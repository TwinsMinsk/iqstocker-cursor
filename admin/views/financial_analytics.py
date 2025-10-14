"""Financial Analytics view for revenue, conversion, and LTV analysis."""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from config.database import SessionLocal
from database.models import (
    User, Subscription, Limits, CSVAnalysis, AnalyticsReport,
    TopTheme, ThemeRequest, GlobalTheme, VideoLesson, CalendarEntry, BroadcastMessage
)


class FinancialAnalytics:
    """Financial analytics engine for revenue and conversion analysis."""

    def __init__(self):
        self.db: Session = SessionLocal()

    def get_revenue_metrics(self) -> Dict[str, Any]:
        """Get comprehensive revenue metrics."""
        
        # Total revenue from all subscriptions
        total_revenue = self.db.query(func.sum(Subscription.amount)).scalar() or 0
        
        # Revenue by subscription type
        revenue_by_type = (
            self.db.query(
                Subscription.subscription_type,
                func.sum(Subscription.amount).label('total_amount'),
                func.count(Subscription.id).label('count')
            )
            .group_by(Subscription.subscription_type)
            .all()
        )
        
        revenue_by_type_dict = {}
        for sub_type, amount, count in revenue_by_type:
            revenue_by_type_dict[sub_type.value] = {
                'amount': float(amount) if amount else 0,
                'count': count,
                'average': float(amount) / count if count > 0 else 0
            }
        
        # Monthly recurring revenue (MRR)
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        mrr_subscriptions = (
            self.db.query(Subscription)
            .filter(
                Subscription.expires_at >= current_month,
                Subscription.subscription_type != 'FREE'
            )
            .all()
        )
        
        mrr = sum(sub.amount for sub in mrr_subscriptions if sub.amount)
        
        # Average revenue per user (ARPU)
        total_users = self.db.query(User).count()
        arpu = total_revenue / total_users if total_users > 0 else 0
        
        # Customer lifetime value (LTV) estimation
        # Simplified calculation: average subscription value * average retention period
        avg_subscription_value = (
            self.db.query(func.avg(Subscription.amount))
            .filter(Subscription.subscription_type != 'FREE')
            .scalar() or 0
        )
        
        # Estimate retention period (simplified)
        retention_period_months = 6  # Assume 6 months average retention
        ltv = float(avg_subscription_value) * retention_period_months
        
        return {
            'total_revenue': float(total_revenue),
            'revenue_by_type': revenue_by_type_dict,
            'mrr': float(mrr),
            'arpu': float(arpu),
            'ltv': float(ltv),
            'avg_subscription_value': float(avg_subscription_value)
        }

    def get_conversion_metrics(self) -> Dict[str, Any]:
        """Get conversion funnel metrics."""
        
        # Total users by subscription type
        users_by_type = (
            self.db.query(
                User.subscription_type,
                func.count(User.id).label('count')
            )
            .group_by(User.subscription_type)
            .all()
        )
        
        total_users = sum(count for _, count in users_by_type)
        users_by_type_dict = {sub_type.value: count for sub_type, count in users_by_type}
        
        # Conversion rates
        conversion_rates = {}
        if total_users > 0:
            for sub_type, count in users_by_type:
                conversion_rates[f"{sub_type.value}_conversion_rate"] = (count / total_users) * 100
        
        # Free to paid conversion
        free_users = users_by_type_dict.get('FREE', 0)
        paid_users = total_users - free_users
        free_to_paid_conversion = (paid_users / total_users) * 100 if total_users > 0 else 0
        
        # Trial to paid conversion (TEST_PRO to PRO/ULTRA)
        test_pro_users = users_by_type_dict.get('TEST_PRO', 0)
        pro_users = users_by_type_dict.get('PRO', 0) + users_by_type_dict.get('ULTRA', 0)
        trial_to_paid_conversion = (pro_users / test_pro_users) * 100 if test_pro_users > 0 else 0
        
        return {
            'total_users': total_users,
            'users_by_type': users_by_type_dict,
            'conversion_rates': conversion_rates,
            'free_to_paid_conversion': float(free_to_paid_conversion),
            'trial_to_paid_conversion': float(trial_to_paid_conversion)
        }

    def get_revenue_trends(self, months: int = 12) -> Dict[str, Any]:
        """Get revenue trends over time."""
        
        # Revenue by month
        revenue_by_month = (
            self.db.query(
                func.strftime('%Y-%m', Subscription.started_at).label('month'),
                func.sum(Subscription.amount).label('revenue'),
                func.count(Subscription.id).label('subscriptions')
            )
            .filter(Subscription.started_at >= datetime.utcnow() - timedelta(days=months * 30))
            .group_by('month')
            .order_by('month')
            .all()
        )
        
        revenue_trends = []
        for month, revenue, subs in revenue_by_month:
            revenue_trends.append({
                'month': month,
                'revenue': float(revenue) if revenue else 0,
                'subscriptions': subs
            })
        
        # Calculate growth rate
        if len(revenue_trends) >= 2:
            current_month_revenue = revenue_trends[-1]['revenue']
            previous_month_revenue = revenue_trends[-2]['revenue']
            growth_rate = ((current_month_revenue - previous_month_revenue) / previous_month_revenue) * 100 if previous_month_revenue > 0 else 0
        else:
            growth_rate = 0
        
        return {
            'revenue_trends': revenue_trends,
            'monthly_growth_rate': float(growth_rate),
            'period_months': months
        }

    def get_churn_analysis(self) -> Dict[str, Any]:
        """Get churn analysis metrics."""
        
        # Expired subscriptions
        expired_subscriptions = (
            self.db.query(Subscription)
            .filter(Subscription.expires_at < datetime.utcnow())
            .count()
        )
        
        # Active subscriptions
        active_subscriptions = (
            self.db.query(Subscription)
            .filter(Subscription.expires_at >= datetime.utcnow())
            .count()
        )
        
        # Total subscriptions
        total_subscriptions = self.db.query(Subscription).count()
        
        # Churn rate calculation
        churn_rate = (expired_subscriptions / total_subscriptions) * 100 if total_subscriptions > 0 else 0
        
        # Subscriptions expiring soon (next 30 days)
        expiring_soon = (
            self.db.query(Subscription)
            .filter(
                Subscription.expires_at >= datetime.utcnow(),
                Subscription.expires_at <= datetime.utcnow() + timedelta(days=30)
            )
            .count()
        )
        
        return {
            'expired_subscriptions': expired_subscriptions,
            'active_subscriptions': active_subscriptions,
            'total_subscriptions': total_subscriptions,
            'churn_rate': float(churn_rate),
            'expiring_soon': expiring_soon
        }

    def get_financial_summary(self) -> Dict[str, Any]:
        """Get comprehensive financial summary."""
        return {
            'revenue': self.get_revenue_metrics(),
            'conversion': self.get_conversion_metrics(),
            'trends': self.get_revenue_trends(),
            'churn': self.get_churn_analysis()
        }

    def close(self):
        """Close the database session."""
        self.db.close()
