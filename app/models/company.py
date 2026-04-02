from  sqlalchemy import Column, Integer, String, Enum, Boolean,DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

import enum
class PlanType(str, enum.Enum):
   free       = "free"
   pro        = "pro"
   enterprise = "enterprise"

class CompanyStatus(str, enum.Enum):
    active    = "active"
    suspended = "suspended"
    cancelled = "cancelled"
class Company(Base):
    __tablename__ = "companies"
 
    company_id   = Column(Integer, primary_key=True, autoincrement=True, index=True)
    company_name = Column(String(255), nullable=False)
    company_code = Column(String(50),  nullable=False, unique=True, index=True)
    email        = Column(String(255), nullable=True)
    phone        = Column(String(50),  nullable=True)
    address      = Column(Text,        nullable=True)
    logo_url     = Column(String(500), nullable=True)
    plan_type    = Column(Enum(PlanType),      default=PlanType.free,      nullable=False)
    status       = Column(Enum(CompanyStatus), default=CompanyStatus.active, nullable=False)
    max_users    = Column(Integer,     default=10)
    timezone     = Column(String(100), default="UTC")
    currency     = Column(String(10),  default="USD")
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    expires_at   = Column(DateTime(timezone=True), nullable=True)

    # Image file add

    logo_url     = Column(Text,        nullable=True)
    logo_public_id  = Column(Text,     nullable=True)
    banner_url      = Column(Text,     nullable=True)
    banner_public_id = Column(Text,    nullable=True)
    updated_at        = Column(DateTime(timezone=True), server_default=func.now(),onupdate=func.now(), nullable=False)
    # logo_url     = Column(DateTime(timezone=True), nullable=True)
    # Relationships
    users              = relationship("User",             back_populates="company", cascade="all, delete-orphan")
    roles              = relationship("Role",             back_populates="company", cascade="all, delete-orphan")
    departments        = relationship("Department",       back_populates="company", cascade="all, delete-orphan")
    staff_roles        = relationship("StaffRole",        back_populates="company", cascade="all, delete-orphan")
    staff              = relationship("Staff",            back_populates="company", cascade="all, delete-orphan")
    leave_requests     = relationship("LeaveRequest",     back_populates="company", cascade="all, delete-orphan")
    attendance_records = relationship("AttendanceRecord", back_populates="company", cascade="all, delete-orphan")
    audit_logs         = relationship("AuditLog",         back_populates="company", cascade="all, delete-orphan")
    system_settings    = relationship("SystemSetting",    back_populates="company", cascade="all, delete-orphan")
    notifications      = relationship("Notification",     back_populates="company", cascade="all, delete-orphan")
    salaries           = relationship("Salary",           back_populates="company", cascade="all, delete-orphan")
    salary_adjustments = relationship("SalaryAdjustment", back_populates="company", cascade="all, delete-orphan")
    suppliers          = relationship("Supplier",         back_populates="company", cascade="all, delete-orphan")
    categories         = relationship("Category",         back_populates="company", cascade="all, delete-orphan")
    products           = relationship("Product",          back_populates="company", cascade="all, delete-orphan")
    product_images     = relationship("ProductImage",     back_populates="company", cascade="all, delete-orphan")
    stock_movements    = relationship("StockMovement",    back_populates="company", cascade="all, delete-orphan")
    customers          = relationship("Customer",         back_populates="company", cascade="all, delete-orphan")
    invoices           = relationship("Invoice",          back_populates="company", cascade="all, delete-orphan")
    invoice_items      = relationship("InvoiceItem",      back_populates="company", cascade="all, delete-orphan")
    chat_groups        = relationship("ChatGroup",        back_populates="company", cascade="all, delete-orphan")
    chat_messages      = relationship("ChatMessage",      back_populates="company", cascade="all, delete-orphan")
    chat_group_members = relationship("ChatGroupMember",  back_populates="company", cascade="all, delete-orphan")
 