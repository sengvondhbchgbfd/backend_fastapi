from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.auth.setup_repository import SetupRepository
from app.core.security import hash_password
from app.schemas.schema import SetupRequest
from app.dependencies import get_db


class SetupService:

    def __init__(self, db: AsyncSession):
        self.repo = SetupRepository(db) 

    # -----------------------------------------------------------------------
    # Check status
    # -----------------------------------------------------------------------

    async def is_initialized(self) -> bool:
        return (await self.repo.count_users()) > 0

    async def get_status(self) -> dict:
        initialized = await self.is_initialized()
        return {
            "initialized": initialized,
            "message":     "System ready. Please login."
                           if initialized else
                           "System not initialized. Please complete setup.",
        }

    # -----------------------------------------------------------------------
    # Initialize — runs only once
    # -----------------------------------------------------------------------



    async def initialize(self, data: SetupRequest) -> dict:
        if await self.is_initialized():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code":    "ALREADY_INITIALIZED",
                    "message": "System already initialized. This endpoint is locked.",
                },
            )      
        if await self.repo.get_company_by_code(data.company_code):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Company code '{data.company_code}' already exists.",
            )
        if await self.repo.get_user_by_username(data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{data.username}' already exists.",
            )
        company = await self.repo.create_company(
            company_name = data.company_name,
            company_code = data.company_code,
            timezone     = data.timezone or "UTC",
            currency     = data.currency or "USD",
        )
        
        roles = await self.repo.create_default_roles(company.company_id)
        dept = await self.repo.create_default_department(company.company_id)
        await self.repo.create_superuser(
            company_id    = company.company_id,
            username      = data.username,
            password_hash = hash_password(data.password),
            full_name     = data.full_name,
            role_id       = roles["superuser"].role_id,
            department_id = dept.department_id,
        )

        return {
            "message":      f"Company '{data.company_name}' registered successfully.",
            "company_id":   company.company_id,
            "company_name": company.company_name,
            "company_code": company.company_code,
            "username":     data.username,
            "role":         "superuser",
        }





# =============================================================================
# FACTORY
# =============================================================================

async def get_setup_service(
    db: AsyncSession = Depends(get_db),
) -> SetupService:
    return SetupService(db)