from sqlalchemy import Column, Integer, String, Boolean, DateTime,ForeignKey
from datetime import datetime
from  sqlalchemy.sql import func
from  app.db.base import Base
from sqlalchemy.orm import Mapped, relationship, mapped_column

from typing import TYPE_CHECKING

from app.db.base import Base
if TYPE_CHECKING:
    from .users import User
    from .company import Company

class RefreshToken(Base):
    __tablename__ ="refresh_token"

    id:            Mapped[int]   = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    token_hash:  Mapped[String]  = mapped_column(String, nullable=False, unique=True, index=True)  # store hash not raw
    is_revoked:   Mapped[Boolean] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    expires_at    = Column(DateTime(timezone=True), nullable=False)

      # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="refreshtokens")
    user: Mapped["User"] = relationship("User", back_populates="refreshtokens")




