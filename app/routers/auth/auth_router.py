from fastapi import APIRouter, Depends, status, Request, HTTPException, Cookie, Response
from typing import Optional
from app.schemas.schema import (
    LoginRequest, LoginResponse,
    RegisterRequest, RegisterResponse,
    ResetPasswordRequest, ChangePasswordRequest,
    RefreshRequest, RefreshResponse,
)
from app.utils.auth import require_superuser, require_admin, require_login
from app.services.auth.auth_service import AuthService, get_auth_service
from app.utils.helper import is_mobile, set_refresh_cookie
from app.core.rate_limit import ip_limiter



router = APIRouter(prefix="/auth", tags=["Auth"])

# =============================================================================
# REGISTER
# =============================================================================

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Superuser] Register a new user",
)
async def register(
    body:         RegisterRequest,
    request:      Request,
    current_user: dict        = Depends(require_superuser),
    service:      AuthService = Depends(get_auth_service),
):
    return await service.register(
        body            = body,
        company_id      = current_user["company_id"],
        current_user_id = int(current_user["sub"]),
        client_ip       = request.client.host,
    )


# =============================================================================
# LOGIN ✅ web → cookie, mobile → body
# =============================================================================



@router.post("/login", summary="Login — returns access + refresh token")
@ip_limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    tokens = await service.login(body=body, client_ip=request.client.host)
    mobile = is_mobile(request)
    if mobile:
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "access_expires_in": tokens["access_expires_in"],
            "refresh_expires_in": tokens["refresh_expires_in"],
            "token_type": "bearer",
            "user": tokens["user"],
        }
    else:
        set_refresh_cookie(response, tokens["refresh_token"])
        return {
            "access_token": tokens["access_token"],
            "access_expires_in": tokens["access_expires_in"],
            "token_type": "bearer",
            "user": tokens["user"],
        }
    





    
# =============================================================================
# REFRESH ✅ fully implemented
# =============================================================================

@router.post(
    "/refresh",
    summary="Refresh access token",
)
async def refresh(
    request:      Request,
    response:     Response,
    service:      AuthService = Depends(get_auth_service),
    body:         RefreshRequest = None,
    cookie_token: Optional[str] = Cookie(None, alias="refresh_token"),
):
    print("DEBUG mobile:", is_mobile(request))
    print("DEBUG cookie_token:", cookie_token)
    print("DEBUG body:", body)
    print("DEBUG headers:", dict(request.headers))
    mobile = is_mobile(request)
    refresh_token = (body.refresh_token if body else None) if mobile else cookie_token

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code":    "NO_REFRESH_TOKEN",
                "message": "Refresh token missing.",
                "action":  "FULL_LOGIN",
            }
        )
    tokens = await service.refresh(refresh_token)

    if mobile:
        # Mobile → both tokens in body
        return {
            "access_token":       tokens["access_token"],
            "refresh_token":      tokens["refresh_token"],
            "access_expires_in":  tokens["access_expires_in"],
            "refresh_expires_in": tokens["refresh_expires_in"],
            "token_type":         "bearer",
        }
    

    else:
        # Web → rotate cookie, access_token in body only
        set_refresh_cookie(response, tokens["refresh_token"])
        print("test")
        return {
            "access_token":      tokens["access_token"],
            "access_expires_in": tokens["access_expires_in"],
            "token_type":        "bearer",
            
        }
    





# =============================================================================
# LOGOUT
# =============================================================================

@router.post("/logout", summary="Logout")
async def logout(
    request:      Request,
    response:     Response,
    current_user: dict        = Depends(require_login),
    service:      AuthService = Depends(get_auth_service),
):
    result = await service.logout(
        user_id    = int(current_user["sub"]),
        company_id = current_user["company_id"],
        client_ip  = request.client.host,
    )
    # Web → clear cookie on logout
    if not is_mobile(request):
        response.delete_cookie("refresh_token", path="/auth/refresh")
    return result








# =============================================================================
# GET USER BY ID
# =============================================================================

