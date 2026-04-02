from sqlalchemy import Integer, String, DateTime, ForeignKey, Text, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, TYPE_CHECKING, List
from app.db.base import Base
import enum

if TYPE_CHECKING:
    from ..users import User
    from ..company import Company
    from .chat_message import ChatMessage
    from .chat_group_member import ChatGroupMember




class ChatType(str, enum.Enum):
    group  = "group"
    direct = "direct"
 
 



class ChatGroup(Base):
    __tablename__ = "chat_groups"

    group_id:   Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int]      = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    group_name: Mapped[str]      = mapped_column(String(150), nullable=False)
    chat_type:  Mapped[ChatType]     = mapped_column(Enum(ChatType), default=ChatType.group, nullable=False)

    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.user_id"), nullable=True)
    is_active:  Mapped[bool]     = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())






    # Relationships
    company: Mapped["Company"]               = relationship("Company",         back_populates="chat_groups")
    creator: Mapped[Optional["User"]]        = relationship("User",            foreign_keys=[created_by])
    members: Mapped[List["ChatGroupMember"]] = relationship("ChatGroupMember", back_populates="group", cascade="all, delete-orphan")
    messages: Mapped[List["ChatMessage"]]    = relationship("ChatMessage",     back_populates="group")