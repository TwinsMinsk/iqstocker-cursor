"""Secure authentication backend for SQLAdmin."""

import os
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config.database import AsyncSessionLocal
from database.models.user import User

# Используем простой секретный ключ из .env или временный
ADMIN_SECRET_KEY = os.environ.get("ADMIN_SECRET_KEY", "your-very-secret-key-for-admin")


class AdminAuth(AuthenticationBackend):
    """Secure authentication backend using telegram_id and is_admin flag."""
    
    async def login(self, request: Request) -> bool:
        """Handle login form submission."""
        form = await request.form()
        # Используем telegram_id как "username" для простоты
        telegram_id = form.get("username")

        if not telegram_id:
            return False

        try:
            user_id = int(telegram_id)
        except ValueError:
            return False

        # Получаем сессию
        async with AsyncSessionLocal() as session:
            user = await self.get_admin_user(session, user_id)

            if user and user.is_admin:
                # Устанавливаем cookie сессии
                request.session.update({
                    "admin_user_id": user.id,
                    "admin_telegram_id": user.telegram_id,
                    "admin_username": user.username or f"User_{user.telegram_id}"
                })
                return True

        return False

    async def logout(self, request: Request) -> bool:
        """Handle logout."""
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """Check if user is authenticated."""
        if "admin_user_id" in request.session:
            return True
        return False

    async def get_admin_user(self, session: AsyncSession, user_id: int) -> User | None:
        """
        Вспомогательная функция для получения пользователя-администратора.
        """
        stmt = select(User).where(User.telegram_id == user_id, User.is_admin == True)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


# Создаем экземпляр бэкенда
authentication_backend = AdminAuth(secret_key=ADMIN_SECRET_KEY)