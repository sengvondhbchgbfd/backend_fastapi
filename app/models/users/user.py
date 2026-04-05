from sqlalchemy import Integer, String, ForeignKey, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import enum

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.departments.department import Department
    from app.models.roles.role import Role
    from app.models.staffs.staff import Staff
    from app.models.audit_log import AuditLog
    from app.models.notification import Notification
    from app.models.chat.chat_message import ChatMessage
    from app.models.company import Company 
    from app.models.refresh_token import RefreshToken       


class UserStatus(str, enum.Enum):
    active   = "active"
    inactive = "inactive"


class User(Base):
    __tablename__ = "users"

    user_id:       Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id:    Mapped[int]           = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    username:      Mapped[str]           = mapped_column(String(100), nullable=False, unique=True)
    password_hash: Mapped[str]           = mapped_column(String(255), nullable=False)
    full_name:     Mapped[str]           = mapped_column(String(150), nullable=False)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("departments.department_id"), nullable=True)
    role_id:       Mapped[int]           = mapped_column(Integer, ForeignKey("roles.role_id"), nullable=False)
    status:        Mapped[UserStatus]    = mapped_column(Enum(UserStatus), default=UserStatus.active, nullable=False)
    # image
    # avatar_url:    Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # avatar_public_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # created_at:    Mapped[datetime]      = mapped_column(DateTime, default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    # updated_at:    Mapped[datetime]      = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    company:             Mapped["Company"]              = relationship("Company",     back_populates="users")
    role:                Mapped["Role"]                 = relationship("Role",        back_populates="users")
    department:          Mapped[Optional["Department"]] = relationship("Department",  foreign_keys=[department_id],        back_populates="users")
    managed_departments: Mapped[list["Department"]]     = relationship("Department",  foreign_keys="Department.manager_id", back_populates="manager")
    staff:               Mapped[Optional["Staff"]]      = relationship("Staff",       back_populates="user", uselist=False)
    audit_logs:          Mapped[list["AuditLog"]]       = relationship("AuditLog",    back_populates="user")
    notifications:       Mapped[list["Notification"]]   = relationship("Notification", back_populates="user")
    sent_messages:       Mapped[list["ChatMessage"]]    = relationship("ChatMessage", foreign_keys="ChatMessage.sender_id",   back_populates="sender")
    received_messages:   Mapped[list["ChatMessage"]]    = relationship("ChatMessage", foreign_keys="ChatMessage.receiver_id", back_populates="receiver")
    refreshtokens:       Mapped[list["RefreshToken"]]  = relationship("RefreshToken", back_populates="user")
    # ✅ REMOVED chat_group_members — belongs to Staff not User

    # staff: Mapped[Optional["Staff"]] = relationship("Staff", back_populates="user", uselist=False)