@router.get(
    "/users/{user_id}",
    response_model=RegisterResponse,
    summary="[Admin] Get user by id",
)
async def get_user(
    user_id:      int,
    current_user: dict        = Depends(require_admin),
    service:      AuthService = Depends(get_auth_service),
):
    return await service.get_user_by_id(
        user_id    = user_id,
        company_id = current_user["company_id"],
    )


# =============================================================================
# GET USER BY USERNAME
# =============================================================================

@router.get(
    "/users/username/{username}",
    response_model=RegisterResponse,
    summary="[Admin] Get user by username",
)
async def get_user_by_username(
    username:     str,
    current_user: dict        = Depends(require_admin),
    service:      AuthService = Depends(get_auth_service),
):
    return await service.get_user_by_username(username)


# =============================================================================
# GET ALL USERS
# =============================================================================

@router.get(
    "/users",
    response_model=list[RegisterResponse],
    summary="[Admin] List all users",
)
async def get_all_users(
    current_user: dict        = Depends(require_admin),
    service:      AuthService = Depends(get_auth_service),
):
    return await service.get_all_users(company_id=current_user["company_id"])


# =============================================================================
# UPDATE USER
# =============================================================================

@router.patch(
    "/users/{user_id}",
    response_model=RegisterResponse,
    summary="[Admin] Update user",
)
async def update_user(
    user_id:      int,
    data:         dict,
    request:      Request,
    current_user: dict        = Depends(require_admin),
    service:      AuthService = Depends(get_auth_service),
):
    return await service.update_user(
        user_id         = user_id,
        company_id      = current_user["company_id"],
        data            = {k: v for k, v in data.items() if v is not None},
        current_user_id = int(current_user["sub"]),
        client_ip       = request.client.host,
    )


# =============================================================================
# DEACTIVATE USER
# =============================================================================

@router.post(
    "/users/{user_id}/deactivate",
    response_model=RegisterResponse,
    summary="[Superuser] Deactivate a user",
)
async def deactivate_user(
    user_id:      int,
    request:      Request,
    current_user: dict        = Depends(require_superuser),
    service:      AuthService = Depends(get_auth_service),
):
    return await service.deactivate_user(
        user_id         = user_id,
        company_id      = current_user["company_id"],
        current_user_id = int(current_user["sub"]),
        client_ip       = request.client.host,
    )


# =============================================================================
# ACTIVATE USER
# =============================================================================

@router.post(
    "/users/{user_id}/activate",
    response_model=RegisterResponse,
    summary="[Superuser] Activate a user",
)
async def activate_user(
    user_id:      int,
    request:      Request,
    current_user: dict        = Depends(require_superuser),
    service:      AuthService = Depends(get_auth_service),
):
    return await service.update_user(
        user_id         = user_id,
        company_id      = current_user["company_id"],
        data            = {"status": "active"},
        current_user_id = int(current_user["sub"]),
        client_ip       = request.client.host,
    )


# =============================================================================
# CHANGE PASSWORD
# =============================================================================

@router.post("/change-password", summary="Change my own password")
async def change_password(
    body:         ChangePasswordRequest,
    request:      Request,
    current_user: dict        = Depends(require_login),
    service:      AuthService = Depends(get_auth_service),
):
    return await service.change_password(
        user_id         = int(current_user["sub"]),
        company_id      = current_user["company_id"],
        old_password    = body.old_password,
        new_password    = body.new_password,
        current_user_id = int(current_user["sub"]),
        client_ip       = request.client.host,
    )


# =============================================================================
# RESET PASSWORD
# =============================================================================

@router.post("/reset-password/{user_id}", summary="[Admin] Reset user password")
async def reset_password(
    user_id:      int,
    body:         ResetPasswordRequest,
    request:      Request,
    current_user: dict        = Depends(require_admin),
    service:      AuthService = Depends(get_auth_service),
):
    return await service.reset_password(
        user_id         = user_id,
        company_id      = current_user["company_id"],
        new_password    = body.new_password,
        current_user_id = int(current_user["sub"]),
        client_ip       = request.client.host,
    )