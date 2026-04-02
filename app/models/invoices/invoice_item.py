from sqlalchemy import Integer, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .invoice import Invoice
    from ..products import Product
    from ..company import Company

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    item_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey("invoices.invoice_id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="invoice_items")
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="invoice_items")