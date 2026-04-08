from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.schema import SetupRequest, SetupResponse, SetupStatusResponse
from app.services.auth.setup_service import SetupService, get_setup_service

setup_router = APIRouter(prefix="/setup", tags=["Setup"])


# =============================================================================
# GET /setup/status — frontend calls this on first load
# =============================================================================

@setup_router.get(
    "/status",
    response_model=SetupStatusResponse,
    summary="Check if system is initialized",
)
async def setup_status(
    service: SetupService = Depends(get_setup_service),
):
    """
    Call this before showing login or setup page.
    - initialized: false → show setup form
    - initialized: true  → show login screen
    """
    return await service.get_status()





# =============================================================================
# POST /setup/register — one-time only, locks after first use
# =============================================================================

@setup_router.post(
    "/register",
    response_model=SetupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="First-run: create company + superuser",
)



async def setup_register(
    data:    SetupRequest,
    service: SetupService = Depends(get_setup_service),
):
    """
    No authentication required — open only when no users exist.

    Creates in one transaction:
    - Company
    - Roles: superuser, admin, manager, staff
    - Department: Management
    - Superuser account

    Returns 403 ALREADY_INITIALIZED after first successful call.
    """
    return await service.initialize(data)