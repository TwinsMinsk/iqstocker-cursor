"""Pagination utilities for inline keyboards."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards.callbacks import ReportPaginationCallback


def create_pagination_keyboard(
    current_page: int,
    total_pages: int,
    callback_prefix: str = "report",
    show_view_button: bool = True,
    report_id: int = None
) -> InlineKeyboardMarkup:
    """Create pagination keyboard with navigation buttons."""
    keyboard = []
    
    # Navigation row
    nav_row = []
    if current_page > 1:
        nav_row.append(InlineKeyboardButton(
            text="◀️ Предыдущий",
            callback_data=ReportPaginationCallback(
                action="prev",
                page=current_page - 1,
                report_id=report_id
            ).pack()
        ))
    
    nav_row.append(InlineKeyboardButton(
        text=f"{current_page}/{total_pages}",
        callback_data="page_info"
    ))
    
    if current_page < total_pages:
        nav_row.append(InlineKeyboardButton(
            text="Следующий ▶️",
            callback_data=ReportPaginationCallback(
                action="next",
                page=current_page + 1,
                report_id=report_id
            ).pack()
        ))
    
    if nav_row:  # Only add navigation row if there are buttons
        keyboard.append(nav_row)
    
    # View button (if needed)
    if show_view_button and report_id:
        keyboard.append([
            InlineKeyboardButton(
                text="📊 Просмотреть отчет",
                callback_data=ReportPaginationCallback(
                    action="view",
                    page=current_page,
                    report_id=report_id
                ).pack()
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_simple_pagination_keyboard(
    current_page: int,
    total_pages: int,
    callback_prefix: str = "page"
) -> InlineKeyboardMarkup:
    """Create simple pagination keyboard without view button."""
    return create_pagination_keyboard(
        current_page=current_page,
        total_pages=total_pages,
        callback_prefix=callback_prefix,
        show_view_button=False,
        report_id=0
    )


def create_report_list_keyboard(
    reports: list,
    current_page: int = 1,
    reports_per_page: int = 5
) -> InlineKeyboardMarkup:
    """Create keyboard for listing reports with pagination."""
    keyboard = []
    
    # Calculate pagination
    start_idx = (current_page - 1) * reports_per_page
    end_idx = start_idx + reports_per_page
    page_reports = reports[start_idx:end_idx]
    
    total_pages = (len(reports) + reports_per_page - 1) // reports_per_page
    
    # Add report buttons
    for i, report in enumerate(page_reports, start_idx + 1):
        keyboard.append([
            InlineKeyboardButton(
                text=f"📊 Отчет {i}",
                callback_data=ReportPaginationCallback(
                    action="view",
                    page=current_page,
                    report_id=report.get('id', i)
                ).pack()
            )
        ])
    
    # Add pagination if needed
    if total_pages > 1:
        pagination_keyboard = create_simple_pagination_keyboard(
            current_page=current_page,
            total_pages=total_pages
        )
        
        # Merge keyboards
        keyboard.extend(pagination_keyboard.inline_keyboard)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
