from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users.user import User
from app.models.staffs.staff import Staff
from app.models.roles.role import Role


class AuthRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    # -----------------------------------------------------------------------
    # GET all users — scoped to company
    # -----------------------------------------------------------------------

    async def get_all(self, company_id: int) -> list[User]:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.company_id == company_id)   # ✅ scope to company
            .order_by(User.full_name)
        )
        return result.scalars().all()

    # -----------------------------------------------------------------------
    # GET by id — scoped to company
    # -----------------------------------------------------------------------

    async def get_by_id(self, user_id: int, company_id: int) -> User | None:
        result = await self.db.execute(
            select(User)
            .options(
                selectinload(User.role),
                selectinload(User.department),
                selectinload(User.staff),
            )
            .where(
                User.user_id    == user_id,
                User.company_id == company_id,   # ✅ scope to company
            )
        )
        # ✅ return None instead of raising — let service handle 404
        return result.scalar_one_or_none()

    # -----------------------------------------------------------------------
    # GET by username — NO company_id filter
    # login doesn't know company_id yet, username is globally unique
    # -----------------------------------------------------------------------

    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(
            select(User)
            .options(
                selectinload(User.role),
                selectinload(User.department),
            )
            .where(User.username == username)
            # ✅ intentionally no company_id — username is globally unique
        )
        return result.scalar_one_or_none()

    # -----------------------------------------------------------------------
    # GET staff by user_id — used in login to build JWT payload
    # -----------------------------------------------------------------------

    async def get_staff_by_user_id(self, user_id: int) -> Staff | None:
        result = await self.db.execute(
            select(Staff)
            .options(
                joinedload(Staff.staff_role)   # load is_manager
            )
            .where(Staff.user_id == user_id)
            # ✅ no company_id here — called right after get_by_username
            # which already validated the user
        )
        return result.scalar_one_or_none()

    # -----------------------------------------------------------------------
    # GET role by name — used in setup/seed
    # -----------------------------------------------------------------------

    async def get_role_by_name(
        self, role_name: str, company_id: int
    ) -> Role | None:
        result = await self.db.execute(
            select(Role).where(
                Role.role_name  == role_name,
                Role.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    # -----------------------------------------------------------------------
    # CHECK username exists — used before creating user
    # -----------------------------------------------------------------------

    async def exists_by_username(self, username: str) -> bool:
        result = await self.db.execute(
            select(User.user_id).where(User.username == username)
        )
        return result.scalar_one_or_none() is not None

    # -----------------------------------------------------------------------
    # LOAD permissions — based on role name
    # -----------------------------------------------------------------------

    async def load_permissions(
        self, user_id: int, role_name: str
    ) -> list[str]:
        if role_name == "superuser":
            return ["*"]

        if role_name == "admin":
            return [
                "read_all",
                "write_all",
                "delete_users",
                "manage_roles",
                "view_audit_logs",
            ]

        if role_name == "manager":
            return [
                "read_staff",
                "write_staff",
                "approve_leave",
                "view_attendance",
                "manage_salary",
            ]

        # staff / default
        return [
            "read_own_profile",
            "request_leave",
            "view_own_attendance",
            "view_own_salary",
        ]

    # -----------------------------------------------------------------------
    # CREATE user
    # -----------------------------------------------------------------------

    async def create(self, **kwargs) -> User:
        user = User(**kwargs)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    # -----------------------------------------------------------------------
    # UPDATE user
    # -----------------------------------------------------------------------

    async def update(
        self, user_id: int, company_id: int, **kwargs
    ) -> User | None:
        # ✅ pass company_id — scope to company
        user = await self.get_by_id(user_id, company_id)
        if not user:
            return None
        for key, value in kwargs.items():
            setattr(user, key, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user