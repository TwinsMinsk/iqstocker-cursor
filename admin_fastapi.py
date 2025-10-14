# src/admin/app.py
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request as StarletteRequest
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from config.settings import settings
from database.models import (
    User, SubscriptionType, Subscription, Limits,
    CSVAnalysis, AnalyticsReport, TopTheme, ThemeRequest,
    GlobalTheme, VideoLesson, CalendarEntry, BroadcastMessage,
    AuditLog
)
from config.database import engine
from admin.utils.analytics_engine import AnalyticsEngine
from admin.utils.chart_generator import ChartGenerator
from admin.utils.quick_actions import QuickActions
from admin.utils.audit_logger import AuditLogger
from admin.views.financial_analytics import FinancialAnalytics
from admin.views.usage_analytics import UsageAnalytics
from admin.middlewares.ip_whitelist import IPWhitelistMiddleware, should_enable_whitelist

# Import new AI components
from core.ai.sales_predictor import SalesPredictor
from core.ai.recommendation_engine import RecommendationEngine
from core.ai.market_analyzer import MarketAnalyzer
from core.ai.cache_manager import AICacheManager
from core.ai.rate_limiter import AIRateLimiter
from core.monitoring.ai_monitor import AIPerformanceMonitor
from core.analytics.advanced_metrics import AdvancedMetrics
from core.analytics.benchmark_engine import BenchmarkEngine

