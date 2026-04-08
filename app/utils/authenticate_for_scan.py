from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.users import User
from app.models.staffs import Staff
from app.models.staffs import StaffRole
from fastapi import Depends, HTTPException, status
from app.core.security import verify_password, create_scan_token, decode_refresh_token, create_access_token, create_refresh_token
from app.core.config import settings



# ======================================================================
# 
# ======================================================================
async def login_service(
    username: str,
    password: str,
    db:       AsyncSession,
) -> dict:
    """
    Full login:
    1. Verify credentials
    2. Fetch staff + role
    3. Return access_token (60min) + refresh_token (30 days)
    """
    # 1. Verify user
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()
 
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )
 
    if not user.status:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled. Contact manager.",
        )
 
    # 2. Fetch staff + role
    staff_result = await db.execute(
        select(Staff, StaffRole)
        .outerjoin(StaffRole, Staff.staff_role_id == StaffRole.staff_role_id)
        .where(Staff.user_id == user.user_id)
    )
    row        = staff_result.first()
    staff      = row[0] if row else None
    staff_role = row[1] if row else None
 
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No staff record linked to this account.",
        )
 
    is_manager = staff_role.is_manager if staff_role else False
 
    # 3. Build both tokens
    token_data = {
        "sub":           str(user.user_id),
        "staff_id":      staff.staff_id,
        "staff_role_id": staff.staff_role_id,
        "is_manager":    is_manager,
        "role_id":       user.role_id,
    }
 
    return {
        "access_token":       create_access_token(token_data),
        "refresh_token":      create_refresh_token(staff.staff_id),
        "token_type":         "bearer",
        "access_expires_in":  settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_expires_in": settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        "staff_id":           staff.staff_id,
        "staff_name":         staff.name,
        "is_manager":         is_manager,
    }


 
#  =====================================================================
# 
# ======================================================================


async def refresh_service(
    refresh_token: str,
    db:            AsyncSession,
) -> dict:
    """"""
    staff_id = decode_refresh_token(refresh_token)
 
    staff_result = await db.execute(
        select(Staff, StaffRole)
        .outerjoin(StaffRole, Staff.staff_role_id == StaffRole.staff_role_id)
        .where(Staff.staff_id == staff_id)
    )
    row        = staff_result.first()
    staff      = row[0] if row else None
    staff_role = row[1] if row else None
 
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found.")
 
    if staff.user_id:
        user_result = await db.execute(
            select(User).where(User.user_id == staff.user_id)
        )
        user = user_result.scalar_one_or_none()
        if user and not user.status:
            raise HTTPException(
                status_code=403,
                detail={
                    "code":    "ACCOUNT_DISABLED",
                    "message": "Account disabled. Contact manager.",
                    "action":  "FULL_LOGIN",
                },
            )
    is_manager = staff_role.is_manager if staff_role else False
    token_data = {
        "sub":           str(staff.user_id),
        "staff_id":      staff.staff_id,
        "staff_role_id": staff.staff_role_id,
        "is_manager":    is_manager,
    }
 
    return {
        "access_token":      create_access_token(token_data),
        "token_type":        "bearer",
        "access_expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
 
# =================================================================
# 
# =================================================================


async def scan_auth_service(
    password:        str,
    staff_id:        int,      
    db:              AsyncSession,
) -> dict:
    """"""
    # Get staff → user → verify password
    staff_result = await db.execute(
        select(Staff).where(Staff.staff_id == staff_id)
    )
    staff = staff_result.scalar_one_or_none()


    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found.")
 

    user_result = await db.execute(
        select(User).where(User.user_id == staff.user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password.",
        )
 
    scan_token = create_scan_token(staff_id=staff_id)
 
    return {
        "scan_token":      scan_token,
        "expires_in_secs": settings.SCAN_TOKEN_EXPIRE_MINUTES * 60,
        "staff_name":      staff.name,
        "message": (
            f"Password verified. "
            f"You have {settings.SCAN_TOKEN_EXPIRE_MINUTES} minutes to scan."
        ),
    }


