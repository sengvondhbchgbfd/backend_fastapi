from fastapi import APIRouter, Depends, status, UploadFile, File, Form, BackgroundTasks
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanySettingsResponse,
    CompanyStatsResponse,
    UpdatePlanRequest,
    UpdateStatusRequest,
    CompanyStatusHistoryResponse,
)
from app.services.company.company_service import CompanyService
from app.dependencies import get_db
from app.utils.auth import require_superuser, require_admin

company_router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)

def get_company_service(
    db: AsyncSession = Depends(get_db),
) -> CompanyService:
    return CompanyService(db)


# ===========================================================================
# SPECIFIC ROUTES FIRST (before any /{company_id} dynamic routes)
# ===========================================================================

@company_router.get(
    "/",
    response_model=list[CompanyResponse],
    summary="[Admin] List all companies",
)
async def list_companies(
    current_user: dict = Depends(require_admin),
    service:      CompanyService = Depends(get_company_service),
):
    return await service.get_all()


@company_router.post(
    "/",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Create new company",
)
async def create_company(
    data:         CompanyCreate,
    current_user: dict = Depends(require_admin),
    service:      CompanyService = Depends(get_company_service),
):
    return await service.create(data)


# ===========================================================================
# /{company_id}/sub-routes BEFORE /{company_id} itself
# ===========================================================================

@company_router.get(
    "/{company_id}/settings",
    response_model=CompanySettingsResponse,
    summary="[Admin] Get company settings",
)
async def get_settings(
    company_id:   int,
    current_user: dict = Depends(require_admin),
    service:      CompanyService = Depends(get_company_service),
):
    return await service.get_settings(company_id)




@company_router.get(
    "/{company_id}/stats",
    response_model=CompanyStatsResponse,
    summary="[Admin] Get company stats",
)
async def get_stats(
    company_id: int,
    current_user: dict = Depends(require_admin),
    service:    CompanyService = Depends(get_company_service),
):
    return await service.get_stats(company_id)







@company_router.patch(
    "/{company_id}/plan",
    response_model=CompanyResponse,
    summary="[Superuser] Update company plan",
)
async def update_plan(
    company_id:   int,
    data:         UpdatePlanRequest,
    current_user: dict = Depends(require_superuser),
    service:      CompanyService = Depends(get_company_service),
):
    return await service.update_plan(company_id, data)


@company_router.patch(
    "/{company_id}/status",
    response_model=CompanyStatusHistoryResponse,
    summary="[Superuser] Update company status (active/suspended/cancelled)",
)
async def update_status(
    company_id:   int,
    data:         UpdateStatusRequest,
    current_user: dict = Depends(require_superuser),
    service:      CompanyService = Depends(get_company_service),
):
    return await service.update_status(
        company_id=company_id,
        data=data,
        changed_by=int(current_user["sub"]),
    )


# ===========================================================================
# /{company_id} DYNAMIC ROUTES LAST
# ===========================================================================

@company_router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="[Admin] Get company by id",
)
async def get_company(
    company_id:   int,
    current_user: dict = Depends(require_admin),
    service:      CompanyService = Depends(get_company_service),
):
    return await service.get_by_id(company_id)






@company_router.patch(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="[Admin] Update company info",
)
async def update_company(
    company_id:           int,
    company_name:         Optional[str]        = Form(None),
    email:                Optional[str]        = Form(None),
    phone:                Optional[str]        = Form(None),
    timezone:             Optional[str]        = Form(None),
    currency:             Optional[str]        = Form(None),
    old_logo_public_id:   Optional[str]        = Form(None),
    old_banner_public_id: Optional[str]        = Form(None),
    logo:                 Optional[UploadFile] = File(None),
    banner:               Optional[UploadFile] = File(None),
    current_user:         dict                 = Depends(require_admin),
    service:              CompanyService       = Depends(get_company_service),
):
    data = CompanyUpdate(
        company_name=company_name,
        email=email,
        phone=phone,
        timezone=timezone,
        currency=currency,
    )
    return await service.update(
        company_id,
        data,
        logo=logo,
        banner=banner,
        old_logo_public_id=old_logo_public_id,
        old_banner_public_id=old_banner_public_id,
    )


@company_router.delete(
    "/{company_id}",
    summary="[Superuser] Delete company",
)
async def delete_company(
    company_id:       int,
    background_tasks: BackgroundTasks,
    service:          CompanyService = Depends(get_company_service),
):
    return await service.delete(company_id, background_tasks)