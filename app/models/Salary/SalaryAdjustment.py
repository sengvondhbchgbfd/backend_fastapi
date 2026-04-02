# models/salary_adjustment.py
from sqlalchemy import Integer, Numeric, String, Text, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.db.base import Base
from typing import TYPE_CHECKING




if TYPE_CHECKING:
    from .salary import Salary
    from ..company import Company
    
class AdjustmentType(str, enum.Enum):
    bonus = "bonus"
    deduction = "deduction"

class SalaryAdjustment(Base):
    __tablename__ = "salary_adjustments"

    adjustment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    salary_id: Mapped[int] = mapped_column(Integer, ForeignKey("salaries.salary_id"), nullable=False)
    
    adjusted_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), nullable=False)

    adjustment_type: Mapped[AdjustmentType] = mapped_column(Enum(AdjustmentType), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    # 

    # Relationships
    salary: Mapped["Salary"] = relationship("Salary", back_populates="adjustments")
    company: Mapped["Company"] = relationship("Company", back_populates="salary_adjustments")
