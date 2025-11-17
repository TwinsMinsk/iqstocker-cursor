"""VIP Group Member model for tracking user joins/leaves in VIP group."""

from datetime import datetime
from sqlalchemy import BigInteger, String, DateTime, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

from config.database import Base
from database.models.user import utc_now


class VIPGroupMemberStatus(str, Enum):
    """VIP Group member status types."""
    JOINED = "JOINED"  # Пользователь вступил в группу
    LEFT = "LEFT"  # Пользователь вышел из группы
    REMOVED = "REMOVED"  # Пользователь был удален из группы


class VIPGroupMember(Base):
    """VIP Group Member model for tracking user participation in VIP group."""
    
    __tablename__ = "vip_group_members"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Тариф на момент вступления/выхода
    subscription_type: Mapped[str] = mapped_column(String(50), nullable=True)
    
    # Статус события (вступление/выход)
    status: Mapped[VIPGroupMemberStatus] = mapped_column(
        SQLEnum(VIPGroupMemberStatus),
        nullable=False
    )
    
    # Дата вступления
    joined_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Дата выхода/удаления
    left_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Дата создания записи
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    
    # Примечание (например, причина удаления)
    note: Mapped[str] = mapped_column(String(500), nullable=True)
    
    # Связь с User (опциональная, т.к. пользователь может быть не зарегистрирован в боте)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='SET NULL'), 
        nullable=True, 
        index=True
    )
    
    def __repr__(self):
        return (
            f"<VIPGroupMember(id={self.id}, telegram_id={self.telegram_id}, "
            f"status={self.status}, joined_at={self.joined_at})>"
        )


# Add composite indexes for optimization
Index('idx_vip_member_telegram_status', VIPGroupMember.telegram_id, VIPGroupMember.status)
Index('idx_vip_member_joined_at', VIPGroupMember.joined_at)
Index('idx_vip_member_created_at', VIPGroupMember.created_at)

