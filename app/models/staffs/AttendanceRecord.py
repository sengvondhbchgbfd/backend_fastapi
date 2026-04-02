from sqlalchemy import Integer, Date, Time, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime, date, time
from typing import Optional, TYPE_CHECKING
from app.db.base import Base

if TYPE_CHECKING:
    from .staff import Staff
    from ..company import Company


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    attendance_id:  Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id:     Mapped[int]           = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    staff_id:       Mapped[int]           = mapped_column(Integer, ForeignKey("staff.staff_id"),       nullable=False)
    # ✅ FIX 1: Mapped[date] not Mapped[datetime] — column is Date not DateTime
    date:           Mapped[date]          = mapped_column(Date,    nullable=False)
    check_in_time:  Mapped[Optional[time]]= mapped_column(Time,    nullable=True)
    check_out_time: Mapped[Optional[time]]= mapped_column(Time,    nullable=True)
    # ✅ FIX 2: added DateTime type
    created_at:     Mapped[datetime]      = mapped_column(DateTime, server_default=func.now(), nullable=False)
    latitude:       Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    longitude:      Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="attendance_records")
    staff:   Mapped["Staff"]   = relationship("Staff",   back_populates="attendance_records")