from sqlalchemy import Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from app.db.base import Base

if  TYPE_CHECKING:
    from .invoices import Invoice
    from .company import Company

class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)

    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    total_purchase: Mapped[float] = mapped_column(Numeric(14, 2), default=0)

    # ✅ cloudinary image
    avatar_url:       Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    avatar_public_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="customers")
    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="customer")