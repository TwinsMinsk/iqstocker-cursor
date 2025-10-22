"""UserIssuedTheme model to track which themes were issued to a user."""

from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base


class UserIssuedTheme(Base):
    """Map of user to issued themes to avoid duplicates."""
    __tablename__ = "user_issued_themes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    theme_id: Mapped[int] = mapped_column(ForeignKey("global_themes.id"), index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="issued_themes")
    theme: Mapped["GlobalTheme"] = relationship(back_populates="issued_to_users")

    __table_args__ = (
        UniqueConstraint("user_id", "theme_id", name="uq_user_theme"),
    )


