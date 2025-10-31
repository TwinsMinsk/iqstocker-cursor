"""Secure authentication backend for SQLAdmin."""

from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from config.settings import settings

# Используем секретный ключ из настроек
ADMIN_SECRET_KEY = settings.admin.secret_key


class AdminAuth(AuthenticationBackend):
    """Secure authentication backend using ADMIN_USERNAME and ADMIN_PASSWORD from settings."""
    
    async def login(self, request: Request) -> bool:
        """Handle login form submission."""
        form = await request.form()
        username = form.get("username", "")
        password = form.get("password", "")

        if not username or not password:
            return False

        # Проверяем логин и пароль из настроек
        if username == settings.admin.username and password == settings.admin.password:
            # Устанавливаем cookie сессии
            request.session.update({
                "admin_authenticated": True,
                "admin_username": username
            })
            return True

        return False

    async def logout(self, request: Request) -> bool:
        """Handle logout."""
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """Check if user is authenticated."""
        if request.session.get("admin_authenticated"):
            return True
        return False


# Создаем экземпляр бэкенда
authentication_backend = AdminAuth(secret_key=ADMIN_SECRET_KEY)