"""Main FastAPI application for admin panel."""

from pathlib import Path
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
# SQLAdmin imports removed - not using SQLAdmin anymore
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
import logging

from config.database import get_async_session, AsyncSessionLocal
# SQLAdmin model imports removed - not needed anymore
from admin_panel.auth import authentication_backend, ADMIN_SECRET_KEY
from admin_panel.views import dashboard, themes, placeholders, lexicon, users, analytics, broadcast, payments, payment_test, tariff_limits, referral, vip_group
from api.webhook_server import webhook_router

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
        # Редиректим корневой /admin/ на /dashboard
        if request.url.path == "/admin" or request.url.path == "/admin/":
            return RedirectResponse(url="/dashboard")
        
        return await call_next(request)


# SQLAdminCSSMiddleware removed - SQLAdmin not used anymore


# Применяем middleware
app.add_middleware(AdminRedirectMiddleware)

# Mount static files с проверкой
if not STATIC_DIR.is_dir():
    logger.error(f"Static directory NOT FOUND at {STATIC_DIR}")
    raise RuntimeError(f"Static directory not found at {STATIC_DIR}")
else:
    logger.info("Static directory found.")
    # Mount static files with no-cache headers
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.types import ASGIApp
    
    class NoCacheStaticMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            if request.url.path.startswith("/static/"):
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
            return response
    
    app.add_middleware(NoCacheStaticMiddleware)
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

# SQLAdmin removed - using custom admin views instead
logger.info("Using custom admin views instead of SQLAdmin")

# Include routers
# Important: Register specific routers BEFORE placeholders to avoid conflicts
app.include_router(dashboard.router, prefix="", tags=["dashboard"])
app.include_router(lexicon.router, prefix="", tags=["lexicon"])
app.include_router(users.router, prefix="", tags=["users"])
app.include_router(analytics.router, prefix="", tags=["analytics"])
app.include_router(broadcast.router, prefix="", tags=["broadcast"])
app.include_router(payments.router, prefix="", tags=["payments"])
app.include_router(payment_test.router, prefix="", tags=["payment_test"])
app.include_router(tariff_limits.router, prefix="", tags=["tariff_limits"])
app.include_router(referral.router, prefix="", tags=["referral"])
app.include_router(themes.router, prefix="", tags=["themes"])
app.include_router(vip_group.router, prefix="", tags=["vip_group"])
# Webhook router for payment processing
app.include_router(webhook_router, prefix="", tags=["webhooks"])
# Placeholders router should be last to catch any unmatched routes
app.include_router(placeholders.router, prefix="", tags=["placeholders"])


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway."""
    try:
        # Test database connection
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "service": "iqstocker-admin",
            "version": "2.0",
            "database": "connected",
            "admin_panel": "available"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "iqstocker-admin",
            "version": "2.0",
            "error": str(e)
        }


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
