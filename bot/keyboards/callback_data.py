"""Callback data classes for bot keyboards."""

from aiogram.filters.callback_data import CallbackData


class ThemesArchiveCallback(CallbackData, prefix="themes_archive"):
    """Callback data for themes archive pagination."""
    page: int
