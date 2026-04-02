from sqlalchemy import Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from app.db.base import Base
import enum
from datetime import date
from sqlalchemy import Date, Text
from typing import List

if TYPE_CHECKING:
    from ..users.user import User
    from .staff_role import StaffRole
    from ..Salary.salary import Salary
    from .leave_request import LeaveRequest
    from ..staffs.AttendanceRecord import AttendanceRecord
    from ..invoices.invoice import Invoice
    from ..company import Company
    from ..chat.chat_message import ChatMessage
    from ..chat.chat_group_member import ChatGroupMember

class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"

class Staff(Base):
    __tablename__ = "staff"

    staff_id:      Mapped[int]          = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id:    Mapped[int]          = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    user_id:       Mapped[int]          = mapped_column(Integer, ForeignKey("users.user_id"),        nullable=False, unique=True)
    staff_role_id: Mapped[Optional[int]]= mapped_column(Integer, ForeignKey("staff_roles.staff_role_id"), nullable=True)
    name:          Mapped[str]          = mapped_column(String(150), nullable=False)
    gender:        Mapped[Optional[GenderEnum]] = mapped_column(Enum(GenderEnum), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True) 
    address:       Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email:         Mapped[Optional[str]]= mapped_column(String(255), nullable=True)
    phone:         Mapped[Optional[str]]= mapped_column(String(20),  nullable=True)
    
    #  add avatar fields
    avatar_url:    Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    avatar_public_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at:    Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    company:    Mapped["Company"]            = relationship("Company",   back_populates="staff")
    user:       Mapped["User"]               = relationship("User",      back_populates="staff")

    staff_role: Mapped[Optional["StaffRole"]]= relationship("StaffRole", back_populates="staff_members")

    salaries:           Mapped[list["Salary"]]          = relationship("Salary",           back_populates="staff",    foreign_keys="Salary.staff_id")
    leave_requests:     Mapped[list["LeaveRequest"]]    = relationship("LeaveRequest",     back_populates="staff",    foreign_keys="LeaveRequest.staff_id")
    # ✅ FIX 2: added approved_leaves — staff can approve other staff leaves
    approved_leaves:    Mapped[list["LeaveRequest"]]    = relationship("LeaveRequest",     back_populates="approver", foreign_keys="LeaveRequest.approved_by")
    attendance_records: Mapped[list["AttendanceRecord"]]= relationship("AttendanceRecord", back_populates="staff")
    invoices:           Mapped[list["Invoice"]]         = relationship("Invoice",          back_populates="staff")
    # ✅ FIX 3: added chat relationships
    chat_group_members: Mapped[List["ChatGroupMember"]] = relationship("ChatGroupMember",  back_populates="staff")    
    # in company.py — make sure back_populates matches
  