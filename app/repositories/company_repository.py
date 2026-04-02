from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.models.company import Company
from app.models.staffs.staff import Staff
from app.models.departments.department import Department
from app.models.users.user import User, UserStatus
from app.models.roles.role import Role
class CompanyRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    # -----------------------------------------------------------------------
    # Read
    # -----------------------------------------------------------------------

    async def get_all(self) -> list[Company]:
        result = await self.db.execute(
            select(Company).order_by(Company.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_id(self, company_id: int) -> Company | None:
        result = await self.db.execute(
            select(Company).where(Company.company_id == company_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, company_code: str) -> Company | None:
        result = await self.db.execute(
            select(Company).where(
                Company.company_code == company_code.upper()
            )
        )
        return result.scalar_one_or_none()

    # -----------------------------------------------------------------------
    # Create
    # -----------------------------------------------------------------------

    async def create(self, data: dict) -> Company:
        company = Company(**data)
        self.db.add(company)
        await self.db.commit()
        await self.db.refresh(company)
        return company

    # -----------------------------------------------------------------------
    # Update
    # -----------------------------------------------------------------------



    async def update(self, company: Company, data: dict) -> Company:
        for key, value in data.items():
            if value is not None:
                setattr(company, key, value)
        await self.db.commit()
        await self.db.refresh(company)
        return company
    



    # -----------------------------------------------------------------------
    # Delete
    # -----------------------------------------------------------------------

    async def delete(self, company: Company) -> None:
        await self.db.delete(company)
        await self.db.commit()

    # -----------------------------------------------------------------------
    # Stats
    # -----------------------------------------------------------------------

    async def get_stats(self, company_id: int) -> dict:
        # total staff
        staff_count = await self.db.execute(
            select(func.count()).select_from(Staff)
            .where(Staff.company_id == company_id)
        )

        # total departments
        dept_count = await self.db.execute(
            select(func.count()).select_from(Department)
            .where(Department.company_id == company_id)
        )

        # total users
        user_count = await self.db.execute(
            select(func.count()).select_from(User)
            .where(User.company_id == company_id)
        )

        # active users
        active_count = await self.db.execute(
            select(func.count()).select_from(User)
            .where(
                User.company_id == company_id,
                User.status     == UserStatus.active,
            )
        )

        # total roles
        role_count = await self.db.execute(
            select(func.count()).select_from(Role)
            .where(Role.company_id == company_id)
        )

        return {
            "total_staff":       staff_count.scalar() or 0,
            "total_departments": dept_count.scalar()  or 0,
            "total_users":       user_count.scalar()  or 0,
            "active_users":      active_count.scalar() or 0,
            "total_roles":       role_count.scalar()  or 0,
        }