app = FastAPI(title="IQStocker Admin Panel", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="admin/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="admin/templates")

# Добавляем middleware для сессий
app.add_middleware(SessionMiddleware, secret_key=settings.admin.secret_key)

# Add IP whitelist middleware for production
if should_enable_whitelist():
    app.add_middleware(IPWhitelistMiddleware)

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        try:
            form = await request.form()
            username = form.get("username", "")
            password = form.get("password", "")

            # Проверяем логин и пароль из наших настроек
            if username == settings.admin.username and password == settings.admin.password:
                request.session.update({"token": "admin_session", "username": username})
                
                # Log successful login
                try:
                    audit_logger = AuditLogger()
                    client_ip = request.client.host if request.client else "unknown"
                    user_agent = request.headers.get("user-agent", "unknown")
                    audit_logger.log_login(username, client_ip, user_agent)
                    audit_logger.close()
                except Exception as e:
                    print(f"Failed to log login: {e}")
                
                return True
            return False
        except Exception as e:
            print(f"Login error: {e}")
            return False

    async def logout(self, request: Request) -> bool:
        try:
            username = request.session.get("username", "unknown")
            request.session.clear()
            
            # Log logout
            try:
                audit_logger = AuditLogger()
                client_ip = request.client.host if request.client else "unknown"
                audit_logger.log_logout(username, client_ip)
                audit_logger.close()
            except Exception as e:
                print(f"Failed to log logout: {e}")
            
            return True
        except Exception as e:
            print(f"Logout error: {e}")
            return False

    async def authenticate(self, request: Request) -> bool:
        try:
            return "token" in request.session and request.session.get("token") == "admin_session"
        except Exception as e:
            print(f"Authentication error: {e}")
            return False

# Создаем экземпляр бэкенда с секретным ключом
authentication_backend = AdminAuth(secret_key=settings.admin.secret_key)

# Configure admin with custom logo and title
admin = Admin(
    app=app,
    engine=engine,
    authentication_backend=authentication_backend,
    title="IQStocker Admin",
    logo_url="/static/img/logo.png",
    base_url="/admin",
    templates_dir="admin/templates"
)

# Добавляем представления моделей
class UserAdmin(ModelView, model=User):
    column_list = [
        User.id, User.telegram_id, User.username, 
        User.first_name, User.subscription_type, 
        User.subscription_expires_at, User.created_at
    ]
    column_searchable_list = [User.username, User.first_name, User.last_name, User.telegram_id]
    column_sortable_list = [User.created_at, User.subscription_expires_at, User.id]
    # Временно убираем фильтры для исправления ошибки
    # column_filters = [
    #     User.subscription_type,
    #     User.created_at,
    #     User.subscription_expires_at
    # ]
    column_details_exclude_list = [User.id]
    can_create = False
    can_edit = True
    can_delete = False
    can_export = True
    export_types = ["csv", "json"]
    
    # Custom formatters
    column_formatters = {
        User.subscription_expires_at: lambda m, a: m.subscription_expires_at.strftime('%Y-%m-%d %H:%M') if m.subscription_expires_at else 'Never',
        User.created_at: lambda m, a: m.created_at.strftime('%Y-%m-%d %H:%M')
    }

class SubscriptionAdmin(ModelView, model=Subscription):
    column_list = [
        Subscription.id, Subscription.user_id, Subscription.subscription_type,
        Subscription.started_at, Subscription.expires_at, Subscription.payment_id
    ]
    column_searchable_list = [Subscription.payment_id]
    column_sortable_list = [Subscription.started_at, Subscription.expires_at, Subscription.id]
    # Временно убираем фильтры для исправления ошибки
    # column_filters = [
    #     Subscription.subscription_type,
    #     Subscription.started_at,
    #     Subscription.expires_at
    # ]
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True
    export_types = ["csv", "json"]
    
    # Custom formatters
    column_formatters = {
        Subscription.started_at: lambda m, a: m.started_at.strftime('%Y-%m-%d %H:%M'),
        Subscription.expires_at: lambda m, a: m.expires_at.strftime('%Y-%m-%d %H:%M') if m.expires_at else 'Never'
    }

class LimitsAdmin(ModelView, model=Limits):
    column_list = [
        Limits.id, Limits.user_id, Limits.analytics_total,
        Limits.analytics_used, Limits.themes_total, Limits.themes_used,
        Limits.top_themes_total, Limits.top_themes_used
    ]
    column_sortable_list = [Limits.id, Limits.user_id]
    # Временно убираем фильтры для исправления ошибки
    # column_filters = [Limits.user_id]
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True
    export_types = ["csv", "json"]

class CSVAnalysisAdmin(ModelView, model=CSVAnalysis):
    column_list = [
        CSVAnalysis.id, CSVAnalysis.user_id, CSVAnalysis.file_path, 
        CSVAnalysis.status, CSVAnalysis.created_at, CSVAnalysis.processed_at
    ]
    column_searchable_list = [CSVAnalysis.file_path]
    column_sortable_list = [CSVAnalysis.created_at, CSVAnalysis.processed_at, CSVAnalysis.id]
    # Временно убираем фильтры для исправления ошибки
    # column_filters = [
    #     CSVAnalysis.status,
    #     CSVAnalysis.created_at,
    #     CSVAnalysis.processed_at
    # ]
    can_create = False
    can_edit = True
    can_delete = True
    can_export = True
    export_types = ["csv", "json"]
    
    # Custom formatters
    column_formatters = {
        CSVAnalysis.created_at: lambda m, a: m.created_at.strftime('%Y-%m-%d %H:%M'),
        CSVAnalysis.processed_at: lambda m, a: m.processed_at.strftime('%Y-%m-%d %H:%M') if m.processed_at else 'Not processed'
    }

class AnalyticsReportAdmin(ModelView, model=AnalyticsReport):
    column_list = [
        AnalyticsReport.id, AnalyticsReport.csv_analysis_id, AnalyticsReport.total_sales,
        AnalyticsReport.total_revenue, AnalyticsReport.portfolio_sold_percent,
        AnalyticsReport.created_at
    ]
    column_sortable_list = [AnalyticsReport.created_at, AnalyticsReport.total_revenue, AnalyticsReport.id]
    # Временно убираем фильтры для исправления ошибки
    # column_filters = [
    #     AnalyticsReport.csv_analysis_id,
    #     AnalyticsReport.created_at
    # ]
    can_create = False
    can_edit = True
    can_delete = True
    can_export = True
    export_types = ["csv", "json"]
    
    # Custom formatters
    column_formatters = {
        AnalyticsReport.created_at: lambda m, a: m.created_at.strftime('%Y-%m-%d %H:%M'),
        AnalyticsReport.total_revenue: lambda m, a: f"${m.total_revenue:,.2f}" if m.total_revenue else "$0.00"
    }

class TopThemeAdmin(ModelView, model=TopTheme):
    column_list = [
        TopTheme.id, TopTheme.csv_analysis_id, TopTheme.theme_name,
        TopTheme.sales_count, TopTheme.revenue, TopTheme.rank, TopTheme.created_at
    ]
    column_searchable_list = [TopTheme.theme_name]
    column_sortable_list = [TopTheme.created_at, TopTheme.sales_count, TopTheme.revenue, TopTheme.rank]
    # Временно убираем фильтры для исправления ошибки
    # column_filters = [
    #     TopTheme.csv_analysis_id,
    #     TopTheme.rank,
    #     TopTheme.created_at
    # ]
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True
    export_types = ["csv", "json"]
    
    # Custom formatters
    column_formatters = {
        TopTheme.created_at: lambda m, a: m.created_at.strftime('%Y-%m-%d %H:%M'),
        TopTheme.revenue: lambda m, a: f"${m.revenue:,.2f}" if m.revenue else "$0.00"
    }

class ThemeRequestAdmin(ModelView, model=ThemeRequest):
    column_list = [
        ThemeRequest.id, ThemeRequest.user_id, ThemeRequest.themes,
        ThemeRequest.requested_at
    ]
    column_sortable_list = [ThemeRequest.requested_at, ThemeRequest.id]
    # Временно убираем фильтры для исправления ошибки
    # column_filters = [
    #     ThemeRequest.user_id,
    #     ThemeRequest.requested_at
    # ]
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True
    export_types = ["csv", "json"]
    
    # Custom formatters
    column_formatters = {
        ThemeRequest.requested_at: lambda m, a: m.requested_at.strftime('%Y-%m-%d %H:%M')
    }

class GlobalThemeAdmin(ModelView, model=GlobalTheme):
    column_list = [
        GlobalTheme.id, GlobalTheme.theme_name, GlobalTheme.total_sales,
        GlobalTheme.total_revenue, GlobalTheme.authors_count, GlobalTheme.last_updated
    ]
    column_searchable_list = [GlobalTheme.theme_name]
    column_sortable_list = [GlobalTheme.last_updated, GlobalTheme.total_sales, GlobalTheme.total_revenue]
    # Временно убираем фильтры для исправления ошибки
    # column_filters = [
    #     GlobalTheme.theme_name,
    #     GlobalTheme.last_updated
    # ]
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True
    export_types = ["csv", "json"]
    
    # Custom formatters
    column_formatters = {
        GlobalTheme.last_updated: lambda m, a: m.last_updated.strftime('%Y-%m-%d %H:%M') if m.last_updated else 'Never',
        GlobalTheme.total_revenue: lambda m, a: f"${m.total_revenue:,.2f}" if m.total_revenue else "$0.00"
    }

class VideoLessonAdmin(ModelView, model=VideoLesson):
    column_list = [
        VideoLesson.id, VideoLesson.title, VideoLesson.description,
        VideoLesson.url, VideoLesson.order, VideoLesson.is_pro_only, VideoLesson.created_at
    ]
    column_searchable_list = [VideoLesson.title, VideoLesson.description]
    column_sortable_list = [VideoLesson.created_at, VideoLesson.order, VideoLesson.id]
    # Временно убираем фильтры для исправления ошибки
    # column_filters = [
    #     VideoLesson.is_pro_only,
    #     VideoLesson.created_at
    # ]
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True
    export_types = ["csv", "json"]
    
    # Custom formatters
    column_formatters = {
        VideoLesson.created_at: lambda m, a: m.created_at.strftime('%Y-%m-%d %H:%M'),
        VideoLesson.is_pro_only: lambda m, a: "Pro Only" if m.is_pro_only else "Free"
    }

class CalendarEntryAdmin(ModelView, model=CalendarEntry):
    column_list = [
        CalendarEntry.id, CalendarEntry.month, CalendarEntry.year,
        CalendarEntry.description, CalendarEntry.source, CalendarEntry.created_at
    ]
    column_searchable_list = [CalendarEntry.description]
    column_sortable_list = [CalendarEntry.created_at, CalendarEntry.year, CalendarEntry.month]
    # Временно убираем фильтры для исправления ошибки
    # column_filters = [
    #     CalendarEntry.month,
    #     CalendarEntry.year,
    #     CalendarEntry.source,
    #     CalendarEntry.created_at
    # ]
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True
    export_types = ["csv", "json"]
    
    # Custom formatters
    column_formatters = {
        CalendarEntry.created_at: lambda m, a: m.created_at.strftime('%Y-%m-%d %H:%M'),
        CalendarEntry.source: lambda m, a: m.source.title() if m.source else 'Manual'
    }

class BroadcastMessageAdmin(ModelView, model=BroadcastMessage):
    column_list = [
        BroadcastMessage.id, BroadcastMessage.text,
        BroadcastMessage.recipients_count, BroadcastMessage.sent_at, BroadcastMessage.created_at
    ]
    column_searchable_list = [BroadcastMessage.text]
    column_sortable_list = [BroadcastMessage.created_at, BroadcastMessage.sent_at, BroadcastMessage.id]
    # Временно убираем фильтры для исправления ошибки
    # column_filters = [
    #     BroadcastMessage.sent_at,
    #     BroadcastMessage.created_at
    # ]
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True
    export_types = ["csv", "json"]
    
    # Custom formatters
    column_formatters = {
        BroadcastMessage.created_at: lambda m, a: m.created_at.strftime('%Y-%m-%d %H:%M'),
        BroadcastMessage.sent_at: lambda m, a: m.sent_at.strftime('%Y-%m-%d %H:%M') if m.sent_at else 'Not sent'
    }

class AuditLogAdmin(ModelView, model=AuditLog):
    column_list = [
        AuditLog.id, AuditLog.admin_username, AuditLog.action,
        AuditLog.resource_type, AuditLog.resource_id, AuditLog.created_at
    ]
    column_searchable_list = [AuditLog.admin_username, AuditLog.action, AuditLog.resource_type]
    column_sortable_list = [AuditLog.created_at, AuditLog.id]
    # Временно убираем фильтры для исправления ошибки
    # column_filters = [
    #     AuditLog.admin_username,
    #     AuditLog.action,
    #     AuditLog.resource_type,
    #     AuditLog.created_at
    # ]
    can_create = False
    can_edit = False
    can_delete = True
    can_export = True
    export_types = ["csv", "json"]
    
    # Custom formatters
    column_formatters = {
        AuditLog.created_at: lambda m, a: m.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }

# Регистрируем все представления
try:
    admin.add_view(UserAdmin)
    admin.add_view(SubscriptionAdmin)
    admin.add_view(LimitsAdmin)
    admin.add_view(CSVAnalysisAdmin)
    admin.add_view(AnalyticsReportAdmin)
    admin.add_view(TopThemeAdmin)
    admin.add_view(ThemeRequestAdmin)
    admin.add_view(GlobalThemeAdmin)
    admin.add_view(VideoLessonAdmin)
    admin.add_view(CalendarEntryAdmin)
    admin.add_view(BroadcastMessageAdmin)
    admin.add_view(AuditLogAdmin)
    print("✅ All admin views registered successfully")
except Exception as e:
    print(f"❌ Error registering admin views: {e}")

# Добавляем healthcheck endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Проверяем подключение к БД
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "service": "iqstocker-admin",
            "version": "1.0.0",
            "database": "connected",
            "admin_panel": "available"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "iqstocker-admin",
            "version": "1.0.0",
            "error": str(e)
        }

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "IQStocker Admin Panel",
        "status": "running",
        "version": "1.0.0",
        "admin_url": "/admin"
    }

