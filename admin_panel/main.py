"""Main FastAPI application for admin panel."""

from pathlib import Path
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
import logging

from config.database import get_async_session, engine
from database.models import (
    User, Subscription, GlobalTheme, SystemMessage, 
    AnalyticsReport, VideoLesson, LLMSettings
)
from admin_panel.auth import authentication_backend, ADMIN_SECRET_KEY
from admin_panel.views import dashboard, themes, placeholders, lexicon, users, analytics

# Определяем корень директории admin_panel
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Проверка для отладки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"Admin Panel BASE_DIR: {BASE_DIR}")
logger.info(f"Admin Panel STATIC_DIR: {STATIC_DIR}")
logger.info(f"Admin Panel TEMPLATES_DIR: {TEMPLATES_DIR}")

# Create FastAPI app
app = FastAPI(title="IQStocker Admin Panel", version="2.0")

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=ADMIN_SECRET_KEY)


# Middleware для редиректа /admin/ на /dashboard
class AdminRedirectMiddleware(BaseHTTPMiddleware):
    """Middleware to redirect /admin/ to /dashboard."""
    
    async def dispatch(self, request: StarletteRequest, call_next):
        # Редиректим /admin/ на /dashboard
        if request.url.path == "/admin" or request.url.path == "/admin/":
            return RedirectResponse(url="/dashboard")
        
        return await call_next(request)


# Middleware для инжекции CSS в SQLAdmin страницы
class SQLAdminCSSMiddleware(BaseHTTPMiddleware):
    """Middleware to inject custom CSS into SQLAdmin pages."""
    
    async def dispatch(self, request: StarletteRequest, call_next):
        response = await call_next(request)
        
        # Только для HTML ответов от SQLAdmin (пути /admin/* но не /admin/ напрямую)
        if (request.url.path.startswith("/admin/") and 
            request.url.path != "/admin/" and
            response.headers.get("content-type", "").startswith("text/html")):
            
            try:
                # Читаем body если это streaming response
                if hasattr(response, 'body_iterator'):
                    body = b""
                    async for chunk in response.body_iterator:
                        body += chunk
                elif hasattr(response, 'body'):
                    body = response.body
                else:
                    return response
                
                body_str = body.decode('utf-8', errors='ignore')
                
                # Инжектируем CSS перед закрывающим </head>
                if '</head>' in body_str.lower() and '/static/css/admin.css' not in body_str:
                    css_injection = '''
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="/static/css/admin.css" rel="stylesheet">
    <style>
        /* Дополнительные стили для SQLAdmin */
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important; 
            background-color: #f5f7fa !important;
        }
        .admin-sidebar, .sidebar, nav.sidebar { 
            background: linear-gradient(180deg, #252836 0%, #1a1b23 100%) !important; 
            box-shadow: 2px 0 10px rgba(0,0,0,0.1) !important;
        }
        .nav-link.active, .sidebar-nav .nav-link.active { 
            background: rgba(102, 126, 234, 0.2) !important; 
            border-left: 3px solid #667eea !important; 
            color: white !important;
        }
        .nav-link, .sidebar-nav .nav-link { 
            color: rgba(255, 255, 255, 0.7) !important;
            transition: all 0.3s ease !important;
        }
        .nav-link:hover, .sidebar-nav .nav-link:hover { 
            background: rgba(255, 255, 255, 0.1) !important; 
            color: white !important;
        }
        .card, .admin-card { 
            border-radius: 12px !important; 
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important; 
            border: none !important;
        }
        .btn-primary { 
            background: linear-gradient(135deg, #667eea, #764ba2) !important; 
            border: none !important; 
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
        }
        .btn-primary:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
        }
        .table { 
            border-radius: 8px !important; 
            overflow: hidden !important; 
            box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
        }
        .table thead { 
            background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%) !important; 
        }
        .table tbody tr:hover {
            background-color: #f9fafb !important;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #1f2937 !important;
        }
        .badge {
            border-radius: 6px !important;
            padding: 0.375rem 0.75rem !important;
            font-weight: 500 !important;
        }
    </style>
'''
                    body_str = body_str.replace('</head>', css_injection + '</head>')
                    body = body_str.encode('utf-8')
                    
                    # Создаем новый response с обновленным body
                    return Response(
                        content=body,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type=response.media_type
                    )
                
                # Возвращаем оригинальный response если не было изменений
                if hasattr(response, 'body_iterator'):
                    return Response(
                        content=body,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type=response.media_type
                    )
            except Exception as e:
                logger.error(f"Error in SQLAdminCSSMiddleware: {e}")
        
        return response


