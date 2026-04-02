from sqlalchemy import Integer, Numeric, Date, Enum, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime, date
from typing import Optional
import enum
from app.db.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..staffs import Staff
    from ..Salary import SalaryAdjustment
    from ..company import Company

class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    cancelled = "cancelled"

class Salary(Base):
    __tablename__ = "salaries"

    salary_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    managed_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), nullable=False)
    staff_id: Mapped[int] = mapped_column(Integer, ForeignKey("staff.staff_id"), nullable=False)
    base_salary: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    bonus: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    deductions: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    net_salary: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    pay_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    pay_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    payment_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.pending)
    # created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="salaries")
    staff: Mapped["Staff"] = relationship("Staff", back_populates="salaries")
    adjustments: Mapped[list["SalaryAdjustment"]] = relationship("SalaryAdjustment", back_populates="salary")