# Dashboard endpoint
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_view(request: Request):
    """Dashboard with metrics and charts."""
    try:
        # Get analytics data
        analytics = AnalyticsEngine()
        metrics = analytics.get_dashboard_summary()
        analytics.close()
        
        # Generate charts
        chart_generator = ChartGenerator()
        charts = chart_generator.generate_dashboard_charts(metrics)
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "metrics": metrics,
            "charts": charts
        })
    except Exception as e:
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "metrics": {},
            "charts": {},
            "error": str(e)
        })

# Analytics endpoints
@app.get("/api/analytics/summary")
async def get_analytics_summary():
    """Get analytics summary for dashboard."""
    try:
        analytics = AnalyticsEngine()
        summary = analytics.get_dashboard_summary()
        analytics.close()
        return {"success": True, "data": summary}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/analytics/charts")
async def get_analytics_charts():
    """Get charts data."""
    try:
        analytics = AnalyticsEngine()
        metrics = analytics.get_dashboard_summary()
        analytics.close()
        
        chart_generator = ChartGenerator()
        charts = chart_generator.generate_dashboard_charts(metrics)
        
        return {"success": True, "charts": charts}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/audit/logs")
async def get_audit_logs(
    admin_username: str = None,
    action: str = None,
    resource_type: str = None,
    limit: int = 100,
    offset: int = 0
):
    """Get audit logs with filters."""
    try:
        audit_logger = AuditLogger()
        logs = audit_logger.get_audit_logs(
            admin_username=admin_username,
            action=action,
            resource_type=resource_type,
            limit=limit,
            offset=offset
        )
        audit_logger.close()
        
        return {"success": True, "data": [log.to_dict() for log in logs]}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/audit/admin-activity/{admin_username}")
