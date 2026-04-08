from fastapi import APIRouter, Depends, status, Request, Query
from app.schemas.schema import (
    UserUpdate, UserResponse,
    RoleCreate, RoleResponse,
    DepartmentCreate, DepartmentResponse,
    RegisterRequest,
    PaginatedResponse,
    ErrorResponse,
)
from app.services.auth.user_service import UserService, get_user_service
from app.utils.auth import require_admin
from app.services.cache_service import CacheService, get_cache_service

# ---------------------------------------------------------------------------
router            = APIRouter(prefix="/users",       tags=["Users"])
role_router       = APIRouter(prefix="/roles",       tags=["Roles"])
department_router = APIRouter(prefix="/departments", tags=["Departments"])


# ===========================================================================
# ROLES
# ===========================================================================

@role_router.post(
    "/",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Create role",
)
async def create_role(
    data:         RoleCreate,
    current_user: dict        = Depends(require_admin),
    service:      UserService = Depends(get_user_service),
    cache:        CacheService = Depends(get_cache_service),
):
    role = await service.create_role(data, company_id=current_user["company_id"])
    await cache.delete(f"roles:{current_user['company_id']}")
    return role





@role_router.get(
    "/",
    response_model=list[RoleResponse],
    summary="[Admin] List all roles",
)
async def get_roles(
    current_user: dict        = Depends(require_admin),
    service:      UserService = Depends(get_user_service),
    cache:        CacheService = Depends(get_cache_service),
):
    cache_key = f"roles:{current_user['company_id']}"

    cached = await cache.get(cache_key)
    if cached:
        return cached
    roles      = await service.get_all_roles(company_id=current_user["company_id"])
    roles_data = [RoleResponse.model_validate(r).model_dump() for r in roles]
    await cache.set(cache_key, roles_data, ttl=300)
    return roles_data




@role_router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] Delete role",
)
async def delete_role(
    role_id:      int,
    current_user: dict        = Depends(require_admin),
    service:      UserService = Depends(get_user_service),
    cache:        CacheService = Depends(get_cache_service),  # ✅ fix: was UserService
):
    await service.delete_role(role_id, company_id=current_user["company_id"])
    await cache.delete(f"roles:{current_user['company_id']}")


# ===========================================================================
# DEPARTMENTS
# ===========================================================================

@department_router.post(
    "/",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Create department",
)
async def create_department(
    data:         DepartmentCreate,
    current_user: dict        = Depends(require_admin),
    service:      UserService = Depends(get_user_service),
    cache:        CacheService = Depends(get_cache_service),
):
    dept = await service.create_department(data, company_id=current_user["company_id"])
    await cache.delete(f"departments:{current_user['company_id']}")
    return dept


@department_router.get(
    "/",
    response_model=list[DepartmentResponse],
    summary="[Admin] List all departments",
)
async def get_departments(
    current_user: dict        = Depends(require_admin),
    service:      UserService = Depends(get_user_service),
    cache:        CacheService = Depends(get_cache_service),
):
    cache_key = f"departments:{current_user['company_id']}"

    cached = await cache.get(cache_key)
    if cached:
        return cached

    depts      = await service.get_all_departments(company_id=current_user["company_id"])
    depts_data = [DepartmentResponse.model_validate(d).model_dump() for d in depts]
    await cache.set(cache_key, depts_data, ttl=300)
    return depts_data


@department_router.delete(
    "/{department_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] Delete department",
)
async def delete_department(
    department_id: int,
    current_user:  dict        = Depends(require_admin),
    service:       UserService = Depends(get_user_service),
    cache:         CacheService = Depends(get_cache_service),
):
    await service.delete_department(
        department_id, company_id=current_user["company_id"]
    )
    await cache.delete(f"departments:{current_user['company_id']}")


# ===========================================================================
# USERS
# ===========================================================================

@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Create user",
)
async def create_user(
    data:         RegisterRequest,
    request:      Request,
    current_user: dict        = Depends(require_admin),
    service:      UserService = Depends(get_user_service),
    cache:        CacheService = Depends(get_cache_service),
):
    user = await service.create_user(
        data                    = data,
        company_id              = current_user["company_id"],
        current_user_actions_id = int(current_user["sub"]),
        client_ip               = request.client.host,
    )
    await cache.delete_pattern(f"users:{current_user['company_id']}:*")
    return user


@router.get(
    "/",
    response_model=PaginatedResponse,
    summary="[Admin] List all users",
    responses={403: {"model": ErrorResponse}},
)
async def get_users(
    skip:         int         = Query(0, ge=0),
    limit:        int         = Query(10, ge=1, le=20),
    current_user: dict        = Depends(require_admin),
    service:      UserService = Depends(get_user_service),
    cache:        CacheService = Depends(get_cache_service),
):
    cache_key = f"users:{current_user['company_id']}:{skip}:{limit}"

    cached = await cache.get(cache_key)
    if cached:
        return cached

    company_id = current_user["company_id"]
    users  = await service.get_all_users(company_id=company_id, skip=skip, limit=limit)
    total  = await service.count(company_id)

    response = PaginatedResponse(
        total = total,
        skip  = skip,
        limit = limit,
        items = [UserResponse.model_validate(u) for u in users],
    )
    await cache.set(cache_key, response.model_dump(mode="json"), ttl=300)
    return response


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="[Admin] Get user by id",
)
async def get_user(
    user_id:      int,
    current_user: dict        = Depends(require_admin),
    service:      UserService = Depends(get_user_service),
    cache:        CacheService = Depends(get_cache_service),
):
    cache_key = f"user:{current_user['company_id']}:{user_id}"

    cached = await cache.get(cache_key)
    if cached:
        return cached

    user          = await service.get_user_by_id(user_id, company_id=current_user["company_id"])
    user_response = UserResponse.model_validate(user)
    await cache.set(cache_key, user_response.model_dump(mode="json"), ttl=300)  # ✅ fix: mode="json" for datetime
    return user_response




@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="[Admin] Update user",
)
async def update_user(
    user_id:      int,
    data:         UserUpdate,
    current_user: dict        = Depends(require_admin),
    service:      UserService = Depends(get_user_service),
    cache:        CacheService = Depends(get_cache_service),  # ✅ fix: was get_redis_client
):
    user = await service.update_user(
        user_id, data, company_id=current_user["company_id"]
    )
    await cache.delete(f"user:{current_user['company_id']}:{user_id}")
    await cache.delete_pattern(f"users:{current_user['company_id']}:*")  # ✅ fix: use delete_pattern not delete
    return user






@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] Delete user",
)


async def delete_user(
    user_id:      int,
    current_user: dict        = Depends(require_admin),
    service:      UserService = Depends(get_user_service),
    cache:        CacheService = Depends(get_cache_service),
):
    await service.delete_user(user_id, company_id=current_user["company_id"])
    await cache.delete(f"user:{current_user['company_id']}:{user_id}")
    await cache.delete_pattern(f"users:{current_user['company_id']}:*")  # ✅ fix: use delete_pattern not delete