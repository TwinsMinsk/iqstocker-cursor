import os
import sys

# Add project root to PYTHONPATH so that `config` and other packages resolve
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

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
    CSVAnalysis, AnalyticsReport, ThemeRequest,
    GlobalTheme, VideoLesson, CalendarEntry, BroadcastMessage,
    AuditLog, ReferralReward
)
from config.database import engine
from admin_panel.auth import authentication_backend, ADMIN_SECRET_KEY

# Optional imports (wrap in try/except to avoid crashes during startup)
# Flags for optional features
should_enable_whitelist = lambda: False
IPWhitelistMiddleware = None

# Optional integrations
SalesPredictor = None
RecommendationEngine = None
MarketAnalyzer = None
AICacheManager = None
AIRateLimiter = None
AdvancedMetrics = None
BenchmarkEngine = None
AIPerformanceMonitor = None

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
                    from config.database import SessionLocal
                    db = SessionLocal()
                    try:
                        client_ip = request.client.host if request.client else "unknown"
                        user_agent = request.headers.get("user-agent", "unknown")
                        audit_log = AuditLog(
                            admin_username=username,
                            admin_ip=client_ip,
                            action="LOGIN",
                            resource_type="Admin",
                            resource_id=username,
                            description=f"Admin login from {client_ip}",
                            request_method="POST",
                            request_path="/admin/login"
                        )
                        db.add(audit_log)
                        db.commit()
                    finally:
                        db.close()
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
                from config.database import SessionLocal
                db = SessionLocal()
                try:
                    client_ip = request.client.host if request.client else "unknown"
                    audit_log = AuditLog(
                        admin_username=username,
                        admin_ip=client_ip,
                        action="LOGOUT",
                        resource_type="Admin",
                        resource_id=username,
                        description=f"Admin logout from {client_ip}",
                        request_method="POST",
                        request_path="/admin/logout"
                    )
                    db.add(audit_log)
                    db.commit()
                finally:
                    db.close()
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
        User.subscription_expires_at, User.referral_balance, User.referrer_id, User.created_at
    ]
    column_searchable_list = [User.username, User.first_name, User.last_name, User.telegram_id, User.referrer_id]
    column_sortable_list = [User.created_at, User.subscription_expires_at, User.referral_balance, User.id]
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
    
    # Column labels
    column_labels = {
        User.referral_balance: "IQ Баллы",
        User.referrer_id: "ID Пригласившего",
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
        Limits.id, Limits.user_id, 
        Limits.analytics_total, Limits.analytics_used,
        Limits.themes_total, Limits.themes_used,
        Limits.theme_cooldown_days,
        Limits.last_theme_request_at
    ]
    column_sortable_list = [Limits.id, Limits.user_id, Limits.last_theme_request_at]
    column_searchable_list = [Limits.user_id]
    
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True
    export_types = ["csv", "json"]
    
    # Детали для редактирования
    form_columns = [
        Limits.user_id,
        Limits.analytics_total,
        Limits.analytics_used,
        Limits.themes_total,
        Limits.themes_used,
        Limits.theme_cooldown_days,
        Limits.last_theme_request_at
    ]
    
    # Обязательные поля
    form_args = {
        'user_id': {
            'label': 'User ID',
            'description': 'ID пользователя (обязательное поле)',
        },
        'analytics_total': {
            'label': 'Analytics Total',
            'description': 'Общий лимит аналитик',
            'default': 0
        },
        'analytics_used': {
            'label': 'Analytics Used',
            'description': 'Использовано аналитик',
            'default': 0
        },
        'themes_total': {
            'label': 'Themes Total',
            'description': 'Лимит генераций тем в месяц (по умолчанию 4)',
            'default': 4
        },
        'themes_used': {
            'label': 'Themes Used',
            'description': 'Использовано генераций тем',
            'default': 0
        },
        'theme_cooldown_days': {
            'label': 'Theme Cooldown (days)',
            'description': 'Минимальное количество дней между генерациями (по умолчанию 7)',
            'default': 7
        }
    }
    
    # Форматеры для отображения
    column_formatters = {
        Limits.last_theme_request_at: lambda m, a: m.last_theme_request_at.strftime('%Y-%m-%d %H:%M') if m.last_theme_request_at else 'Never',
        Limits.themes_used: lambda m, a: f"{m.themes_used} из {m.themes_total}",
        Limits.analytics_used: lambda m, a: f"{m.analytics_used} из {m.analytics_total}",
        Limits.theme_cooldown_days: lambda m, a: f"{m.theme_cooldown_days} дней ({m.theme_cooldown_days // 7} недель)" if m.theme_cooldown_days else "7 дней"
    }
    
    # Подписи колонок
    column_labels = {
        Limits.id: "ID",
        Limits.user_id: "User ID",
        Limits.analytics_total: "Analytics Limit",
        Limits.analytics_used: "Analytics Used",
        Limits.themes_total: "Themes Limit (per month)",
        Limits.themes_used: "Themes Used",
        Limits.theme_cooldown_days: "Theme Cooldown (days)",
        Limits.last_theme_request_at: "Last Theme Request"
    }
    
    # Описания полей
    column_descriptions = {
        Limits.themes_total: "Количество генераций тем в месяц (рекомендуется 4 = 1 раз в неделю)",
        Limits.theme_cooldown_days: "Минимальное количество дней между генерациями тем (по умолчанию 7 = 1 неделя)",
        Limits.analytics_total: "Лимит аналитик для пользователя"
    }
    
    # Дополнительные колонки для отображения (вычисляемые)
    column_extra_row_actions = None
    
    async def get_list_query(self):
        """Override to eager load user relationship."""
        from sqlalchemy.orm import joinedload
        query = await super().get_list_query()
        return query.options(joinedload(Limits.user))

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

