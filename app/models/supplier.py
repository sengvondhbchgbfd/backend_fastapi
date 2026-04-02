from sqlalchemy import Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from   .company import Company


from datetime import datetime
from typing import Optional
from app.db.base import Base

class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    contact_person: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    avatar_url:    Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    avatar_public_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


    company: Mapped["Company"] = relationship("Company", back_populates="suppliers")
