from fastapi import APIRouter, Depends, status,File,Form, UploadFile
from datetime import date
from typing import Optional

from app.schemas.schema import (
    StaffRoleCreate, StaffRoleUpdate, StaffRoleResponse,
    StaffCreate, StaffUpdate, StaffResponse,
)
from app.services.hr.staff_service import (
    StaffRoleService, get_staff_role_service,
    StaffService, get_staff_service,
)
from app.utils.auth import require_manager, require_login

staff_role_router = APIRouter(prefix="/staff-roles", tags=["Staff Roles"])
staff_router      = APIRouter(prefix="/staff",       tags=["Staff"])


# ===========================================================================
# STAFF ROLES
# ===========================================================================

@staff_role_router.post(
    "/",
    response_model=StaffRoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Manager] Create staff role",
)
async def create_staff_role(
    data:         StaffRoleCreate,
    current_user: dict             = Depends(require_manager),
    service:      StaffRoleService = Depends(get_staff_role_service),
):
    # ✅ correct method name + company_id from JWT
    return await service.create(data, company_id=current_user["company_id"])





@staff_role_router.get(
    "/",
    response_model=list[StaffRoleResponse],
    summary="[Manager] List all staff roles",
)
async def get_all_staff_roles(
    current_user: dict             = Depends(require_manager),
    service:      StaffRoleService = Depends(get_staff_role_service),
):
    # ✅ correct method name + company_id
    return await service.get_all(company_id=current_user["company_id"])






@staff_role_router.get(
    "/{staff_role_id}",
    response_model=StaffRoleResponse,
    summary="[Manager] Get staff role by id",
)
async def get_staff_role(
    staff_role_id: int,
    current_user:  dict             = Depends(require_manager),
    service:       StaffRoleService = Depends(get_staff_role_service),
):
    # ✅ correct method name + company_id
    return await service.get_by_id(staff_role_id, company_id=current_user["company_id"])

@staff_role_router.patch(
    "/{staff_role_id}",
    response_model=StaffRoleResponse,
    summary="[Manager] Update staff role",
)
async def update_staff_role(
    staff_role_id: int,
    data:          StaffRoleUpdate,
    current_user:  dict             = Depends(require_manager),
    service:       StaffRoleService = Depends(get_staff_role_service),
):
    return await service.update(
        staff_role_id,
        data,
        company_id=current_user["company_id"],
    )



@staff_role_router.delete(
    "/{staff_role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Manager] Delete staff role",
)
async def delete_staff_role(
    staff_role_id: int,
    current_user:  dict             = Depends(require_manager),
    # ✅ was Depends(get_db) — wrong, must be Depends(get_staff_role_service)
    service:       StaffRoleService = Depends(get_staff_role_service),
):
    # ✅ correct method name — was service.create_staff_role(staff_id)
    await service.delete(staff_role_id, company_id=current_user["company_id"])


# ===========================================================================
# STAFF
# ===========================================================================



@staff_router.post(
    "/",
    response_model=StaffResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Manager] Create staff",
)
async def create_staff(
    data:         StaffCreate,
    current_user: dict         = Depends(require_manager),
    # ✅ was missing auth
    service:      StaffService = Depends(get_staff_service),
):
    # ✅ correct method name + company_id
    return await service.create(data, company_id=current_user["company_id"])




@staff_router.get(
    "/",
    response_model=list[StaffResponse],
    summary="[Manager] List all staff",
)
async def get_all_staff(
    current_user: dict         = Depends(require_manager),
    service:      StaffService = Depends(get_staff_service),
):
    # ✅ correct method name + company_id
    return await service.get_all(company_id=current_user["company_id"])




@staff_router.get(
    "/managers",
    response_model=list[StaffResponse],
    summary="[Manager] List all managers",
)
async def get_managers(
    current_user: dict         = Depends(require_manager),
    service:      StaffService = Depends(get_staff_service),
):
    return await service.get_managers(company_id=current_user["company_id"])




@staff_router.get(
    "/role/{staff_role_id}",
    response_model=list[StaffResponse],
    summary="[Manager] Get staff by role",
)
async def get_staff_by_role(
    staff_role_id: int,
    current_user:  dict         = Depends(require_manager),
    service:       StaffService = Depends(get_staff_service),
):
    # ✅ company_id added
    return await service.get_by_role(
        staff_role_id, company_id=current_user["company_id"]
    )








@staff_router.get(
    "/user/{user_id}",
    response_model=StaffResponse,
    summary="[Manager] Get staff by user_id",
)
async def get_staff_by_user_id(
    user_id:      int,
    current_user: dict         = Depends(require_manager),
    service:      StaffService = Depends(get_staff_service),
):
    # ✅ company_id added
    return await service.get_by_user_id(
        user_id, company_id=int(current_user["company_id"])
    )






@staff_router.get(
    "/department/{department_id}",
    response_model=list[StaffResponse],
    summary="[Manager] Get staff by department",
)
async def get_staff_by_department(
    department_id: int,
    current_user:  dict         = Depends(require_manager),
    service:       StaffService = Depends(get_staff_service),
):
    return await service.get_by_department(
        department_id, company_id=current_user["company_id"]
    )








@staff_router.get(
    "/my",
    response_model=StaffResponse,
    summary="Staff: get my own profile",
)
async def get_my_profile(
    current_user: dict         = Depends(require_login),
    service:      StaffService = Depends(get_staff_service),
):
    """Staff can view their own profile using staff_id from JWT."""

    return await service.get_by_id(
        staff_id   = int(current_user["staff_id"]),
        company_id = current_user["company_id"],
    )






@staff_router.get(
    "/{staff_id}",
    response_model=StaffResponse,
    summary="[Manager] Get staff by id",
)
async def get_staff(
    staff_id:     int,
    current_user: dict         = Depends(require_manager),
    service:      StaffService = Depends(get_staff_service),
):
    return await service.get_by_id(staff_id, company_id=current_user["company_id"])





@staff_router.patch("/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: int,
    name: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    date_of_birth: Optional[date] = Form(None),
    address: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    avatar_file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(require_manager),
    service: StaffService = Depends(get_staff_service),
):
    data = StaffUpdate(
        name=name, 
        gender=gender,
        date_of_birth=date_of_birth,
        address=address, 
        email=email, 
        phone=phone,
    )

    return await service.update(
        staff_id=staff_id,
        data=data,
        company_id=current_user["company_id"],
        avatar_file=avatar_file,
    )







@staff_router.patch("/{staff_id}/avatar", response_model=StaffResponse)
async def update_avatar(
    staff_id:     int,
    avatar_file:  UploadFile  = File(...),     
    current_user: dict        = Depends(require_manager),
    service:      StaffService = Depends(get_staff_service),
):
    return await service.update_staff_avatar(
        staff_id         = staff_id,
        company_id       = current_user["company_id"],
        avatar_file      = avatar_file,
        avatar_public_id = None,  
    )




@staff_router.delete(
    "/{staff_id}",
    status_code=status.HTTP_200_OK,
    summary="[Manager] Delete staff",
)
async def delete_staff(
    staff_id:     int,
    current_user: dict         = Depends(require_manager),
    service:      StaffService = Depends(get_staff_service),
):
    # ✅ correct method name + company_id
    return await service.delete(staff_id, company_id=current_user["company_id"])