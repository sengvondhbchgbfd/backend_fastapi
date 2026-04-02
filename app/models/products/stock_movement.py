from sqlalchemy import Integer, String, Numeric, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
from app.db.base import Base


if TYPE_CHECKING:
    from .product import Product
    from ..company import Company



class StockMovement(Base):
    __tablename__ = "stock_movements"

    movement_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.product_id"), nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    qty_in: Mapped[int] = mapped_column(Integer, default=0)
    qty_out: Mapped[int] = mapped_column(Integer, default=0)
    balance_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    movement_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    date: Mapped[Optional[str]] = mapped_column(Date, nullable=True)
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    unit_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    opening_balance: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="stock_movements")
    product: Mapped["Product"] = relationship("Product", back_populates="stock_movements")