async def get_admin_activity(admin_username: str, days: int = 30):
    """Get admin activity summary."""
    try:
        audit_logger = AuditLogger()
        summary = audit_logger.get_admin_activity_summary(admin_username, days)
        audit_logger.close()
        
        return {"success": True, "data": summary}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Quick Actions Endpoints
@app.post("/admin/quick-actions/bulk-subscription")
async def bulk_subscription_update(request: Request):
    """Update subscription for multiple users"""
    try:
        data = await request.json()
        user_ids = data.get('user_ids', [])
        subscription_type = data.get('subscription_type', 'FREE')
        duration_days = data.get('duration_days', 30)
        
        if not user_ids:
            return {"success": False, "error": "No user IDs provided"}
        
        quick_actions = QuickActions()
        result = quick_actions.bulk_update_subscription(user_ids, subscription_type, duration_days)
        quick_actions.close()
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/admin/quick-actions/bulk-reset-limits")
async def bulk_reset_limits(request: Request):
    """Reset limits for multiple users"""
    try:
        data = await request.json()
        user_ids = data.get('user_ids', [])
        
        if not user_ids:
            return {"success": False, "error": "No user IDs provided"}
        
        quick_actions = QuickActions()
        result = quick_actions.bulk_reset_limits(user_ids)
        quick_actions.close()
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/admin/quick-actions/export-users")
async def export_users(
    subscription_type: str = None,
    created_after: str = None,
    created_before: str = None,
    is_active: bool = None
):
    """Export users to CSV"""
    try:
        filters = {}
        if subscription_type:
            filters['subscription_type'] = subscription_type
        if created_after:
            filters['created_after'] = datetime.fromisoformat(created_after)
        if created_before:
            filters['created_before'] = datetime.fromisoformat(created_before)
        if is_active is not None:
            filters['is_active'] = is_active
        
        quick_actions = QuickActions()
        csv_content = quick_actions.export_users_csv(filters)
        quick_actions.close()
        
        from fastapi.responses import Response
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/admin/quick-actions/export-analytics")
async def export_analytics(
    user_id: int = None,
    status: str = None,
    created_after: str = None,
    created_before: str = None
):
    """Export analytics data to CSV"""
    try:
        filters = {}
        if user_id:
            filters['user_id'] = user_id
        if status:
            filters['status'] = status
        if created_after:
            filters['created_after'] = datetime.fromisoformat(created_after)
        if created_before:
            filters['created_before'] = datetime.fromisoformat(created_before)
        
        quick_actions = QuickActions()
        csv_content = quick_actions.export_analytics_csv(filters)
        quick_actions.close()
        
        from fastapi.responses import Response
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/admin/quick-actions/export-themes")
async def export_themes(
    csv_analysis_id: int = None,
    min_sales: int = None,
    min_revenue: float = None
):
    """Export theme data to CSV"""
    try:
        filters = {}
        if csv_analysis_id:
            filters['csv_analysis_id'] = csv_analysis_id
        if min_sales:
            filters['min_sales'] = min_sales
        if min_revenue:
            filters['min_revenue'] = min_revenue
        
        quick_actions = QuickActions()
        csv_content = quick_actions.export_themes_csv(filters)
        quick_actions.close()
        
        from fastapi.responses import Response
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=themes_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/admin/quick-actions/bulk-notification")
async def send_bulk_notification(request: Request):
    """Send notification to multiple users"""
    try:
        data = await request.json()
        user_ids = data.get('user_ids', [])
        message = data.get('message', '')
        notification_type = data.get('notification_type', 'info')
        
        if not user_ids:
            return {"success": False, "error": "No user IDs provided"}
        if not message:
            return {"success": False, "error": "No message provided"}
        
        quick_actions = QuickActions()
        result = quick_actions.send_bulk_notification(user_ids, message, notification_type)
        quick_actions.close()
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/admin/quick-actions/bulk-delete-analyses")
async def bulk_delete_analyses(request: Request):
    """Delete multiple CSV analyses"""
    try:
        data = await request.json()
        analysis_ids = data.get('analysis_ids', [])
        
        if not analysis_ids:
            return {"success": False, "error": "No analysis IDs provided"}
        
        quick_actions = QuickActions()
        result = quick_actions.bulk_delete_analyses(analysis_ids)
        quick_actions.close()
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/admin/quick-actions/user-statistics")
async def get_user_statistics():
    """Get comprehensive user statistics"""
    try:
        quick_actions = QuickActions()
        stats = quick_actions.get_user_statistics()
        quick_actions.close()
        
        return {"success": True, "data": stats}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# Financial Analytics Endpoints
