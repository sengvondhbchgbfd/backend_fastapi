from sqlalchemy import Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..users.user import User
    from ..company import Company
class Role(Base):
    __tablename__ = "roles"

    # ✅ unique per company — not globally
    __table_args__ = (UniqueConstraint("company_id", "role_name", name="uq_roles_company_role", ),)
    role_id:    Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.company_id"), nullable=False, index=True)
    # ✅ removed unique=True — handled by __table_args__
    role_name:  Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    company: Mapped["Company"]      = relationship("Company", back_populates="roles")
    users:   Mapped[list["User"]]   = relationship("User",    back_populates="role")