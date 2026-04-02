from sqlalchemy import Integer, Text, Boolean, DateTime, ForeignKey, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from app.db.base import Base
import enum

if TYPE_CHECKING:
    from ..users import User
    from ..company import Company
    from .chat_group import ChatGroup

class MessageType(str, enum.Enum):
    text  = "text"
    image = "image"
    file  = "file"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    message_id:   Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id:   Mapped[int]           = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    group_id:     Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("chat_groups.group_id"), nullable=True)
    sender_id:    Mapped[int]           = mapped_column(Integer, ForeignKey("users.user_id"), nullable=False)
    receiver_id:  Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.user_id"), nullable=True)
    # message_text: Mapped[str]           = mapped_column(Text,    nullable=False)
    message_type: Mapped[MessageType] = mapped_column(Enum(MessageType), default=MessageType.text, nullable=False)
    content:      Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp:    Mapped[datetime]      = mapped_column(DateTime, default=func.now(), nullable=False)
    file_url:     Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_name:    Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_size:    Mapped[Optional[int]] = mapped_column(Integer, nullable=True) 
    is_deleted:   Mapped[bool]         = mapped_column(Boolean, default=False, nullable=False)
    is_read:      Mapped[bool]          = mapped_column(Boolean,  default=False)
    # created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


    # Relationships
    company:  Mapped["Company"]           = relationship("Company",   back_populates="chat_messages")
    group:    Mapped[Optional["ChatGroup"]] = relationship("ChatGroup", back_populates="messages")
    sender:   Mapped["User"]              = relationship("User", foreign_keys=[sender_id],   back_populates="sent_messages")
    receiver: Mapped[Optional["User"]]    = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")