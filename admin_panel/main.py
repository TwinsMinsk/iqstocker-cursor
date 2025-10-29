"""Main FastAPI application for admin panel."""

from pathlib import Path
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.middleware.sessions import SessionMiddleware
import logging

from config.database import get_async_session, engine
from database.models import (
    User, Subscription, GlobalTheme, SystemMessage, 
    AnalyticsReport, VideoLesson, LLMSettings
)
from admin_panel.auth import authentication_backend, ADMIN_SECRET_KEY
from admin_panel.views import dashboard, themes, placeholders

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
    column_list = [User.id, User.username, User.first_name, User.last_name, User.subscription_type, User.is_admin, User.created_at]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

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


@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """Test page."""
    return "<h1>Test Page Works!</h1><p>Админ-панель работает корректно!</p>"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
