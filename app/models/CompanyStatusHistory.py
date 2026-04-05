from sqlalchemy import Column, Integer, Enum, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.company import CompanyStatus
from app.db.base import Base



class CompanyStatusHistory(Base):
    __tablename__ = "company_status_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=False)
    old_status = Column(Enum(CompanyStatus), nullable=False)
    new_status = Column(Enum(CompanyStatus), nullable=False)
    reason = Column(Text, nullable=True)
    changed_by = Column(Integer, nullable=False)  # superuser ID
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    company = relationship("Company", back_populates="status_history")