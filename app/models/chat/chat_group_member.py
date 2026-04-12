# in chat_group_member.py — replace user_id with staff_id
from sqlalchemy import Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import TYPE_CHECKING
from app.db.base import Base

if TYPE_CHECKING:
    from ..staffs.staff import Staff  
    from ..company import Company
    from .chat_group import ChatGroup


class ChatGroupMember(Base):
    __tablename__ = "chat_group_members"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int]      = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    group_id:   Mapped[int]      = mapped_column(Integer, ForeignKey("chat_groups.group_id"), nullable=False)
    staff_id:   Mapped[int]      = mapped_column(Integer, ForeignKey("staff.staff_id"), nullable=False)
    joined_at:  Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    is_admin:   Mapped[bool]     = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    company: Mapped["Company"]   = relationship("Company",   back_populates="chat_group_members")
    group:   Mapped["ChatGroup"] = relationship("ChatGroup", back_populates="members")
    # ✅ staff not user
    staff:   Mapped["Staff"]     = relationship("Staff", foreign_keys=[staff_id],   back_populates="chat_group_members")