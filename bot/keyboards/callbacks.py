"""Callback data factories for structured navigation."""

from typing import Optional
from aiogram.filters.callback_data import CallbackData


class ThemesCallback(CallbackData, prefix="themes"):
    """Callback data for themes actions."""
    action: str
    page: Optional[int] = None


class NavigationCallback(CallbackData, prefix="nav"):
    """Callback data for navigation between sections."""
    section: str


class ActionCallback(CallbackData, prefix="action"):
    """Callback data for actions within sections."""
    action: str
    param: str = None


class AnalyticsCallback(CallbackData, prefix="analytics"):
    """Callback data for analytics actions."""
    action: str
    step: str = None


class ThemeCallback(CallbackData, prefix="theme"):
    """Callback data for theme actions."""
    action: str
    theme_id: str = None


class ReportPaginationCallback(CallbackData, prefix="report"):
    """Callback data for report pagination."""
    action: str  # "view", "prev", "next", "list"
    page: int = 1
    report_id: int = 0  # Default to 0 instead of None


class LessonCallback(CallbackData, prefix="lesson"):
    """Callback data for video lessons."""
    action: str  # "list", "view", "category"
    lesson_id: int = None
    category: str = None
    page: int = 1


class ProfileCallback(CallbackData, prefix="profile"):
    """Callback data for profile actions."""
    action: str
    subscription_type: str = None


class ProfileCallbackData(CallbackData, prefix="prof"):
    """Callback data for profile section actions."""
    action: str
    from_analytics: bool = False  # Флаг, указывающий, что переход произошел из аналитики


class CommonCallbackData(CallbackData, prefix="common"):
    """Callback data for common actions like main_menu."""
    action: str


class PaymentCallbackData(CallbackData, prefix="payment"):
    """Callback data for payment actions."""
    plan: str  # "pro", "ultra", "pro_test_discount", "ultra_test_discount"
    from_analytics: bool = False  # Флаг, указывающий, что переход произошел из аналитики
    previous_step: Optional[str] = None  # Предыдущий шаг в цепочке навигации


class UpgradeCallbackData(CallbackData, prefix="upgrade"):
    """Callback data for upgrade and compare actions."""
    action: str  # "upgrade_pro", "upgrade_ultra", "compare_subscriptions", "compare_free_pro", "compare_pro_ultra"
    previous_step: Optional[str] = None  # Предыдущий шаг в цепочке навигации