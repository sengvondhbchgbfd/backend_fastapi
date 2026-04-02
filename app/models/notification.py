from sqlalchemy import Integer, String, Text, Boolean, Enum, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import enum
from app.db.base import Base
if TYPE_CHECKING:
    from .users import User
    from .company import Company




class NotificationType(str, enum.Enum):
    info = "info"
    warning = "warning"
    error = "error"
    success = "success"

class Notification(Base):
    __tablename__ = "notifications"

    notification_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), default=NotificationType.info)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reference_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)



    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="notifications")
    
    user: Mapped["User"] = relationship("User", back_populates="notifications")