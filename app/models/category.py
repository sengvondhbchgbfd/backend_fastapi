from sqlalchemy import Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional,TYPE_CHECKING
from app.db.base import Base

if TYPE_CHECKING:
    from .products import Product
    from .company import Company

class Category(Base):
    __tablename__ = "categories"

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)

    category_name: Mapped[str] = mapped_column(String(150), nullable=False)
    category_total: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), default=0)
    
    image_url:      Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    image_public_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="categories")
    products: Mapped[list["Product"]] = relationship("Product", back_populates="category")