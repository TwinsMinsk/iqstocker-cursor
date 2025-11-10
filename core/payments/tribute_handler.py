"""Tribute Payment Handler."""

from typing import Optional, Dict, Any
from types import TracebackType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config.settings import settings
from config.database import AsyncSessionLocal
from database.models import User, SubscriptionType, SystemSettings


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
        Возвращает данные о подписке с ценами в евро (EUR).
        """
        base_price = 0
        if sub_type == SubscriptionType.PRO:
            base_price = 5  # 5 EUR
        elif sub_type == SubscriptionType.ULTRA:
            base_price = 8  # 8 EUR

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
        discount_percent: int = 0,
        user_subscription_type: Optional[SubscriptionType] = None
    ) -> Optional[str]:
        """
        Возвращает готовую ссылку на оплату из БД с добавлением user_id.
        
        Определяет правильную ссылку на основе текущего тарифа пользователя:
        - FREE -> PRO: payment_link_free_to_pro
        - FREE -> ULTRA: payment_link_free_to_ultra
        - TEST_PRO -> PRO: payment_link_test_to_pro
        - TEST_PRO -> ULTRA: payment_link_test_to_ultra
        - PRO -> ULTRA: payment_link_pro_to_ultra
        
        ПРИМЕЧАНИЕ: Логика скидок (discount_percent) здесь используется
        только для ОТОБРАЖЕНИЯ в боте. Сама ссылка статична.
        Для применения скидки, в Tribute должны быть созданы
        отдельные продукты/промокоды.
        """
        # Определяем ключ ссылки на основе текущего тарифа пользователя
        link_key = None
        
        if user_subscription_type == SubscriptionType.FREE:
            if subscription_type == SubscriptionType.PRO:
                link_key = 'payment_link_free_to_pro'
            elif subscription_type == SubscriptionType.ULTRA:
                link_key = 'payment_link_free_to_ultra'
        elif user_subscription_type == SubscriptionType.TEST_PRO:
            if subscription_type == SubscriptionType.PRO:
                link_key = 'payment_link_test_to_pro'
            elif subscription_type == SubscriptionType.ULTRA:
                link_key = 'payment_link_test_to_ultra'
        elif user_subscription_type == SubscriptionType.PRO:
            if subscription_type == SubscriptionType.ULTRA:
                link_key = 'payment_link_pro_to_ultra'
        
        # Если не удалось определить ссылку, используем старые ссылки из settings
        if not link_key:
            if subscription_type == SubscriptionType.PRO:
                base_link = self.pro_link
            elif subscription_type == SubscriptionType.ULTRA:
                base_link = self.ultra_link
            else:
                return None
            
            # Добавляем user_id к ссылке
            if base_link:
                separator = '&' if '?' in base_link else '?'
                return f"{base_link}{separator}user_id={user_id}"
            return None
        
        # Получаем ссылку из БД
        async with AsyncSessionLocal() as session:
            try:
                link_query = await session.execute(
                    select(SystemSettings).where(SystemSettings.key == link_key)
                )
                link_setting = link_query.scalar_one_or_none()
                
                if link_setting and link_setting.value:
                    base_link = link_setting.value.strip()
                    # Добавляем user_id к ссылке
                    separator = '&' if '?' in base_link else '?'
                    return f"{base_link}{separator}user_id={user_id}"
            except Exception as e:
                print(f"Error loading payment link from DB: {e}")
        
        # Fallback к старым ссылкам из settings
        if subscription_type == SubscriptionType.PRO:
            base_link = self.pro_link
        elif subscription_type == SubscriptionType.ULTRA:
            base_link = self.ultra_link
        else:
            return None
        
        if base_link:
            separator = '&' if '?' in base_link else '?'
            return f"{base_link}{separator}user_id={user_id}"
        return None


def get_payment_handler() -> TributePaymentHandler:
    """Возвращает экземпляр обработчика Tribute."""
    return TributePaymentHandler()

