from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.users.user import User
from app.models.roles.role import Role
from app.models.departments.department import Department
from app.models.company import Company
from app.core.security import hash_password


async def seed_data(db: AsyncSession):

    # ─────────────────────────────────────────
    # 1. Seed Company (required first — all FKs depend on it)
    # ─────────────────────────────────────────
    result = await db.execute(
        select(Company).where(Company.company_code == "DEFAULT")
    )
    company = result.scalar_one_or_none()

    if not company:
        company = Company(
            company_name = "Default Company",
            company_code = "DEFAULT",
            plan_type    = "enterprise",
            status       = "active",
        )
        db.add(company)
        await db.commit()
        await db.refresh(company)
        print("✅ Company created")
    else:
        print("⏭ Company already exists")

    # ─────────────────────────────────────────
    # 2. Seed Roles
    # ─────────────────────────────────────────
    # ✅ FIX 1: use role_names (not role) to avoid variable conflict
    role_names = ["superuser", "admin", "manager", "staff"]

    for role_name in role_names:        # ✅ iterates role_names not role
        result = await db.execute(
            select(Role).where(
                Role.role_name == role_name,
                Role.company_id == company.company_id,
            )
        )
        existing_role = result.scalar_one_or_none()  # ✅ different variable name

        if not existing_role:
            db.add(Role(
                company_id = company.company_id,  # ✅ FIX 2: company_id required
                role_name  = role_name,
            ))

    await db.commit()
    print("✅ Roles seeded")

    # ─────────────────────────────────────────
    # 3. Seed Department
    # ─────────────────────────────────────────
    result = await db.execute(
        select(Department).where(
            Department.department_name == "IT",
            Department.company_id == company.company_id,
        )
    )
    dept = result.scalar_one_or_none()

    if not dept:
        dept = Department(
            company_id      = company.company_id,  # ✅ company_id required
            department_name = "IT",
        )
        db.add(dept)
        await db.commit()
        await db.refresh(dept)
        print("✅ Department created")

    # ─────────────────────────────────────────
    # 4. Seed Superuser
    # ─────────────────────────────────────────
    result = await db.execute(
        select(User).where(User.username == "admin")
    )
    admin = result.scalar_one_or_none()

    if not admin:
        # get superuser role
        result = await db.execute(
            select(Role).where(
                Role.role_name  == "superuser",
                Role.company_id == company.company_id,
            )
        )
        superuser_role = result.scalar_one()

        admin_user = User(
            company_id    = company.company_id,   # ✅ company_id required
            username      = "admin",
            password_hash = hash_password("admin123"),
            full_name     = "System Admin",
            department_id = dept.department_id,
            role_id       = superuser_role.role_id,
            status        = "active",
        )
        db.add(admin_user)
        await db.commit()
        print("✅ Superuser created: username=admin / password=admin123")
    else:
        print("⏭ Superuser already exists")