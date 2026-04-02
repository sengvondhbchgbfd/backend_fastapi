from sqlalchemy import Integer, String, Boolean, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from decimal import Decimal
from app.db.base import Base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..users.user import User
    from .staff import Staff
    from company import Company


class StaffRole(Base):
    __tablename__ = "staff_roles"

    staff_role_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    role_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    base_salary: Mapped[Decimal | None] = mapped_column(Numeric(10,2), nullable=True)
    is_manager: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)



    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="staff_roles")
    staff_members: Mapped[list["Staff"]] = relationship("Staff", back_populates="staff_role")