from sqlalchemy import Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from app.db.base import Base

if TYPE_CHECKING:
    from .invoice import Invoice


class InvoiceAttachment(Base):
    __tablename__ = "invoice_attachments"

    attachment_id: Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id:    Mapped[int]           = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    invoice_id:    Mapped[int]           = mapped_column(Integer, ForeignKey("invoices.invoice_id", ondelete="CASCADE"), nullable=False, index=True)
    file_url:      Mapped[str]           = mapped_column(String(500), nullable=False)
    public_id:     Mapped[str]           = mapped_column(String(300), nullable=False)
    file_name:     Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_type:     Mapped[Optional[str]] = mapped_column(String(60),  nullable=True)
    created_at:    Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="attachments")