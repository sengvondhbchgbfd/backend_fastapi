from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.schema import (
    SystemSettingCreate,
    SystemSettingUpdate,
    SystemSettingResponse,
    BulkUpdateRequest,
    BulkCreateRequest,       
)
from app.services.system_setting_service import SystemSettingService
from app.dependencies import get_db
from app.utils.auth import require_admin

system_setting_router = APIRouter(
    prefix="/system-settings",
    tags=["System Settings"],
)


def get_service(db: AsyncSession = Depends(get_db)) -> SystemSettingService:
    return SystemSettingService(db)


# ===========================================================================
# GET ALL
# ===========================================================================

@system_setting_router.get(
    "/",
    response_model=list[SystemSettingResponse],
    summary="[Admin] Get all settings",
)
async def get_all_settings(
    current_user: dict = Depends(require_admin),
    service:      SystemSettingService = Depends(get_service),
):
    return await service.get_all(company_id=current_user["company_id"])


# ===========================================================================
# ✅ STATIC ROUTES FIRST — before any {param} routes
# ===========================================================================

@system_setting_router.get(
    "/key/{key}",
    response_model=SystemSettingResponse,
    summary="[Admin] Get setting by key",
)
async def get_setting_by_key(
    key:          str,
    current_user: dict = Depends(require_admin),
    service:      SystemSettingService = Depends(get_service),
):
    return await service.get_by_key(key=key, company_id=current_user["company_id"])


@system_setting_router.patch(
    "/key/{key}",
    response_model=SystemSettingResponse,
    summary="[Admin] Upsert setting by key",
)
async def upsert_setting(
    key:          str,
    data:         SystemSettingUpdate,
    current_user: dict = Depends(require_admin),
    service:      SystemSettingService = Depends(get_service),
):
    return await service.upsert_by_key(
        key        = key,
        value      = data.value,
        company_id = current_user["company_id"],
    )




@system_setting_router.post(
    "/bulk",                              
    response_model=list[SystemSettingResponse],
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Bulk create settings",
)
async def bulk_create_settings(
    data:         BulkCreateRequest,
    current_user: dict = Depends(require_admin),
    service:      SystemSettingService = Depends(get_service),
):
    return await service.bulk_create(
        data       = data.settings,
        company_id = current_user["company_id"],
    )




@system_setting_router.patch(
    "/bulk",                               
    summary="[Admin] Bulk update settings",
)
async def bulk_update_settings(
    data:         BulkUpdateRequest,
    current_user: dict = Depends(require_admin),
    service:      SystemSettingService = Depends(get_service),
):
    return await service.bulk_update(
        data       = data,
        company_id = current_user["company_id"],
    )


# ===========================================================================
# ✅ DYNAMIC {setting_id} ROUTES LAST
# ===========================================================================

@system_setting_router.get(
    "/{setting_id}",
    response_model=SystemSettingResponse,
    summary="[Admin] Get setting by id",
)
async def get_setting(
    setting_id:   int,
    current_user: dict = Depends(require_admin),
    service:      SystemSettingService = Depends(get_service),
):
    return await service.get_by_id(
        setting_id = setting_id,
        company_id = current_user["company_id"],
    )


@system_setting_router.post(
    "/",
    response_model=SystemSettingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Create single setting",
)
async def create_setting(
    data:         SystemSettingCreate,
    current_user: dict = Depends(require_admin),
    service:      SystemSettingService = Depends(get_service),
):
    return await service.create(
        data       = data,
        company_id = current_user["company_id"],
    )


@system_setting_router.patch(
    "/{setting_id}",
    response_model=SystemSettingResponse,
    summary="[Admin] Update setting by id",
)
async def update_setting(
    setting_id:   int,
    data:         SystemSettingUpdate,
    current_user: dict = Depends(require_admin),
    service:      SystemSettingService = Depends(get_service),
):
    return await service.update(
        setting_id = setting_id,
        data       = data,
        company_id = current_user["company_id"],
    )


@system_setting_router.delete(
    "/{setting_id}",
    summary="[Admin] Delete setting",
)
async def delete_setting(
    setting_id:   int,
    current_user: dict = Depends(require_admin),
    service:      SystemSettingService = Depends(get_service),
):
    return await service.delete(
        setting_id = setting_id,
        company_id = current_user["company_id"],
    )