@app.get("/api/financial/summary")
async def get_financial_summary():
    """Get financial analytics summary."""
    try:
        financial_analytics = FinancialAnalytics()
        summary = financial_analytics.get_financial_summary()
        financial_analytics.close()
        return {"success": True, "data": summary}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/financial/revenue")
async def get_revenue_metrics():
    """Get revenue metrics."""
    try:
        financial_analytics = FinancialAnalytics()
        metrics = financial_analytics.get_revenue_metrics()
        financial_analytics.close()
        return {"success": True, "data": metrics}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/financial/conversion")
async def get_conversion_metrics():
    """Get conversion metrics."""
    try:
        financial_analytics = FinancialAnalytics()
        metrics = financial_analytics.get_conversion_metrics()
        financial_analytics.close()
        return {"success": True, "data": metrics}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Usage Analytics Endpoints
@app.get("/api/usage/summary")
async def get_usage_summary():
    """Get usage analytics summary."""
    try:
        usage_analytics = UsageAnalytics()
        summary = usage_analytics.get_usage_summary()
        usage_analytics.close()
        return {"success": True, "data": summary}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/usage/features")
async def get_feature_usage():
    """Get feature usage metrics."""
    try:
        usage_analytics = UsageAnalytics()
        metrics = usage_analytics.get_feature_usage_metrics()
        usage_analytics.close()
        return {"success": True, "data": metrics}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/usage/content")
