"""Callback data factories for structured navigation."""

from aiogram.filters.callback_data import CallbackData


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


class FAQCallback(CallbackData, prefix="faq"):
    """Callback data for FAQ navigation."""
    level: int  # 1=categories, 2=questions, 3=answer
    category: str = None
    question: str = None


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
