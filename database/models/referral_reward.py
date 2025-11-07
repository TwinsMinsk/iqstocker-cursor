"""Referral reward model."""

import enum
from sqlalchemy import String, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class RewardType(str, enum.Enum):
    """
    Тип награды:
    LINK - статичная ссылка (для скидок или IQ Radar)
    FREE_PRO - выдать 1 месяц PRO
    FREE_ULTRA - выдать 1 месяц ULTRA
    SUPPORT_REQUEST - запрос через поддержку (пользователь должен написать в поддержку для получения награды)
    """
    LINK = "link"
    FREE_PRO = "free_pro"
    FREE_ULTRA = "free_ultra"
    SUPPORT_REQUEST = "support_request"


class ReferralReward(Base):
    """Referral reward model for storing referral program rewards."""
    
    __tablename__ = 'referral_rewards'
    
    reward_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cost: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_type: Mapped[RewardType] = mapped_column(
        SQLEnum(RewardType, name="reward_type_enum"), 
        nullable=False
    )
    
    # Это поле будет хранить URL (для скидок и IQ Radar)
    # Для FREE_PRO / FREE_ULTRA оно будет null
    value: Mapped[str | None] = mapped_column(String(512), nullable=True)
    
    def __repr__(self) -> str:
        return f"ReferralReward(id={self.reward_id}, name='{self.name}', cost={self.cost})"