async def get_content_analytics():
    """Get content analytics."""
    try:
        usage_analytics = UsageAnalytics()
        metrics = usage_analytics.get_content_analytics()
        usage_analytics.close()
        return {"success": True, "data": metrics}
    except Exception as e:
        return {"success": False, "error": str(e)}

# AI Performance and Analytics Endpoints
@app.get("/api/ai/performance")
async def get_ai_performance():
    """Get AI performance metrics."""
    try:
        monitor = AIPerformanceMonitor()
        performance = monitor.get_performance_summary("openai", 24)
        return {"success": True, "data": performance}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/ai/cache/status")
async def get_ai_cache_status():
    """Get AI cache status."""
    try:
        cache_manager = AICacheManager()
        stats = cache_manager.get_cache_statistics()
        return {"success": True, "data": stats}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/ai/rate-limits")
async def get_ai_rate_limits():
    """Get AI rate limit status."""
    try:
        rate_limiter = AIRateLimiter()
        status = rate_limiter.get_rate_limit_status("openai")
        return {"success": True, "data": status}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/ai/predictions/{user_id}")
async def get_user_predictions(user_id: int):
    """Get AI predictions for a specific user."""
    try:
        sales_predictor = SalesPredictor()
        predictions = sales_predictor.get_comprehensive_prediction(user_id)
        return {"success": True, "data": predictions}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/ai/recommendations/{user_id}")
