from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import Optional
from decimal import Decimal

from app.models.staffs.staff import Staff
from app.models.staffs.staff_role import StaffRole
from app.schemas.schema import StaffRoleCreate


# ===========================================================================
# STAFF ROLE REPOSITORY
# ===========================================================================

class StaffRolesRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: StaffRoleCreate, company_id: int) -> StaffRole:
        payload = data.model_dump(exclude_none=True)

        # Ensure base_salary is Decimal
        if "base_salary" in payload and payload["base_salary"] is not None:
            payload["base_salary"] = Decimal(str(payload["base_salary"]))

        # ✅ always inject company_id
        payload["company_id"] = company_id

        staff_role = StaffRole(**payload)
        self.db.add(staff_role)
        await self.db.commit()
        await self.db.refresh(staff_role)
        return staff_role
    



    async def get_by_id(
        self, 
        staff_role_id: int, 
        company_id: int
    ) -> StaffRole | None:
        result = await self.db.execute(
            select(StaffRole).where(
                StaffRole.staff_role_id == staff_role_id,
                StaffRole.company_id    == company_id,   # ✅ scope to company
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(
        self, role_name: str, company_id: int
    ) -> StaffRole | None:
        result = await self.db.execute(
            select(StaffRole).where(
                StaffRole.role_name  == role_name,
                StaffRole.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_all(self, company_id: int) -> list[StaffRole]:
        result = await self.db.execute(
            select(StaffRole)
            .where(StaffRole.company_id == company_id)   # ✅ scope to company
            .order_by(StaffRole.role_name)
        )
        return result.scalars().all()

    async def update(
        self, staff_role_id: int, data: dict, company_id: int
    ) -> StaffRole | None:
        # Ensure base_salary is Decimal
        if "base_salary" in data and data["base_salary"] is not None:
            data["base_salary"] = Decimal(str(data["base_salary"]))

        await self.db.execute(
            update(StaffRole)
            .where(
                StaffRole.staff_role_id == staff_role_id,
                StaffRole.company_id    == company_id,
            )
            .values(**data)
        )
        await self.db.commit()
        return await self.get_by_id(staff_role_id, company_id)

    async def delete(self, staff_role_id: int, company_id: int) -> bool:
        staff_role = await self.get_by_id(staff_role_id, company_id)
        if not staff_role:
            return False
        await self.db.delete(staff_role)
        await self.db.commit()
        return True
# ===========================================================================
# STAFF REPOSITORY
# ===========================================================================

class StaffRepository:

    def __init__(self, db: AsyncSession):
        self.db = db
    # -----------------------------------------------------------------------
    # GET all staff
    # -----------------------------------------------------------------------
    async def get_all(self, company_id: int) -> list[Staff]:
        result = await self.db.execute(
            select(Staff)
            .options(
                selectinload(Staff.user),
                selectinload(Staff.staff_role),
            )
            .where(Staff.company_id == company_id)   # ✅ scope to company
            .order_by(Staff.name)
        )
        return result.scalars().all()
    # -----------------------------------------------------------------------
    # GET one staff by id (full detail)
    # -----------------------------------------------------------------------



    async def get_by_id(self, staff_id: int, company_id: int) -> Staff | None:
        result = await self.db.execute(
            select(Staff)
            .options(selectinload(Staff.staff_role))
            .where(
                Staff.staff_id   == staff_id,    
                Staff.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()
    



    # -----------------------------------------------------------------------
    # GET staff by user_id (used in login to get staff_id from JWT)
    # -----------------------------------------------------------------------

    async def get_by_user_id(
        self, user_id: int, company_id: int
    ) -> Staff | None:
        result = await self.db.execute(
            select(Staff)
            .options(selectinload(Staff.staff_role))
            .where(
                Staff.user_id    == user_id,
                Staff.company_id == company_id,   # ✅ scope to company
            )
        )
        return result.scalar_one_or_none()

    # -----------------------------------------------------------------------
    # GET staff by email
    # -----------------------------------------------------------------------

    async def get_by_email(
        self, email: str, company_id: int
    ) -> Staff | None:
        result = await self.db.execute(
            select(Staff).where(
                Staff.email      == email,
                Staff.company_id == company_id,   # ✅ scope to company
            )
        )
        return result.scalar_one_or_none()

    # -----------------------------------------------------------------------
    # GET staff by role
    # ✅ FIX: was filtering by staff_id instead of staff_role_id
    # -----------------------------------------------------------------------

    async def get_by_role(
        self, staff_role_id: int, company_id: int
    ) -> list[Staff]:
        result = await self.db.execute(
            select(Staff)
            .options(selectinload(Staff.staff_role))
            .where(
                Staff.staff_role_id == staff_role_id,  # ✅ was Staff.staff_id
                Staff.company_id    == company_id,
            )
        )
        return result.scalars().all()

    # -----------------------------------------------------------------------
    # GET managers only (is_manager = True)
    # -----------------------------------------------------------------------

    async def get_managers(self, company_id: int) -> list[Staff]:
        result = await self.db.execute(
            select(Staff)
            .join(StaffRole, Staff.staff_role_id == StaffRole.staff_role_id)
            .options(
                selectinload(Staff.user),
                selectinload(Staff.staff_role),
            )
            .where(
                Staff.company_id       == company_id,
                StaffRole.is_manager   == True,
            )
        )
        return result.scalars().all()

    # -----------------------------------------------------------------------
    # GET staff by department
    # -----------------------------------------------------------------------

    async def get_by_department(
        self, department_id: int, company_id: int
    ) -> list[Staff]:
        result = await self.db.execute(
            select(Staff)
            .options(
                selectinload(Staff.user),
                selectinload(Staff.staff_role),
            )
            .join(Staff.user)
            .where(
                Staff.company_id         == company_id,
                Staff.user.has(department_id=department_id),
            )
        )
        return result.scalars().all()

    # -----------------------------------------------------------------------
    # CREATE staff
    # -----------------------------------------------------------------------

    async def create(self, staff: Staff) -> Staff:
        self.db.add(staff)
        await self.db.commit()
        await self.db.refresh(staff)
        return staff

    # -----------------------------------------------------------------------
    # UPDATE staff
    # -----------------------------------------------------------------------


    async def update(
            self, staff_id: int, data: dict, company_id: int
            ) -> Staff | None:
                await self.db.execute(
                    update(Staff)                       
                    .where(
                        Staff.staff_id   == staff_id,
                        Staff.company_id == company_id,
                    )
                    .values(**data)                      
                )
                await self.db.commit()
                return await self.get_by_id(staff_id, company_id)
    
    # -----------------------------------------------------------------------
    # Only avartar
    # -----------------------------------------------------------------------

    
    async def update_avatar(
            self,
            staff_id:         int,
            company_id:       int,
            avatar_url:       str,
            avatar_public_id: str,
        ) -> Staff | None:
            await self.db.execute(
                update(Staff)
                .where(
                    Staff.staff_id   == staff_id,
                    Staff.company_id == company_id,
                )
                .values(
                    avatar_url       = avatar_url,       
                    avatar_public_id = avatar_public_id,
                )
            )
            await self.db.commit()
            return await self.get_by_id(staff_id, company_id)
        



    # -----------------------------------------------------------------------
    # DELETE staff
    # -----------------------------------------------------------------------

    async def delete(self, staff_id: int, company_id: int) -> bool:
        result = await self.db.execute(
            delete(Staff)
            .where(
                Staff.staff_id   == staff_id,
                Staff.company_id == company_id,   # ✅ scope to company
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    # -----------------------------------------------------------------------
    # CHECK exists
    # -----------------------------------------------------------------------

    async def exists_by_user_id(
        self, user_id: int, company_id: int
    ) -> bool:
        result = await self.db.execute(
            select(Staff.staff_id).where(
                Staff.user_id    == user_id,
                Staff.company_id == company_id,
            )
        )
        return result.scalar_one_or_none() is not None