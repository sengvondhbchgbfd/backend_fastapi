from sqlalchemy import Integer, String, Text, Numeric, ForeignKey, DateTime,Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from app.db.base import Base

if TYPE_CHECKING:
    from ..company import Company
    from .product import Product


class ProductImage(Base):

    __tablename__ = "product_images"
    images_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.product_id"), nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    image_url:      Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    image_public_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_primary:      Mapped[bool]          = mapped_column(Boolean,  default=False)
    sort_order:     Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships

    product: Mapped["Product"] = relationship("Product", back_populates="images")
    company: Mapped["Company"] = relationship("Company", back_populates="product_images")