async def get_user_recommendations(user_id: int):
    """Get AI recommendations for a specific user."""
    try:
        recommendation_engine = RecommendationEngine()
        recommendations = recommendation_engine.get_comprehensive_recommendations(user_id)
        return {"success": True, "data": recommendations}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/ai/market-trends")
async def get_market_trends():
    """Get current market trends."""
    try:
        market_analyzer = MarketAnalyzer()
        trends = market_analyzer.get_trending_themes('week', 20)
        return {"success": True, "data": trends}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/ai/market-overview")
async def get_market_overview():
    """Get comprehensive market overview."""
    try:
        market_analyzer = MarketAnalyzer()
        overview = market_analyzer.get_market_overview()
        return {"success": True, "data": overview}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Advanced Analytics Endpoints
@app.get("/api/advanced/metrics/{user_id}")
async def get_advanced_metrics(user_id: int):
    """Get advanced metrics for a user."""
    try:
        advanced_metrics = AdvancedMetrics()
        metrics = advanced_metrics.get_comprehensive_metrics(user_id)
        return {"success": True, "data": metrics}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/benchmark/user/{user_id}")
async def get_user_benchmark(user_id: int):
    """Get benchmark comparison for a user."""
    try:
        benchmark_engine = BenchmarkEngine()
        benchmark = benchmark_engine.compare_user_to_benchmarks(user_id)
        return {"success": True, "data": benchmark}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/benchmark/industry")
async def get_industry_benchmarks():
    """Get industry benchmark data."""
    try:
        benchmark_engine = BenchmarkEngine()
        benchmarks = benchmark_engine.get_industry_benchmarks()
        return {"success": True, "data": benchmarks}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/benchmark/subscription/{subscription_type}")
async def get_subscription_benchmarks(subscription_type: str):
    """Get benchmarks for a specific subscription type."""
    try:
        from database.models import SubscriptionType
        sub_type = SubscriptionType(subscription_type)
        benchmark_engine = BenchmarkEngine()
        benchmarks = benchmark_engine.get_subscription_benchmarks(sub_type)
        return {"success": True, "data": benchmarks}
    except Exception as e:
        return {"success": False, "error": str(e)}

# AI Management Endpoints
@app.post("/api/ai/cache/clear")
async def clear_ai_cache():
    """Clear AI cache."""
    try:
        cache_manager = AICacheManager()
        result = cache_manager.invalidate_cache("weekly_themes")
        return {"success": True, "cleared_items": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/ai/rate-limits/clear")
async def clear_rate_limits():
    """Clear rate limits (for testing)."""
    try:
        rate_limiter = AIRateLimiter()
        result = await rate_limiter.clear_rate_limits("openai")
        return {"success": True, "cleared_limits": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/ai/queue/status")
async def get_queue_status():
    """Get AI request queue status."""
    try:
        rate_limiter = AIRateLimiter()
        status = rate_limiter.get_queue_status()
        return {"success": True, "data": status}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/ai/costs/summary")
async def get_ai_costs_summary():
    """Get AI costs summary."""
    try:
        rate_limiter = AIRateLimiter()
        costs = rate_limiter.get_cost_summary("openai", days=7)
        return {"success": True, "data": costs}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
