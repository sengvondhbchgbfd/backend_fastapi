from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
import redis.asyncio as redis

from app.models.users.user import UserStatus
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.dependencies import get_db, get_redis_client
from app.repositories.auth_repository import AuthRepository
from app.repositories.auditlog_repository import AuditLogRepository
from app.repositories.refresh_token_repository import RefreshTokenRepo
from app.services.notifications_service import NotificationService
from app.core.security import (
    verify_password, hash_password,
    create_access_token, create_refresh_token,
    decode_refresh_token,
)
from app.core.config import settings
from app.schemas.schema import (
    RegisterRequest, RegisterResponse,
    LoginRequest, LoginResponse,
    RefreshRequest, RefreshResponse,
)


class AuthService:

    def __init__(
        self,
        db:           AsyncSession,
        auth_repo:    AuthRepository,
        audit_repo:   AuditLogRepository,
        redis_client: redis.Redis,
        refresh_repo: RefreshTokenRepo,
    ):
        self.auth_repo  = auth_repo
        self.audit_repo = audit_repo
        self.refresh_repo =  refresh_repo
        self.notif      = NotificationService(
            db           = db,
            redis_client = redis_client,
        )

    # =========================================================================
    # REGISTER
    # =========================================================================

    async def register(
        self,
        body:            RegisterRequest,
        company_id:      int,
        current_user_id: int,
        client_ip:       str,
    ) -> RegisterResponse:

        if await self.auth_repo.exists_by_username(body.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken.",
            )

        user = await self.auth_repo.create(
            company_id    = company_id,
            username      = body.username,
            password_hash = hash_password(body.password),
            full_name     = body.full_name,
            role_id       = body.role_id,
            department_id = body.department_id,
            status        = UserStatus.active,
        )

        await self.audit_repo.log(
            user_id    = current_user_id,
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

        user = await self.auth_repo.get_by_id(user.user_id, company_id)

        return RegisterResponse(
            user_id       = user.user_id,
            username      = user.username,
            full_name     = user.full_name,
            role          = user.role.role_name if user.role else None,
            department_id = user.department_id,
            status        = user.status.value,
        )





    # =========================================================================
    # LOGIN
    # =========================================================================

    async def login(
        self,
        body:      LoginRequest,
        client_ip: str,
    ) -> dict:

        user = await self.auth_repo.get_by_username(body.username)
        if not user or not verify_password(body.password, user.password_hash):
            raise UnauthorizedException("Invalid username or password.")
        if user.status != UserStatus.active:
            raise ForbiddenException("Your account is disabled. Contact admin.")
        role_name   = user.role.role_name if user.role else None
        permissions = await self.auth_repo.load_permissions(
            user.user_id, role_name
        )


        staff = await self.auth_repo.get_staff_by_user_id(user.user_id)

        await self.audit_repo.log(
            user_id    = user.user_id,
            company_id = user.company_id,
            action     = "INSERT",
            table_name = "auth_login",
            record_id  = user.user_id,
            old_value  = None,
            new_value  = {"username": user.username, "role": role_name},
            ip_address = client_ip,
        )



        access_token  = create_access_token({
            "sub":         str(user.user_id),
            "company_id":  user.company_id,
            "role":        role_name,
            "permissions": permissions,
            "staff_id":    staff.staff_id if staff else None,
            "is_manager":  staff.staff_role.is_manager if staff and staff.staff_role else False,
        })



        refresh_token = create_refresh_token(user.user_id, user.company_id)
        await self.refresh_repo.save(
            user_id = user.user_id,
            company_id = user.company_id,
            token   = refresh_token,
        )

    
        # ✅ return raw dict — router handles cookie vs body
        return {
            "access_token":        access_token,
            "refresh_token":       create_refresh_token(user.user_id, user.company_id),
            "access_expires_in":   settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_expires_in":  settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            "token_type":          "bearer",
            "user": {
                "user_id":       user.user_id,
                "company_id":    user.company_id,
                "username":      user.username,
                "full_name":     user.full_name,
                "role":          role_name,
                "department_id": user.department_id,
                "permissions":   permissions,
                "staff_id":      staff.staff_id if staff else None,
                "status":        user.status.value,
                "is_manager":    staff.staff_role.is_manager if staff and staff.staff_role else False,
            },
        }





    # =========================================================================
    # REFRESH — ✅ fully fixed
    # =========================================================================

    async def refresh(self, refresh_token: str) -> dict:
       
       
        user_id = decode_refresh_token(refresh_token)
 
        # 2. ✅ Check token exists in DB and is not revoked
        record = await self.refresh_repo.validate(refresh_token)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code":    "REFRESH_TOKEN_INVALID",
                    "message": "Refresh token is invalid, expired, or already used.",
                    "action":  "FULL_LOGIN",
                },
            )
 
        # 3. Load user
        user = await self.auth_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
 
        if user.status != UserStatus.active:
            raise ForbiddenException("Account disabled.")
 
        # 4. Load fresh role + permissions + staff
        role_name   = user.role.role_name if user.role else None
        permissions = await self.auth_repo.load_permissions(user.user_id, role_name)
        staff       = await self.auth_repo.get_staff_by_user_id(user.user_id)
 
        # 5. Issue new tokens
        new_access_token  = create_access_token({
            "sub":         str(user.user_id),
            "company_id":  user.company_id,
            "role":        role_name,
            "permissions": permissions,
            "staff_id":    staff.staff_id if staff else None,
            "is_manager":  staff.staff_role.is_manager if staff and staff.staff_role else False,
        })
        new_refresh_token = create_refresh_token(user.user_id, user.company_id)
        # 6. ✅ Rotate — revoke old, save new
        await self.refresh_repo.rotate(
            old_token  = refresh_token,
            new_token  = new_refresh_token,
            user_id    = user.user_id,
            company_id = user.company_id,
        )

        return {
            "access_token":       new_access_token,
            "refresh_token":      new_refresh_token,
            "access_expires_in":  settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_expires_in": settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            "token_type":         "bearer",
        }
    






    # =========================================================================
    # LOGOUT
    # =========================================================================

    async def logout(self, user_id: int, company_id: int, client_ip: str) -> dict:
        # ✅ Revoke ALL refresh tokens for this user
        await self.token_repo.revoke_all(user_id)
 
        await self.audit_repo.log(
            user_id    = user_id,
            company_id = company_id,
            action     = "DELETE",
            table_name = "auth_login",
            record_id  = user_id,
            old_value  = None,
            new_value  = {"action": "logout"},
            ip_address = client_ip,
        )
        return {"message": "Logged out successfully."}

    # =========================================================================
    # GET USER BY ID
    # =========================================================================

    async def get_user_by_id(
        self, user_id: int, company_id: int
    ) -> RegisterResponse:
        user = await self.auth_repo.get_by_id(user_id, company_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return RegisterResponse(
            user_id       = user.user_id,
            username      = user.username,
            full_name     = user.full_name,
            role          = user.role.role_name if user.role else None,
            department_id = user.department_id,
            status        = user.status.value,
        )

    # =========================================================================
    # GET USER BY USERNAME
    # =========================================================================

    async def get_user_by_username(self, username: str) -> RegisterResponse:
        user = await self.auth_repo.get_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return RegisterResponse(
            user_id       = user.user_id,
            username      = user.username,
            full_name     = user.full_name,
            role          = user.role.role_name if user.role else None,
            department_id = user.department_id,
            status        = user.status.value,
        )

    # =========================================================================
    # GET ALL USERS
    # =========================================================================

    async def get_all_users(self, company_id: int) -> List[RegisterResponse]:
        users = await self.auth_repo.get_all(company_id)
        return [
            RegisterResponse(
                user_id       = u.user_id,
                username      = u.username,
                full_name     = u.full_name,
                role          = u.role.role_name if u.role else None,
                department_id = u.department_id,
                status        = u.status.value,
            )
            for u in users
        ]

    # =========================================================================
    # UPDATE USER
    # =========================================================================

    async def update_user(
        self,
        user_id:         int,
        company_id:      int,
        data:            Dict[str, Any],
        current_user_id: int,
        client_ip:       str,
    ) -> RegisterResponse:
        user = await self.auth_repo.get_by_id(user_id, company_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        old_value = {
            "full_name":     user.full_name,
            "role_id":       user.role_id,
            "department_id": user.department_id,
            "status":        user.status.value,
        }

        updated = await self.auth_repo.update(user_id, company_id, **data)

        await self.audit_repo.log(
            user_id    = current_user_id,
            company_id = company_id,
            action     = "UPDATE",
            table_name = "users",
            record_id  = user_id,
            old_value  = old_value,
            new_value  = data,
            ip_address = client_ip,
        )

        return RegisterResponse(
            user_id       = updated.user_id,
            username      = updated.username,
            full_name     = updated.full_name,
            role          = updated.role.role_name if updated.role else None,
            department_id = updated.department_id,
            status        = updated.status.value,
        )

    # =========================================================================
    # DEACTIVATE USER
    # =========================================================================

    async def deactivate_user(
        self,
        user_id:         int,
        company_id:      int,
        current_user_id: int,
        client_ip:       str,
    ) -> RegisterResponse:
        user = await self.auth_repo.get_by_id(user_id, company_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        old_value = {"status": user.status.value}
        updated   = await self.auth_repo.update(
            user_id, company_id, status=UserStatus.inactive
        )

        await self.audit_repo.log(
            user_id    = current_user_id,
            company_id = company_id,
            action     = "UPDATE",
            table_name = "users",
            record_id  = user_id,
            old_value  = old_value,
            new_value  = {"status": UserStatus.inactive.value},
            ip_address = client_ip,
        )

        await self.notif.send(
            company_id     = company_id,
            user_id        = user_id,
            title          = "Account deactivated",
            message        = (
                "Your account has been deactivated. "
                "Contact your admin for more information."
            ),
            notif_type     = "warning",
            reference_id   = user_id,
            reference_type = "user",
        )

        return RegisterResponse(
            user_id       = updated.user_id,
            username      = updated.username,
            full_name     = updated.full_name,
            role          = updated.role.role_name if updated.role else None,
            department_id = updated.department_id,
            status        = updated.status.value,
        )

    # =========================================================================
    # CHANGE PASSWORD
    # =========================================================================

    async def change_password(
        self,
        user_id:         int,
        company_id:      int,
        old_password:    str,
        new_password:    str,
        current_user_id: int,
        client_ip:       str,
    ) -> Dict[str, str]:
        user = await self.auth_repo.get_by_id(user_id, company_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if not verify_password(old_password, user.password_hash):
            raise UnauthorizedException("Invalid current password.")

        await self.auth_repo.update(
            user_id, company_id,
            password_hash=hash_password(new_password),
        )

        await self.audit_repo.log(
            user_id    = current_user_id,
            company_id = company_id,
            action     = "UPDATE",
            table_name = "users",
            record_id  = user_id,
            old_value  = {"password_hash": "***"},
            new_value  = {"password_hash": "***"},
            ip_address = client_ip,
        )

        await self.notif.send(
            company_id     = company_id,
            user_id        = user_id,
            title          = "Password changed",
            message        = (
                "Your password has been changed. "
                "If you did not do this, contact admin immediately."
            ),
            notif_type     = "success",
            reference_id   = user_id,
            reference_type = "user",
        )

        return {"message": "Password changed successfully."}

    # =========================================================================
    # RESET PASSWORD
    # =========================================================================

    async def reset_password(
        self,
        user_id:         int,
        company_id:      int,
        new_password:    str,
        current_user_id: int,
        client_ip:       str,
    ) -> Dict[str, str]:
        user = await self.auth_repo.get_by_id(user_id, company_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        await self.auth_repo.update(
            user_id, company_id,
            password_hash=hash_password(new_password),
        )

        await self.audit_repo.log(
            user_id    = current_user_id,
            company_id = company_id,
            action     = "UPDATE",
            table_name = "users",
            record_id  = user_id,
            old_value  = {"password_hash": "***"},
            new_value  = {"password_hash": "***"},
            ip_address = client_ip,
        )

        await self.notif.send(
            company_id     = company_id,
            user_id        = user_id,
            title          = "Password reset",
            message        = (
                "Your password was reset by an admin. "
                "Please login and change it immediately."
            ),
            notif_type     = "warning",
            reference_id   = user_id,
            reference_type = "user",
        )

        return {"message": "Password reset successfully."}


# =============================================================================
# FACTORY
# =============================================================================

async def get_auth_service(
    db:           AsyncSession = Depends(get_db),
    redis_client: redis.Redis  = Depends(get_redis_client),
) -> AuthService:
    return AuthService(
        db           = db,
        auth_repo    = AuthRepository(db),
        audit_repo   = AuditLogRepository(db),
        refresh_repo = RefreshTokenRepo(db),
        redis_client = redis_client,
    )