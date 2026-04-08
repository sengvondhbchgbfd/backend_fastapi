from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse
from datetime import date
from typing import Optional
import base64
import io
from app.schemas.schema import (
    ScanAuthRequest,
    ScanTokenResponse,
    ScanRequest,
    ScanResponse,
    OfficeQRResponse,
    AttendanceResponse,
)
from app.services.hr.attendance_service import AttendanceService, get_attendance_service
from app.utils.authenticate_for_scan import scan_auth_service
from app.dependencies import get_db
from app.utils.auth import require_login, require_manager
from app.core.exceptions import HTTPException




attendance_router = APIRouter(prefix="/attendance", tags=["Attendance"])



# ===========================================================================
# STEP 1 — Re-enter password → get scan_token (15 min)
# Requires valid access_token (require_login)
# ===========================================================================



@attendance_router.post(
    "/scan/authenticate",
    response_model=ScanTokenResponse,
    summary="Step 1: Re-enter password to get scan token (15 min)",
)
async def scan_authenticate(
    data:         ScanAuthRequest,
    current_user: dict         = Depends(require_login),
    db:           AsyncSession = Depends(get_db),
):
    """
    Staff re-enters password to get a 15-minute scan token. 
    scan_token is then used for check-in/check-out.
    staff_id comes from JWT — not from request body.
    """


    staff_id = current_user.get("staff_id")
    if not staff_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff accounts can authenticate for scanning.",
        )

    return await scan_auth_service(
        password = data.password,
        staff_id = staff_id,
        db       = db,
    )





# ===========================================================================
# STEP 2 — Scan office QR to check in
# No JWT needed — scan_token carries identity
# ===========================================================================
@attendance_router.post(
    "/scan/check-in",
    response_model=ScanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Step 2: Scan office QR to check in",
)
async def scan_check_in(
    data:    ScanRequest,
    service: AttendanceService = Depends(get_attendance_service),
):
    """
    No JWT required — scan_token carries staff identity.
    Validates: scan_token + office_qr_token + GPS location.
    """
    return await service.check_in(
        scan_token      = data.scan_token,
        office_qr_token = data.office_qr_token,
        latitude        = data.latitude,
        longitude       = data.longitude,
        company_id      = data.company_id,   
    )


@attendance_router.post(
    "/scan/check-out",
    response_model=ScanResponse,
    summary="Step 2: Scan office QR to check out",
)
async def scan_check_out(
    data:    ScanRequest,
    service: AttendanceService = Depends(get_attendance_service),
):
    """
    Same validations as check-in.
    scan_token must still be valid (not expired).
    """
    return await service.check_out(
        scan_token      = data.scan_token,
        office_qr_token = data.office_qr_token,
        latitude        = data.latitude,
        longitude       = data.longitude,
        company_id      = data.company_id,   
    )


# ===========================================================================
# OFFICE QR — manager generates once, prints on wall
# ===========================================================================

@attendance_router.get(
    "/office-qr",
    response_model=OfficeQRResponse,
    summary="[Manager] Get office QR token + base64 image",
)
async def get_office_qr(
    current_user: dict             = Depends(require_manager),
    service:      AttendanceService = Depends(get_attendance_service),
):
    return await service.generate_office_qr()


@attendance_router.get(
    "/office-qr/image",
    summary="[Manager] Download office QR as PNG for printing",
)
async def download_office_qr(
    current_user: dict             = Depends(require_manager),
    service:      AttendanceService = Depends(get_attendance_service),
):
    result  = await service.generate_office_qr()
    b64data = result["qr_image"]

    # ✅ handle both "data:image/png;base64,..." and raw base64
    if "," in b64data:
        b64data = b64data.split(",")[1]

    img_bytes = base64.b64decode(b64data)
    return StreamingResponse(
        io.BytesIO(img_bytes),
        media_type="image/png",
        headers={"Content-Disposition": "attachment; filename=office_qr.png"},
    )


# ===========================================================================
# ATTENDANCE RECORDS — static routes before dynamic /{id}
# ===========================================================================

@attendance_router.get(
    "/my",
    response_model=list[AttendanceResponse],
    summary="Staff: view my attendance history",
)
async def get_my_attendance(
    month:        Optional[int] = Query(None, ge=1, le=12),
    year:         Optional[int] = Query(None, ge=2000),
    current_user: dict          = Depends(require_login),
    service:      AttendanceService = Depends(get_attendance_service),
):
    staff_id = current_user.get("staff_id")
    if not staff_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff accounts can view attendance.",
        )
    # ✅ pass company_id
    return await service.get_my_attendance(
        staff_id   = staff_id,
        company_id = current_user["company_id"],
        month      = month,
        year       = year,
    )


@attendance_router.get(
    "/my/monthly-stats",
    summary="Staff: get my monthly attendance stats",
)
async def get_my_monthly_stats(
    month:        int = Query(..., ge=1, le=12),
    year:         int = Query(..., ge=2000),
    current_user: dict = Depends(require_login),
    service:      AttendanceService = Depends(get_attendance_service),
):
    staff_id = current_user.get("staff_id")
    if not staff_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff accounts can view attendance stats.",
        )
    # ✅ pass company_id
    return await service.get_monthly_stats(
        staff_id   = staff_id,
        company_id = current_user["company_id"],
        month      = month,
        year       = year,
    )


@attendance_router.get(
    "/summary/today",
    summary="[Manager] Today attendance summary",
)
async def today_summary(
    current_user: dict             = Depends(require_manager),
    service:      AttendanceService = Depends(get_attendance_service),
):
    # ✅ pass company_id
    return await service.get_today_summary(
        company_id=current_user["company_id"]
    )


@attendance_router.get(
    "/date-range",
    response_model=list[AttendanceResponse],
    summary="[Manager] Get attendance by date range",
)
async def get_by_date_range(
    start_date:   date              = Query(...),
    end_date:     date              = Query(...),
    staff_id:     Optional[int]     = Query(None, description="Filter by staff"),
    current_user: dict              = Depends(require_manager),
    service:      AttendanceService = Depends(get_attendance_service),
):
    # ✅ pass company_id
    return await service.get_by_date_range(
        company_id = current_user["company_id"],
        start_date = start_date,
        end_date   = end_date,
        staff_id   = staff_id,
    )


@attendance_router.get(
    "/",
    response_model=list[AttendanceResponse],
    summary="[Manager] All attendance records",
)
async def get_all_attendance(
    filter_date:  Optional[date] = Query(None),
    current_user: dict           = Depends(require_manager),
    service:      AttendanceService = Depends(get_attendance_service),
):
    # ✅ pass company_id
    return await service.get_all_attendance(
        company_id  = current_user["company_id"],
        filter_date = filter_date,
    )


@attendance_router.get(
    "/{attendance_id}",
    response_model=AttendanceResponse,
    summary="[Manager] Get attendance record by id",
)
async def get_attendance_by_id(
    attendance_id: int,
    current_user:  dict             = Depends(require_manager),
    service:       AttendanceService = Depends(get_attendance_service),
):
    # ✅ pass company_id + dynamic route last
    return await service.get_by_id(
        attendance_id = attendance_id,
        company_id    = current_user["company_id"],
    )