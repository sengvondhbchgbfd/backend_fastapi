from fastapi import APIRouter, Depends, status, Request, HTTPException, Query
from typing import Optional

from app.schemas.schema import (
    LeaveRequestCreate,
    LeaveRequestUpdate,
    LeaveRequestResponse,
)
from app.models.staffs.leave_request import LeaveStatus, LeaveType
from app.services.hr.leave_requests_service import LeaveRequestService, get_leave_service
from app.utils.auth import require_login, require_manager

leave_router = APIRouter(prefix="/leave-requests", tags=["Leave Requests"])


# ===========================================================================
# STAFF — own leave requests
# ===========================================================================

@leave_router.post(
    "/",
    response_model=LeaveRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Staff: submit a leave request",
)


async def create_leave(
    data:         LeaveRequestCreate,
    request:      Request,
    current_user: dict               = Depends(require_login),
    service:      LeaveRequestService = Depends(get_leave_service),
):
    # ✅ verify staff_id exists in JWT
    staff_id = current_user.get("staff_id")
    if not staff_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff accounts can submit leave requests.",
        )
    # ✅ pass company_id
    return await service.create(
        data            = data,
        staff_id        = staff_id,
        company_id      = current_user["company_id"],
        current_user_id = int(current_user["sub"]),
        client_ip       = request.client.host,
    )

@leave_router.get(
    "/my",
    response_model=list[LeaveRequestResponse],
    summary="Staff: get my leave requests",
)
async def get_my_leaves(
    skip:         int  = Query(0,  ge=0),
    limit:        int  = Query(50, ge=1, le=200),
    current_user: dict = Depends(require_login),
    service:      LeaveRequestService = Depends(get_leave_service),
):
    staff_id = current_user.get("staff_id")
    if not staff_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff accounts can view leave requests.",
        )

    # ✅ pass company_id
    return await service.get_my_leaves(
        staff_id   = staff_id,
        company_id = current_user["company_id"],
        skip       = skip,
        limit      = limit,
    )


@leave_router.post(
    "/{leave_id}/cancel",
    response_model=LeaveRequestResponse,
    summary="Staff: cancel my leave request",
)
async def cancel_leave(
    leave_id:     int,
    request:      Request,
    current_user: dict               = Depends(require_login),
    service:      LeaveRequestService = Depends(get_leave_service),
):
    staff_id = current_user.get("staff_id")
    if not staff_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff accounts can cancel leave requests.",
        )

    # ✅ pass company_id + staff_id for ownership check
    return await service.cancel(
        leave_id        = leave_id,
        company_id      = current_user["company_id"],
        staff_id        = staff_id,
        current_user_id = int(current_user["sub"]),
        client_ip       = request.client.host,
    )


# ===========================================================================
# MANAGER — manage all leave requests
# ===========================================================================

@leave_router.get(
    "/",
    response_model=list[LeaveRequestResponse],
    summary="[Manager] List all leave requests",
)
async def get_all_leaves(
    skip:         int                    = Query(0,  ge=0),
    limit:        int                    = Query(50, ge=1, le=200),
    leave_status: Optional[LeaveStatus]  = Query(None, description="pending | approved | rejected | cancelled"),
    leave_type:   Optional[LeaveType]    = Query(None, description="annual | sick | unpaid | ..."),
    current_user: dict                   = Depends(require_manager),
    service:      LeaveRequestService    = Depends(get_leave_service),
):
    # ✅ pass company_id
    return await service.get_all(
        company_id = current_user["company_id"],
        skip       = skip,
        limit      = limit,
        status     = leave_status,
        leave_type = leave_type,
    )


@leave_router.get(
    "/pending",
    response_model=list[LeaveRequestResponse],
    summary="[Manager] Get pending leave requests",
)
async def get_pending_leaves(
    skip:         int  = Query(0,  ge=0),
    limit:        int  = Query(50, ge=1, le=200),
    current_user: dict = Depends(require_manager),
    service:      LeaveRequestService = Depends(get_leave_service),
):
    # ✅ static route /pending before /{leave_id} to avoid conflict
    return await service.get_pending(
        company_id = current_user["company_id"],
        skip       = skip,
        limit      = limit,
    )


@leave_router.get(
    "/summary",
    summary="[Manager] Get leave stats summary",
)
async def get_summary(
    current_user: dict               = Depends(require_manager),
    service:      LeaveRequestService = Depends(get_leave_service),
):
    return await service.get_summary(
        company_id=current_user["company_id"]
    )


@leave_router.get(
    "/{leave_id}",
    response_model=LeaveRequestResponse,
    summary="[Manager] Get leave request by id",
)
async def get_leave_by_id(
    leave_id:     int,
    current_user: dict               = Depends(require_manager),
    # ✅ auth was commented out — always require auth
    service:      LeaveRequestService = Depends(get_leave_service),
):
    # ✅ pass company_id + correct method name
    return await service.get_by_id(
        leave_id   = leave_id,
        company_id = current_user["company_id"],
    )


@leave_router.patch(
    "/{leave_id}/approve",
    response_model=LeaveRequestResponse,
    summary="[Manager] Approve leave request",
)
async def approve_leave(
    leave_id:     int,
    request:      Request,
    current_user: dict               = Depends(require_manager),
    service:      LeaveRequestService = Depends(get_leave_service),
):
    staff_id = current_user.get("staff_id")
    if not staff_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager must have a staff record to approve leave.",
        )

    # ✅ pass company_id + approved_by staff_id
    return await service.approve(
        leave_id        = leave_id,
        company_id      = current_user["company_id"],
        approved_by     = staff_id,
        current_user_id = int(current_user["sub"]),
        client_ip       = request.client.host,
    )


@leave_router.patch(
    "/{leave_id}/reject",
    response_model=LeaveRequestResponse,
    summary="[Manager] Reject leave request",
)
async def reject_leave(
    leave_id:     int,
    request:      Request,
    data:         LeaveRequestUpdate,
    current_user: dict               = Depends(require_manager),
    service:      LeaveRequestService = Depends(get_leave_service),
):
    # ✅ pass company_id
    return await service.reject(
        leave_id        = leave_id,
        company_id      = current_user["company_id"],
        reason          = data.reason if hasattr(data, "reason") else None,
        current_user_id = int(current_user["sub"]),
        client_ip       = request.client.host,
    )


@leave_router.delete(
    "/{leave_id}",
    status_code=status.HTTP_200_OK,
    summary="[Manager] Delete leave request",
)
async def delete_leave(
    leave_id:     int,
    request:      Request,
    current_user: dict               = Depends(require_manager),
    service:      LeaveRequestService = Depends(get_leave_service),
):
    # ✅ pass company_id
    return await service.delete(
        leave_id        = leave_id,
        company_id      = current_user["company_id"],
        current_user_id = int(current_user["sub"]),
        client_ip       = request.client.host,
    )