# TopTheme model не существует в текущей схеме БД, поэтому закомментируем
# class TopThemeAdmin(ModelView, model=TopTheme):
#     column_list = [
#         TopTheme.id, TopTheme.csv_analysis_id, TopTheme.theme_name,
#         TopTheme.sales_count, TopTheme.revenue, TopTheme.rank, TopTheme.created_at
#     ]
#     column_searchable_list = [TopTheme.theme_name]
#     column_sortable_list = [TopTheme.created_at, TopTheme.sales_count, TopTheme.revenue, TopTheme.rank]
#     can_create = True
#     can_edit = True
#     can_delete = True
#     can_export = True
#     export_types = ["csv", "json"]
#     
#     # Custom formatters
#     column_formatters = {
#         TopTheme.created_at: lambda m, a: m.created_at.strftime('%Y-%m-%d %H:%M'),
#         TopTheme.revenue: lambda m, a: f"${m.revenue:,.2f}" if m.revenue else "$0.00"
#     }

class ThemeRequestAdmin(ModelView, model=ThemeRequest):
    column_list = [
        ThemeRequest.id, ThemeRequest.user_id, ThemeRequest.theme_name,
        ThemeRequest.status, ThemeRequest.created_at
    ]
    column_sortable_list = [ThemeRequest.created_at, ThemeRequest.id]
    # Временно убираем фильтры для исправления ошибки
    # column_filters = [
    #     ThemeRequest.user_id,
    #     ThemeRequest.status
    # ]
    can_create = True
    can_edit = True
    can_delete = True
    can_export = True
    export_types = ["csv", "json"]
    
    # Custom formatters
    column_formatters = {
        ThemeRequest.created_at: lambda m, a: m.created_at.strftime('%Y-%m-%d %H:%M')
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

# LLMSettingsAdmin removed - LLM functionality is deprecated

class ReferralRewardAdmin(ModelView, model=ReferralReward):
    name = "Награда"
    name_plural = "Награды за рефералов"
    icon = "fa-solid fa-gift"
    
    # Запрещаем создавать или удалять награды, админ может только редактировать 5 существующих
    can_create = False
    can_delete = False
    can_edit = True
    can_export = True
    export_types = ["csv", "json"]
    
    column_list = [
        ReferralReward.reward_id, 
        ReferralReward.name, 
        ReferralReward.cost, 
        ReferralReward.reward_type, 
        ReferralReward.value
    ]
    
    column_labels = {
        ReferralReward.reward_id: "ID",
        ReferralReward.name: "Название",
        ReferralReward.cost: "Стоимость (Баллы)",
        ReferralReward.reward_type: "Тип",
        ReferralReward.value: "Ссылка (для LINK)"
    }
    
    column_sortable_list = [ReferralReward.reward_id, ReferralReward.cost, ReferralReward.reward_type]
    column_searchable_list = [ReferralReward.name]

# Регистрируем все представления
try:
    admin.add_view(UserAdmin)
    admin.add_view(SubscriptionAdmin)
    admin.add_view(LimitsAdmin)
    admin.add_view(CSVAnalysisAdmin)
    admin.add_view(AnalyticsReportAdmin)
    # admin.add_view(TopThemeAdmin)  # Закомментировано, так как TopTheme не существует
    admin.add_view(ThemeRequestAdmin)
    admin.add_view(GlobalThemeAdmin)
    admin.add_view(VideoLessonAdmin)
    admin.add_view(CalendarEntryAdmin)
    admin.add_view(BroadcastMessageAdmin)
    admin.add_view(AuditLogAdmin)
    admin.add_view(ReferralRewardAdmin)
    # admin.add_view(LLMSettingsAdmin)  # Removed - LLM functionality is deprecated
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
        from config.database import SessionLocal
        db = SessionLocal()
        try:
            # Get basic metrics
            total_users = db.query(User).count()
            total_analyses = db.query(CSVAnalysis).count()
            total_themes = db.query(ThemeRequest).count()
            
            metrics = {
                "total_users": total_users,
                "total_analyses": total_analyses,
                "total_themes": total_themes
            }
            
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "metrics": metrics,
                "charts": {}
            })
        finally:
            db.close()
    except Exception as e:
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "metrics": {},
            "charts": {},
            "error": str(e)
        })

