from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.schemas.schema import (
    SalaryCreate,
    SalaryUpdate,
    SalaryResponse,
    SalaryAdjustmentCreate,
    SalaryAdjustmentResponse,

    SalarySummaryResponse,
    MarkPaidRequest,


)
from app.services.salaries_service import get_salary_service, SalaryService
from app.dependencies import get_db
from app.utils.auth import  require_staff, require_manager

salary_router = APIRouter(prefix="/salaries",tags=["Salaries"],)





# ===========================================================================
# STAFF — view own salary only
# ===========================================================================

@salary_router.get(
    "/my",
    response_model=list[SalaryResponse],
    summary="Staff: view my salary records",
)
async def get_my_salaries(
    current_user: dict = Depends(require_staff),
    service:      SalaryService = Depends(get_salary_service),
):
    return await service.get_my_salaries(
        staff_id   = current_user["staff_id"],
        company_id = current_user["company_id"],
    )


# ===========================================================================
# MANAGER — manage all salaries
# ===========================================================================

@salary_router.get(
    "/",
    response_model=list[SalaryResponse],
    summary="[Manager] List all salaries",
)
async def get_all_salaries(
    staff_id:     Optional[int] = Query(None, description="Filter by staff"),
    pay_status:   Optional[str] = Query(None, description="pending | paid | cancelled"),
    current_user: dict = Depends(require_manager),
    service:      SalaryService = Depends(get_salary_service),
):
    return await service.get_all(
        company_id = current_user["company_id"],
        staff_id   = staff_id,
        status     = pay_status,
    )


@salary_router.get(
    "/summary",
    response_model=SalarySummaryResponse,
    summary="[Manager] Salary summary stats",
)
async def get_summary(
    current_user: dict = Depends(require_manager),
    service:      SalaryService = Depends(get_salary_service),
):
    return await service.get_summary(
        company_id=current_user["company_id"]
    )


@salary_router.get(
    "/{salary_id}",
    response_model=SalaryResponse,
    summary="[Manager] Get salary by id",
)
async def get_salary(
    salary_id:    int,
    current_user: dict = Depends(require_manager),
    service:      SalaryService = Depends(get_salary_service),
):
    return await service.get_by_id(
        salary_id  = salary_id,
        company_id = current_user["company_id"],
    )


@salary_router.post(
    "/",
    response_model=SalaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Manager] Create salary record",
)
async def create_salary(
    data:         SalaryCreate,
    current_user: dict = Depends(require_manager),
    service:      SalaryService = Depends(get_salary_service),
):
    return await service.create(
        data       = data,
        company_id = current_user["company_id"],
    )


@salary_router.patch(
    "/{salary_id}",
    response_model=SalaryResponse,
    summary="[Manager] Update salary",
)
async def update_salary(
    salary_id:    int,
    data:         SalaryUpdate,
    current_user: dict = Depends(require_manager),
    service:      SalaryService = Depends(get_salary_service),
):
    return await service.update(
        salary_id  = salary_id,
        data       = data,
        company_id = current_user["company_id"],
    )


@salary_router.patch(
    "/{salary_id}/mark-paid",
    response_model=SalaryResponse,
    summary="[Manager] Mark salary as paid",
)
async def mark_paid(
    salary_id:    int,
    data:         MarkPaidRequest,
    current_user: dict = Depends(require_manager),
    service:      SalaryService = Depends(get_salary_service),
):
    return await service.mark_paid(
        salary_id  = salary_id,
        data       = data,
        company_id = current_user["company_id"],
    )


@salary_router.delete(
    "/{salary_id}",
    summary="[Manager] Delete salary (only if not paid)",
)
async def delete_salary(
    salary_id:    int,
    current_user: dict = Depends(require_manager),
    service:      SalaryService = Depends(get_salary_service),
):
    return await service.delete(
        salary_id  = salary_id,
        company_id = current_user["company_id"],
    )


# ===========================================================================
# ADJUSTMENTS
# ===========================================================================

@salary_router.get(
    "/{salary_id}/adjustments",
    response_model=list[SalaryAdjustmentResponse],
    summary="[Manager] Get adjustments for a salary",
)
async def get_adjustments(
    salary_id:    int,
    current_user: dict = Depends(require_manager),
    service:      SalaryService = Depends(get_salary_service),
):
    return await service.get_adjustments(
        salary_id  = salary_id,
        company_id = current_user["company_id"],
    )


@salary_router.post(
    "/adjustments",
    response_model=SalaryAdjustmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Manager] Add bonus or deduction to salary",
)
async def create_adjustment(
    data:         SalaryAdjustmentCreate,
    current_user: dict = Depends(require_manager),
    service:      SalaryService = Depends(get_salary_service),
):
    """
    Adds bonus or deduction and automatically recalculates net_salary.
    """
    return await service.create_adjustment(
        data             = data,
        company_id       = current_user["company_id"],
        manager_staff_id = int(current_user["sub"]),
    )




@salary_router.delete(
    "/adjustments/{adjustment_id}",
    summary="[Manager] Delete adjustment",
)




async def delete_adjustment(
    adjustment_id: int,
    current_user:  dict = Depends(require_manager),
    service:       SalaryService = Depends(get_salary_service),
):
    return await service.delete_adjustment(
        adjustment_id = adjustment_id,
        company_id    = current_user["company_id"],
    )