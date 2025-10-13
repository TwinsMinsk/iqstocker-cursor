# src/admin/app.py
from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse

from config.settings import settings
from database.models import (
    User, SubscriptionType, Subscription, Limits, 
    CSVAnalysis, AnalyticsReport, TopTheme, ThemeRequest, 
    GlobalTheme, VideoLesson, CalendarEntry, BroadcastMessage
)
from config.database import engine

app = FastAPI(title="IQStocker Admin Panel", version="1.0.0")

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]

        # Проверяем логин и пароль из наших настроек
        if username == settings.admin.username and password == settings.admin.password:
            request.session.update({"token": "admin_session"})  # Просто маркер, что мы вошли
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return "token" in request.session

# Создаем экземпляр бэкенда с секретным ключом
authentication_backend = AdminAuth(secret_key=settings.admin.secret_key)

# Подключаем админку к FastAPI-приложению с аутентификацией
admin = Admin(
    app=app,
    engine=engine,
    authentication_backend=authentication_backend,
    title="IQStocker Admin",
    base_url="/admin"
)

# Добавляем представления моделей
class UserAdmin(ModelView, model=User):
    column_list = [
        User.id, User.telegram_id, User.username, 
        User.first_name, User.subscription_type, 
        User.subscription_expires_at, User.created_at
    ]
    column_searchable_list = [User.username, User.first_name]
    column_sortable_list = [User.created_at, User.subscription_expires_at]
    column_details_exclude_list = [User.id]
    can_create = False
    can_edit = True
    can_delete = False

class SubscriptionAdmin(ModelView, model=Subscription):
    column_list = [
        Subscription.id, Subscription.user_id, Subscription.subscription_type,
        Subscription.started_at, Subscription.expires_at, Subscription.payment_id
    ]
    column_sortable_list = [Subscription.started_at, Subscription.expires_at]
    can_create = True
    can_edit = True
    can_delete = True

class LimitsAdmin(ModelView, model=Limits):
    column_list = [
        Limits.id, Limits.user_id, Limits.analytics_total,
        Limits.analytics_used, Limits.themes_total, Limits.themes_used,
        Limits.top_themes_total, Limits.top_themes_used
    ]
    can_create = True
    can_edit = True
    can_delete = True

class CSVAnalysisAdmin(ModelView, model=CSVAnalysis):
    column_list = [
        CSVAnalysis.id, CSVAnalysis.user_id, CSVAnalysis.file_path,
        CSVAnalysis.status, CSVAnalysis.created_at, CSVAnalysis.processed_at
    ]
    column_sortable_list = [CSVAnalysis.created_at, CSVAnalysis.processed_at]
    can_create = False
    can_edit = True
    can_delete = True

class AnalyticsReportAdmin(ModelView, model=AnalyticsReport):
    column_list = [
        AnalyticsReport.id, AnalyticsReport.csv_analysis_id, AnalyticsReport.total_sales,
        AnalyticsReport.total_revenue, AnalyticsReport.portfolio_sold_percent,
        AnalyticsReport.created_at
    ]
    column_sortable_list = [AnalyticsReport.created_at, AnalyticsReport.total_revenue]
    can_create = False
    can_edit = True
    can_delete = True

class TopThemeAdmin(ModelView, model=TopTheme):
    column_list = [
        TopTheme.id, TopTheme.csv_analysis_id, TopTheme.theme_name,
        TopTheme.sales_count, TopTheme.revenue, TopTheme.rank, TopTheme.created_at
    ]
    column_sortable_list = [TopTheme.created_at, TopTheme.sales_count, TopTheme.revenue, TopTheme.rank]
    can_create = True
    can_edit = True
    can_delete = True

class ThemeRequestAdmin(ModelView, model=ThemeRequest):
    column_list = [
        ThemeRequest.id, ThemeRequest.user_id, ThemeRequest.themes,
        ThemeRequest.requested_at
    ]
    column_sortable_list = [ThemeRequest.requested_at]
    can_create = True
    can_edit = True
    can_delete = True

class GlobalThemeAdmin(ModelView, model=GlobalTheme):
    column_list = [
        GlobalTheme.id, GlobalTheme.theme_name, GlobalTheme.total_sales,
        GlobalTheme.total_revenue, GlobalTheme.authors_count, GlobalTheme.last_updated
    ]
    column_sortable_list = [GlobalTheme.last_updated, GlobalTheme.total_sales, GlobalTheme.total_revenue]
    can_create = True
    can_edit = True
    can_delete = True

class VideoLessonAdmin(ModelView, model=VideoLesson):
    column_list = [
        VideoLesson.id, VideoLesson.title, VideoLesson.description,
        VideoLesson.url, VideoLesson.order, VideoLesson.is_pro_only, VideoLesson.created_at
    ]
    column_sortable_list = [VideoLesson.created_at, VideoLesson.order]
    can_create = True
    can_edit = True
    can_delete = True

class CalendarEntryAdmin(ModelView, model=CalendarEntry):
    column_list = [
        CalendarEntry.id, CalendarEntry.month, CalendarEntry.year,
        CalendarEntry.description, CalendarEntry.source, CalendarEntry.created_at
    ]
    column_sortable_list = [CalendarEntry.created_at, CalendarEntry.year, CalendarEntry.month]
    can_create = True
    can_edit = True
    can_delete = True

class BroadcastMessageAdmin(ModelView, model=BroadcastMessage):
    column_list = [
        BroadcastMessage.id, BroadcastMessage.text,
        BroadcastMessage.recipients_count, BroadcastMessage.sent_at, BroadcastMessage.created_at
    ]
    column_sortable_list = [BroadcastMessage.created_at, BroadcastMessage.sent_at]
    can_create = True
    can_edit = True
    can_delete = True

# Регистрируем все представления
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

# Добавляем healthcheck endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "iqstocker-admin",
        "version": "1.0.0"
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