# User Limits Management Page
@app.get("/admin/user-limits", response_class=HTMLResponse)
async def user_limits_page(request: Request):
    """User limits management page."""
    try:
        return templates.TemplateResponse("user_limits.html", {
            "request": request
        })
    except Exception as e:
        return HTMLResponse(f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)

# Analytics endpoints
@app.get("/api/analytics/summary")
async def get_analytics_summary():
    """Get analytics summary for dashboard."""
    try:
        from config.database import SessionLocal
        db = SessionLocal()
        try:
            total_users = db.query(User).count()
            total_analyses = db.query(CSVAnalysis).count()
            total_themes = db.query(ThemeRequest).count()
            
            summary = {
                "total_users": total_users,
                "total_analyses": total_analyses,
                "total_themes": total_themes
            }
            return {"success": True, "data": summary}
        finally:
            db.close()
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/analytics/charts")
async def get_analytics_charts():
    """Get charts data."""
    try:
        # Placeholder for charts
        charts = {}
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
        from config.database import SessionLocal
        db = SessionLocal()
        try:
            query = db.query(AuditLog)
            
            if admin_username:
                query = query.filter(AuditLog.admin_username == admin_username)
            if action:
                query = query.filter(AuditLog.action == action)
            if resource_type:
                query = query.filter(AuditLog.resource_type == resource_type)
            
            logs = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset).all()
            
            return {"success": True, "data": [
                {
                    "id": log.id,
                    "admin_username": log.admin_username,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                }
                for log in logs
            ]}
        finally:
            db.close()
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/audit/admin-activity/{admin_username}")
async def get_admin_activity(admin_username: str, days: int = 30):
    """Get admin activity summary."""
    try:
        from config.database import SessionLocal
        from datetime import timedelta
        db = SessionLocal()
        try:
            from_date = datetime.utcnow() - timedelta(days=days)
            logs = db.query(AuditLog).filter(
                AuditLog.admin_username == admin_username,
                AuditLog.created_at >= from_date
            ).all()
            
            summary = {
                "total_actions": len(logs),
                "admin_username": admin_username,
                "period_days": days
            }
            
            return {"success": True, "data": summary}
        finally:
            db.close()
    except Exception as e:
        return {"success": False, "error": str(e)}

# Quick Actions Endpoints (simplified - removed deprecated QuickActions class)
@app.get("/admin/quick-actions/user-statistics")
async def get_user_statistics():
    """Get comprehensive user statistics"""
    try:
        from config.database import SessionLocal
        db = SessionLocal()
        try:
            total_users = db.query(User).count()
            active_subscriptions = db.query(Subscription).filter(
                Subscription.expires_at > datetime.utcnow()
            ).count()
            
            stats = {
                "total_users": total_users,
                "active_subscriptions": active_subscriptions
            }
            
            return {"success": True, "data": stats}
        finally:
            db.close()
    except Exception as e:
        return {"success": False, "error": str(e)}

# Note: AI endpoints removed as LLM functionality is deprecated

