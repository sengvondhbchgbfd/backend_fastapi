from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.users.user import User
from app.models.company import Company
from app.models.roles.role import Role
from app.models.departments.department import Department


class SetupRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    # -----------------------------------------------------------------------
    # CHECK initialized — count users
    # -----------------------------------------------------------------------

    async def count_users(self) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(User)
        )
        return result.scalar() or 0
    





    # -----------------------------------------------------------------------
    # CHECK duplicates
    # -----------------------------------------------------------------------

    async def get_company_by_code(self, code: str) -> Company | None:
        result = await self.db.execute(
            select(Company).where(
                Company.company_code == code.upper()
            )
        )
        return result.scalar_one_or_none()
    



    async def get_user_by_username(self, username: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    # -----------------------------------------------------------------------
    # CREATE company
    # -----------------------------------------------------------------------

    async def create_company(
        self,
        company_name: str,
        company_code: str,
        timezone:     str,
        currency:     str,
    ) -> Company:
        company = Company(
            company_name = company_name,
            company_code = company_code.upper(),
            plan_type    = "enterprise",
            status       = "active",
            timezone     = timezone,
            currency     = currency,
        )
        self.db.add(company)
        await self.db.flush()   # get company_id without full commit
        return company

    # -----------------------------------------------------------------------
    # CREATE default roles
    # -----------------------------------------------------------------------

    async def create_default_roles(
        self, company_id: int
    ) -> dict[str, Role]:
        role_names = ["superuser", "admin", "manager", "staff"]
        roles      = {}
        for role_name in role_names:
            role = Role(
                company_id = company_id,
                role_name  = role_name,
            )
            self.db.add(role)
            await self.db.flush()
            roles[role_name] = role

        return roles
    
    # -----------------------------------------------------------------------
    # CREATE default department
    # -----------------------------------------------------------------------

    async def create_default_department(
        self, company_id: int
    ) -> Department:
        dept = Department(
            company_id      = company_id,
            department_name = "Management",
        )
        self.db.add(dept)
        await self.db.flush()
        return dept

    # -----------------------------------------------------------------------
    # CREATE superuser
    # -----------------------------------------------------------------------

    async def create_superuser(
        self,
        company_id:    int,
        username:      str,
        password_hash: str,
        full_name:     str,
        role_id:       int,
        department_id: int,
    ) -> User:
        from app.models.users.user import UserStatus
        user = User(
            company_id    = company_id,
            username      = username,
            password_hash = password_hash,
            full_name     = full_name,
            role_id       = role_id,
            department_id = department_id,
            status        = UserStatus.active,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user