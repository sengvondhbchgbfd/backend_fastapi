from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.users.user import User
from app.models.roles.role import Role
from app.models.departments.department import Department
from sqlalchemy import func, select


# ===========================================================================
# ROLE REPOSITORY
# ===========================================================================



class RoleRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, role_name: str, company_id: int) -> Role:
        role = Role(
            role_name  = role_name,
            company_id = company_id,   # ✅ required
        )
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def get_by_id(self, role_id: int, company_id: int) -> Role | None:
        result = await self.db.execute(
            select(Role).where(
                Role.role_id   == role_id,
                Role.company_id == company_id,   # ✅ scope to company
            )
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, role_name: str, company_id: int) -> Role | None:
        result = await self.db.execute(
            select(Role).where(
                Role.role_name  == role_name,
                Role.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_all(self, company_id: int) -> list[Role]:
        result = await self.db.execute(
            select(Role)
            .where(Role.company_id == company_id)   # ✅ scope to company
            .order_by(Role.role_name)
        )
        return result.scalars().all()

    async def update(self, role: Role, data: dict) -> Role:
        for field, value in data.items():
            if value is not None:
                setattr(role, field, value)
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def delete(self, role_id: int, company_id: int) -> bool:
        role = await self.get_by_id(role_id, company_id)
        if not role:
            return False
        await self.db.delete(role)
        await self.db.commit()
        return True
    

# ===========================================================================
# USER REPOSITORY
# ===========================================================================

class UserRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> User:
        user = User(**kwargs)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    

    async def get_by_id(self, user_id: int, company_id: int) -> User | None:
        result = await self.db.execute(
            select(User)
            .options(
                selectinload(User.role),
                selectinload(User.department),
                selectinload(User.staff),
            )
            .where(
                User.user_id   == user_id,
                User.company_id == company_id,   # ✅ scope to company
            )
        )
        user = result.scalar_one_or_none()
        if user:
           await self.db.refresh(user)

        return user



    async def get_by_username(self, username: str) -> User | None:
        """
        No company_id filter here — username is globally unique.
        Used by login which doesn't know company_id yet.
        """
        result = await self.db.execute(
            select(User)
            .options(
                selectinload(User.role),
                selectinload(User.staff),
            )
            .where(User.username == username)
        )
        return result.scalar_one_or_none()
    
# ===============================================================
#   count
# ===============================================================

    async def count(self, company_id: int) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(User)
            .where(User.company_id == company_id)
        )
        return result.scalar() or 0
    

# ===============================================================
# get all
# ===============================================================


    async def get_all(
            self, 
            company_id: int,
            skip: int =0,
            limit: int = 20
            ) -> list[User]:
        result = await self.db.execute(
            select(User)
            .options(
                selectinload(User.role),
                selectinload(User.department),
                selectinload(User.staff)
            )
            .where(User.company_id == company_id)
            .order_by(User.full_name)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()




# ===============================================================
# 
# ===============================================================



    async def get_by_department(
        self, department_id: int, company_id: int
    ) -> list[User]:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(
                User.department_id == department_id,
                User.company_id    == company_id,
            )
        )
        return result.scalars().all()

    async def update(self, user: User, data: dict) -> User:
        for field, value in data.items():
            if value is not None:
                setattr(user, field, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user_id: int, company_id: int) -> bool:
        user = await self.get_by_id(user_id, company_id)
        if not user:
            return False
        await self.db.delete(user)
        await self.db.commit()
        return True


# ===========================================================================
# DEPARTMENT REPOSITORY
# ===========================================================================

class DepartmentRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        department_name: str,
        company_id:      int,
        manager_id:      int | None = None,
    ) -> Department:
        department = Department(
            department_name = department_name,
            company_id      = company_id,   # ✅ required
            manager_id      = manager_id,
        )
        self.db.add(department)
        await self.db.commit()
        await self.db.refresh(department)
        return department

    async def get_by_id(
        self, department_id: int, company_id: int
    ) -> Department | None:
        result = await self.db.execute(
            select(Department)
            .options(selectinload(Department.manager))
            .where(
                Department.department_id == department_id,
                Department.company_id    == company_id,   # ✅ scope to company
            )
        )
        return result.scalar_one_or_none()

    async def get_by_name(
        self, department_name: str, company_id: int
    ) -> Department | None:
        result = await self.db.execute(
            select(Department).where(
                Department.department_name == department_name,
                Department.company_id      == company_id,
            )
        )
        return result.scalar_one_or_none()



    async def get_all(self, company_id: int) -> list[Department]:
        result = await self.db.execute(
            select(Department)
            .options(selectinload(Department.manager))
            .where(Department.company_id == company_id)   # ✅ scope to company
            .order_by(Department.department_name)
        )
        return result.scalars().all()
    

    

    async def update(self, department: Department, data: dict) -> Department:
        for field, value in data.items():
            if value is not None:
                setattr(department, field, value)
        await self.db.commit()
        await self.db.refresh(department)
        return department

    async def delete(self, department_id: int, company_id: int) -> bool:
        department = await self.get_by_id(department_id, company_id)
        if not department:
            return False
        await self.db.delete(department)
        await self.db.commit()
        return True