# Применяем middleware (порядок важен! Middleware выполняются в обратном порядке)
# Последний добавленный middleware выполняется первым
# 1. Инжекция CSS для SQLAdmin страниц (выполняется последним из middleware)
app.add_middleware(SQLAdminCSSMiddleware)
# 2. Редирект для /admin/ на /dashboard (выполняется перед CSS инжекцией)
app.add_middleware(AdminRedirectMiddleware)

# Mount static files с проверкой
if not STATIC_DIR.is_dir():
    logger.error(f"Static directory NOT FOUND at {STATIC_DIR}")
    raise RuntimeError(f"Static directory not found at {STATIC_DIR}")
else:
    logger.info("Static directory found.")
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup templates с проверкой
if not TEMPLATES_DIR.is_dir():
    logger.error(f"Templates directory NOT FOUND at {TEMPLATES_DIR}")
    raise RuntimeError(f"Templates directory not found at {TEMPLATES_DIR}")
else:
    logger.info("Templates directory found.")
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Create authentication backend
# authentication_backend is imported from admin_panel.auth

# Create SQLAdmin instance
admin = Admin(
    app=app,
    engine=engine,
    authentication_backend=authentication_backend,
    title="IQStocker Admin",
    base_url="/admin",
    templates_dir=str(TEMPLATES_DIR)
)

# Add model views
class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.first_name, User.last_name, User.telegram_id, User.subscription_type, User.is_admin, User.created_at, User.last_activity_at]
    column_searchable_list = [User.username, User.first_name, User.last_name, User.telegram_id]
    column_sortable_list = [User.id, User.created_at, User.last_activity_at, User.subscription_type]
    column_filters = [User.subscription_type, User.is_admin]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    can_export = True
    export_types = ["csv", "json"]

class SubscriptionAdmin(ModelView, model=Subscription):
    column_list = [Subscription.id, Subscription.user_id, Subscription.subscription_type, Subscription.started_at, Subscription.expires_at]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

class GlobalThemeAdmin(ModelView, model=GlobalTheme):
    column_list = [GlobalTheme.id, GlobalTheme.theme_name, GlobalTheme.total_sales, GlobalTheme.total_revenue, GlobalTheme.authors_count]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

class SystemMessageAdmin(ModelView, model=SystemMessage):
    column_list = [SystemMessage.key, SystemMessage.text]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

class AnalyticsReportAdmin(ModelView, model=AnalyticsReport):
    column_list = [AnalyticsReport.id, AnalyticsReport.csv_analysis_id, AnalyticsReport.total_sales, AnalyticsReport.total_revenue]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

class VideoLessonAdmin(ModelView, model=VideoLesson):
    column_list = [VideoLesson.id, VideoLesson.title, VideoLesson.order, VideoLesson.is_pro_only]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

class LLMSettingsAdmin(ModelView, model=LLMSettings):
    column_list = [LLMSettings.id, LLMSettings.provider_name, LLMSettings.is_active, LLMSettings.theme_request_interval_days]
    column_details_exclude_list = [LLMSettings.api_key_encrypted]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

# Register admin views
admin.add_view(UserAdmin)
admin.add_view(SubscriptionAdmin)
admin.add_view(GlobalThemeAdmin)
admin.add_view(SystemMessageAdmin)
admin.add_view(AnalyticsReportAdmin)
admin.add_view(VideoLessonAdmin)
admin.add_view(LLMSettingsAdmin)

# Include routers
app.include_router(dashboard.router, prefix="", tags=["dashboard"])
app.include_router(themes.router, prefix="", tags=["themes"])
app.include_router(placeholders.router, prefix="", tags=["placeholders"])
app.include_router(lexicon.router, prefix="", tags=["lexicon"])
app.include_router(users.router, prefix="", tags=["users"])
app.include_router(analytics.router, prefix="", tags=["analytics"])


@app.get("/")
async def root():
    """Root page - redirect to dashboard."""
    return RedirectResponse(url="/dashboard")


@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """Test page."""
    return "<h1>Test Page Works!</h1><p>Админ-панель работает корректно!</p>"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
