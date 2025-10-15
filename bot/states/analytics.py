"""FSM states for analytics."""

from aiogram.fsm.state import State, StatesGroup


class AnalyticsStates(StatesGroup):
    """Analytics FSM states."""
    
    waiting_for_portfolio_size = State()
    waiting_for_upload_limit = State()
    waiting_for_monthly_uploads = State()
    # waiting_for_acceptance_rate = State()  # Удалено - не используется
    waiting_for_profit_margin = State()
    waiting_for_content_type = State()
