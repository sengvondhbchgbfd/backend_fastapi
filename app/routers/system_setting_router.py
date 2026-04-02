from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.schema import (
    SystemSettingCreate,
    SystemSettingUpdate,
    SystemSettingResponse,
    BulkUpdateRequest,
)
from app.services.system_setting_service import SystemSettingService
from app.dependencies import get_db
from app.utils.auth import require_admin

system_setting_router = APIRouter(
    prefix="/system-settings",
    tags=["System Settings"],
)


def get_service(
    db: AsyncSession = Depends(get_db),
) -> SystemSettingService:
    return SystemSettingService(db)


# ===========================================================================
# All endpoints require admin or superuser
# company_id always comes from JWT — staff only see their own company settings
# ===========================================================================

@system_setting_router.get(
    "/",
    response_model=list[SystemSettingResponse],
    summary="[Admin] Get all settings for current company",
)
async def get_all_settings(
    current_user: dict = Depends(require_admin),
    service:      SystemSettingService = Depends(get_service),
):
    """Returns all settings for the logged-in user's company."""
    return await service.get_all(
        company_id=current_user["company_id"]
    )


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
    """Useful for fetching a specific setting like 'office_open_time'."""
    return await service.get_by_key(
        key        = key,
        company_id = current_user["company_id"],
    )


@system_setting_router.post(
    "/",
    response_model=SystemSettingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Create new setting",
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


@system_setting_router.patch(
    "/key/{key}",
    response_model=SystemSettingResponse,
    summary="[Admin] Upsert setting by key (create or update)",
)
async def upsert_setting(
    key:          str,
    data:         SystemSettingUpdate,
    current_user: dict = Depends(require_admin),
    service:      SystemSettingService = Depends(get_service),
):
    """
    Update by key if exists, create if not.
    Useful when you don't know the setting_id.
    """
    return await service.upsert_by_key(
        key        = key,
        value      = data.value,
        company_id = current_user["company_id"],
    )


@system_setting_router.patch(
    "/bulk",
    summary="[Admin] Bulk update multiple settings at once",
)
async def bulk_update_settings(
    data:         BulkUpdateRequest,
    current_user: dict = Depends(require_admin),
    service:      SystemSettingService = Depends(get_service),
):
    """
    Update multiple settings in one request.
    Creates setting if key does not exist.

    Example body:
    {
      "settings": [
        { "key": "office_open_time",  "value": "08:00" },
        { "key": "office_close_time", "value": "17:00" },
        { "key": "office_latitude",   "value": "11.5564" },
        { "key": "office_longitude",  "value": "104.9282" },
        { "key": "office_radius_meters", "value": "100" }
      ]
    }
    """
    return await service.bulk_update(
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