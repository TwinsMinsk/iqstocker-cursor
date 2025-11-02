"""Tribute Payment Handler."""

from typing import Optional, Dict, Any
from types import TracebackType
from config.settings import settings
from database.models import User, SubscriptionType


class TributePaymentHandler:
    """
    Обработчик для создания платежных ссылок Tribute.
    Ссылки на оплату (товары, подписки) создаются в UI Tribute
    и хранятся в конфиге.
    """
    
    def __init__(self):
        self.pro_link = settings.payment.tribute_pro_link
        self.ultra_link = settings.payment.tribute_ultra_link
        self.api_key = settings.payment.tribute_api_key

    async def __aenter__(self):
        return self

    async def __aexit__(
        self,
        exc_type: Optional[BaseException],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ):
        pass

    def _get_subscription_data(self, sub_type: SubscriptionType, discount_percent: int = 0) -> Dict[str, Any]:
        """
        (Логика скопирована из boosty_handler.py для отображения цен в боте)
        """
        base_price = 0
        if sub_type == SubscriptionType.PRO:
            base_price = 990
        elif sub_type == SubscriptionType.ULTRA:
            base_price = 1990

        discount_amount = (base_price * discount_percent) / 100
        final_price = base_price - discount_amount

        return {
            "original_price": f"{base_price:.0f}",
            "price": f"{final_price:.0f}",
            "discount_amount": f"{discount_amount:.0f}"
        }

    def calculate_discount(self, user: User, target_plan: SubscriptionType) -> int:
        """
        (Логика скопирована из boosty_handler.py для отображения скидки в боте)
        """
        if user.subscription_type == SubscriptionType.TEST_PRO:
            return settings.pro_discount_percent  # 50%
        elif user.subscription_type == SubscriptionType.FREE:
            return settings.free_discount_percent  # 30%
        return 0

    async def create_subscription_link(
        self, 
        user_id: int, 
        subscription_type: SubscriptionType, 
        discount_percent: int = 0
    ) -> Optional[str]:
        """
        Возвращает готовую ссылку на оплату из конфига.
        
        ПРИМЕЧАНИЕ: Логика скидок (discount_percent) здесь используется
        только для ОТОБРАЖЕНИЯ в боте. Сама ссылка статична.
        Для применения скидки, в Tribute должны быть созданы
        отдельные продукты/промокоды.
        """
        
        if subscription_type == SubscriptionType.PRO:
            return self.pro_link
        elif subscription_type == SubscriptionType.ULTRA:
            return self.ultra_link
        
        return None


def get_payment_handler() -> TributePaymentHandler:
    """Возвращает экземпляр обработчика Tribute."""
    return TributePaymentHandler()

