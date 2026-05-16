from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Depends
import redis.asyncio as redis

from app.models.users.user import User, UserStatus
from app.schemas.schema import (
    DepartmentSimple, RoleCreate, RoleResponse,
    DepartmentCreate, DepartmentResponse,
    RegisterRequest, RegisterResponse, RoleSimple,
    UserUpdate, UserResponse,
)
from app.repositories.auth.user_respo import (
    RoleRepository,
    UserRepository,
    DepartmentRepository,
)
from app.repositories.audit.auditlog_repository import AuditLogRepository
from app.services.communication.notifications_service import NotificationService
from app.core.security import hash_password
from app.dependencies import get_db
from ..cache_service import CacheService
from app.db.redis import get_redis_client


class UserService:

    def __init__(
        self,
        db:           AsyncSession,
        user_repo:    UserRepository,
        audit_repo:   AuditLogRepository,
        role_repo:    RoleRepository,
        dept_repo:    DepartmentRepository,
        redis_client: redis.Redis,
    ):
        self.user_repo  = user_repo
        self.audit_repo = audit_repo
        self.role_repo  = role_repo
        self.dept_repo  = dept_repo
        self.notif      = NotificationService(
            db           = db,
            redis_client = redis_client,
        )

    # ==========================================================================
    # ROLE
    # ==========================================================================

    async def create_role(
        self, data: RoleCreate, company_id: int
    ) -> RoleResponse:
        existing = await self.role_repo.get_by_name(data.role_name, company_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role '{data.role_name}' already exists.",
            )
        return await self.role_repo.create(data.role_name, company_id)




    async def get_all_roles(self, company_id: int) -> list[RoleResponse]:
        return await self.role_repo.get_all(company_id)
    



    async def delete_role(self, role_id: int, company_id: int) -> None:
        deleted = await self.role_repo.delete(role_id, company_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Role not found.")

    # ==========================================================================
    # DEPARTMENT
    # ==========================================================================

    async def create_department(
        self, data: DepartmentCreate, company_id: int
    ) -> DepartmentResponse:
        existing = await self.dept_repo.get_by_name(
            data.department_name, company_id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Department '{data.department_name}' already exists.",
            )
        return await self.dept_repo.create(
            department_name = data.department_name,
            company_id      = company_id,
            manager_id      = data.manager_id,
        )

    async def get_all_departments(
        self, company_id: int
    ) -> list[DepartmentResponse]:
        return await self.dept_repo.get_all(company_id)


        

    async def delete_department(
        self, department_id: int, company_id: int
    ) -> None:
        deleted = await self.dept_repo.delete(department_id, company_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Department not found.")

    # ==========================================================================
    # USER CREATE
    # ==========================================================================

    async def create_user(
        self,
        data:                    RegisterRequest,
        company_id:              int,
        current_user_actions_id: int,
        client_ip:               str,
    ) -> RegisterResponse:

        # ✅ Check username unique globally
        existing = await self.user_repo.get_by_username(data.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists.",
            )
        # ✅ Verify role belongs to same company
        role = await self.role_repo.get_by_id(data.role_id, company_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role id={data.role_id} not found.",
            )

        # ✅ Verify department belongs to same company (if provided)
        if data.department_id:
            dept = await self.dept_repo.get_by_id(data.department_id, company_id)
            if not dept:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Department id={data.department_id} not found.",
                )
            
            
        # ✅ Create user — status defaults to active
        user = await self.user_repo.create(
            company_id    = company_id,
            username      = data.username,
            password_hash = hash_password(data.password),
            full_name     = data.full_name,
            department_id = data.department_id,
            role_id       = data.role_id,
            status        = UserStatus.active,
        )

        # ✅ Audit log
        await self.audit_repo.log(
            user_id    = current_user_actions_id,
            company_id = company_id,
            action     = "INSERT",
            table_name = "users",
            record_id  = user.user_id,
            old_value  = None,
            new_value  = {
                "username":      user.username,
                "full_name":     user.full_name,
                "role_id":       user.role_id,
                "department_id": user.department_id,
                "status":        user.status.value,
            },
            ip_address = client_ip,
        )

        # ✅ Notify new user — welcome message
        await self.notif.send(
            company_id     = company_id,
            user_id        = user.user_id,
            title          = "Welcome to the system!",
            message        = (
                f"Your account has been created. "
                f"Username: {user.username}. "
                f"Please login and change your password."
            ),
            notif_type     = "success",
            reference_id   = user.user_id,
            reference_type = "user",
        )
        # ✅ Reload with relationships
        user = await self.user_repo.get_by_id(user.user_id, company_id)
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            full_name=user.full_name,
            status=user.status,

            role_id=user.role_id,
            department_id=user.department_id,

            role=RoleSimple(
                role_id=user.role.role_id,
                role_name=user.role.role_name
            ) if user.role else None,

            department=DepartmentSimple(
                department_id=user.department.department_id,
                department_name=user.department.department_name
            ) if user.department else None,

            # avatar_url=user.avatar_url,
            # avatar_public_id=user.avatar_public_id,
            avatar_url=user.staff.avatar_url if user.staff else None,
            avatar_public_id=user.staff.avatar_public_id if user.staff else None,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )




    # ==========================================================================
    # GET ALL
    # ==========================================================================

    async def get_all_users(
        self, company_id: int, skip: int, limit: int
    ) -> list[User]:
        return await self.user_repo.get_all(company_id, skip, limit)

    async def count(self, company_id: int) -> int:
        return await self.user_repo.count(company_id)

    # ==========================================================================
    # GET BY ID
    # ==========================================================================

    async def get_user_by_id(self, user_id: int, company_id: int) -> User:
        user = await self.user_repo.get_by_id(user_id, company_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or inactive.",  # ✅ clearer message
            )
        return user

    # ==========================================================================
    # UPDATE
    # ==========================================================================

    async def update_user(
        self, user_id: int, data: UserUpdate, company_id: int
    ) -> User:
        user = await self.get_user_by_id(user_id, company_id)  # ✅ raises 404 if not found

        # ✅ Guard: prevent activating/deactivating via update if status not in data
        updated = await self.user_repo.update(
            user, data.model_dump(exclude_none=True)
        )
        # ✅ Notify user — account updated
        await self.notif.send(
            company_id     = company_id,
            user_id        = user_id,
            title          = "Account updated",
            message        = "Your account information has been updated.",
            notif_type     = "info",
            reference_id   = user_id,
            reference_type = "user",
        )
        return updated
    
    

    # ==========================================================================
    # DEACTIVATE  ✅ soft-disable instead of hard delete
    # ==========================================================================

    async def deactivate_user(
        self, user_id: int, company_id: int
    ) -> None:
        """
        Sets status = inactive instead of deleting the row.
        Use this instead of delete_user() for safe soft-disable.
        """
        user = await self.get_user_by_id(user_id, company_id)
        await self.user_repo.update(user, {"status": UserStatus.inactive})

    # ==========================================================================
    # DELETE  (hard delete — use deactivate_user for soft disable)
    # ==========================================================================

    async def delete_user(self, user_id: int, company_id: int) -> None:
        deleted = await self.user_repo.delete(user_id, company_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )


# ===========================================================================
# FACTORY
# ===========================================================================


async def get_user_service(
    db:           AsyncSession = Depends(get_db),
    redis_client: CacheService  = Depends(get_redis_client),
) -> UserService:
    return UserService(
        db           = db,
        user_repo    = UserRepository(db),
        audit_repo   = AuditLogRepository(db),
        role_repo    = RoleRepository(db),
        dept_repo    = DepartmentRepository(db),
        redis_client = redis_client,
    )