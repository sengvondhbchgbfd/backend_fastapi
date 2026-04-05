from sqlalchemy import Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.company import Company


class SystemSetting(Base):
    __tablename__ = "system_settings"

    setting_id:  Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id:  Mapped[int]           = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    key:         Mapped[str]           = mapped_column(String(100), nullable=False)
    value:       Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at:  Mapped[datetime]      = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at:  Mapped[datetime]      = mapped_column(
                                            DateTime,
                                            server_default = func.now(),
                                            onupdate       = func.now(),  # ✅ ORM update()
                                            nullable       = False,
                                        )

    company: Mapped["Company"] = relationship("Company", back_populates="system_settings")