# Limits Management Endpoints
@app.get("/api/admin/users/{user_id}/limits")
async def get_user_limits(user_id: int, request: Request):
    """Get current limits for a user."""
    try:
        # Check authentication
        if not await authentication_backend.authenticate(request):
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=401, content={"success": False, "error": "Unauthorized"})
        
        from config.database import SessionLocal
        db = SessionLocal()
        try:
            # Find user by ID
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": f"User with ID {user_id} not found"}
            
            # Get limits
            limits = db.query(Limits).filter(Limits.user_id == user_id).first()
            if not limits:
                return {
                    "success": False, 
                    "error": f"Limits not found for user {user_id}. User might need to be initialized."
                }
            
            return {
                "success": True,
                "data": {
                    "user_id": user_id,
                    "telegram_id": user.telegram_id,
                    "username": user.username,
                    "subscription_type": user.subscription_type.value if user.subscription_type else "FREE",
                    "limits": {
                        "analytics_total": limits.analytics_total,
                        "analytics_used": limits.analytics_used,
                        "analytics_remaining": limits.analytics_remaining,
                        "themes_total": limits.themes_total,
                        "themes_used": limits.themes_used,
                        "themes_remaining": limits.themes_remaining,
                    }
                }
            }
        finally:
            db.close()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@app.put("/api/admin/users/{user_id}/limits")
async def update_user_limits(user_id: int, request: Request):
    """Update limits for a user. Logs changes to AuditLog."""
    try:
        # Check authentication
        if not await authentication_backend.authenticate(request):
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=401, content={"success": False, "error": "Unauthorized"})
        
        # Get admin username from session
        admin_username = request.session.get("username", "unknown")
        client_ip = request.client.host if request.client else "unknown"
        
        # Parse request body
        body = await request.json()
        analytics_total = body.get('analytics_total')
        analytics_used = body.get('analytics_used')
        themes_total = body.get('themes_total')
        themes_used = body.get('themes_used')
        
        from config.database import SessionLocal
        db = SessionLocal()
        try:
            # Find user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": f"User with ID {user_id} not found"}
            
            # Find limits
            limits = db.query(Limits).filter(Limits.user_id == user_id).first()
            if not limits:
                # Create limits if not exists
                limits = Limits(user_id=user_id)
                db.add(limits)
                db.flush()
            
            # Store old values for audit log
            old_values = {
                "analytics_total": limits.analytics_total,
                "analytics_used": limits.analytics_used,
                "themes_total": limits.themes_total,
                "themes_used": limits.themes_used,
            }
            
            # Update limits
            new_values = {}
            if analytics_total is not None:
                limits.analytics_total = analytics_total
                new_values["analytics_total"] = analytics_total
            if analytics_used is not None:
                limits.analytics_used = analytics_used
                new_values["analytics_used"] = analytics_used
            if themes_total is not None:
                limits.themes_total = themes_total
                new_values["themes_total"] = themes_total
            if themes_used is not None:
                limits.themes_used = themes_used
                new_values["themes_used"] = themes_used
            
            # Create audit log entry
            audit_log = AuditLog(
                admin_username=admin_username,
                admin_ip=client_ip,
                action="UPDATE",
                resource_type="Limits",
                resource_id=str(user_id),
                old_values=old_values,
                new_values=new_values,
                description=f"Updated limits for user {user.username} (telegram_id: {user.telegram_id})",
                request_method="PUT",
                request_path=f"/api/admin/users/{user_id}/limits"
            )
            db.add(audit_log)
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Limits updated for user {user_id}",
                "data": {
                    "user_id": user_id,
                    "username": user.username,
                    "telegram_id": user.telegram_id,
                    "old_values": old_values,
                    "new_values": new_values,
                    "current_limits": {
                        "analytics_total": limits.analytics_total,
                        "analytics_used": limits.analytics_used,
                        "analytics_remaining": limits.analytics_remaining,
                        "themes_total": limits.themes_total,
                        "themes_used": limits.themes_used,
                        "themes_remaining": limits.themes_remaining,
                    }
                }
            }
        finally:
            db.close()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

# Note: AI Management endpoints removed as LLM functionality is deprecated


if __name__ == "__main__":
    import uvicorn
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    print("🚀 Starting IQStocker Admin Panel on http://localhost:5000")
    print("📊 Available endpoints:")
    print("  - http://localhost:5000/admin - SQLAdmin interface")
    print("  - http://localhost:5000/admin/user-limits - User limits management")
    print("  - http://localhost:5000/health - Health check")
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")
