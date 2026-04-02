from sqlalchemy import Integer, String, Text, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from app.db.base import Base




if TYPE_CHECKING:
    from ..category import Category
    from ..invoices.invoice_item import InvoiceItem
    from .stock_movement import StockMovement
    from ..company import Company
    from .product_image import ProductImage
    
class Product(Base):
    __tablename__ = "products"
    
    product_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.category_id"), nullable=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    length_width: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    descriptions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    # created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships

    company: Mapped["Company"] = relationship("Company", back_populates="products")
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="products")
    stock_movements: Mapped[list["StockMovement"]] = relationship("StockMovement", back_populates="product")
    images: Mapped[list["ProductImage"]] = relationship("ProductImage",back_populates="product", cascade="all, delete-orphan")
    invoice_items: Mapped[list["InvoiceItem"]] = relationship("InvoiceItem", back_populates="product")
    