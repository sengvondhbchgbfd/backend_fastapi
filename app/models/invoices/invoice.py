from sqlalchemy import Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional,TYPE_CHECKING
from app.db.base import Base


if TYPE_CHECKING:
    from ..customer import Customer
    from ..staffs import Staff
    from .invoice_item import InvoiceItem
    from company import Company




class Invoice(Base):
    __tablename__ = "invoices"

    invoice_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    customer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("customers.customer_id"), nullable=True)
    staff_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("staff.staff_id"), nullable=True)
    total_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    discount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    tax: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    payment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="invoices")
    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="invoices")
    staff: Mapped[Optional["Staff"]] = relationship("Staff", back_populates="invoices")
    items: Mapped[list["InvoiceItem"]] = relationship("InvoiceItem", back_populates="invoice")