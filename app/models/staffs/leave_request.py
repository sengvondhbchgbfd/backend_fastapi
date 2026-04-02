from sqlalchemy import Integer, String, Date, Text, Enum, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime, date
from typing import Optional, TYPE_CHECKING
import enum
from app.db.base import Base

if TYPE_CHECKING:
    from .staff import Staff
    from ..company import Company


class LeaveType(str, enum.Enum):
    sick   = "sick"
    annual = "annual"
    unpaid = "unpaid"
    other  = "other"


class LeaveStatus(str, enum.Enum):
    pending   = "pending"
    approved  = "approved"
    rejected  = "rejected"
    cancelled = "cancelled"  # ✅ FIX 1: "cancell" typo → "cancelled"


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    leave_id:   Mapped[int]          = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int]          = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    staff_id:   Mapped[int]          = mapped_column(Integer, ForeignKey("staff.staff_id"),       nullable=False)
    leave_type: Mapped[LeaveType]    = mapped_column(Enum(LeaveType),   nullable=False)
    start_date: Mapped[date]         = mapped_column(Date, nullable=False)
    end_date:   Mapped[date]         = mapped_column(Date, nullable=False)
    reason:     Mapped[Optional[str]]= mapped_column(Text, nullable=True)
    status:     Mapped[LeaveStatus]  = mapped_column(Enum(LeaveStatus), default=LeaveStatus.pending)
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("staff.staff_id"), nullable=True)
    # created_at:  Mapped[datetime]      = mapped_column(DateTime, default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    company: Mapped["Company"]         = relationship("Company", back_populates="leave_requests")
    staff:   Mapped["Staff"]           = relationship("Staff",   back_populates="leave_requests", foreign_keys=[staff_id])
    approver: Mapped[Optional["Staff"]]= relationship("Staff",   back_populates="approved_leaves", foreign_keys=[approved_by])