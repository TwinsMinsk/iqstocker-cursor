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


class ProfileCallback(CallbackData, prefix="profile"):
    """Callback data for profile actions."""
    action: str
    subscription_type: str = None
