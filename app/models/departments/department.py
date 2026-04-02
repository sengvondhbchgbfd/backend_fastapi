from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.users.user import User
    from ..company import Company


class Department(Base):
    __tablename__ = "departments"

    department_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    department_name: Mapped[str] = mapped_column(String(150), nullable=False)  # ← fixed double underscore
    manager_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.user_id", use_alter=True, name="fk_department_manager"), nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="departments")
    manager: Mapped[Optional["User"]] = relationship("User", foreign_keys=[manager_id], back_populates="managed_departments")
    users: Mapped[list["User"]] = relationship("User", foreign_keys="User.department_id", back_populates="department")