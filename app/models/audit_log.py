from sqlalchemy import Integer, String, JSON, ForeignKey,DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Any,TYPE_CHECKING
from app.db.base import Base



if TYPE_CHECKING:
    from .users import User
    from .company import Company

class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)   # INSERT | UPDATE | DELETE
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[int] = mapped_column(Integer, nullable=False)
    old_value: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    new_value: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    # created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


    # Relationships
    
    company: Mapped["Company"] = relationship("Company", back_populates="audit_logs")
    user: Mapped["User"] = relationship("User", back_populates="audit_logs")