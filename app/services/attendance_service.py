from datetime import date, time
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import redis.asyncio as redis

from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.staff_repository import StaffRepository
from app.repositories.notifications_repository import NotificationRepository
from app.services.notifications_service import NotificationService
from app.utils.helper import _get_office_open_time
from app.utils.qr_utils import (
    create_office_qr_token,
    decode_office_qr_token,
    generate_qr_image_base64,
    validate_gps_at_office,
)
from app.core.security import decode_scan_token
from app.core.config import settings
from app.dependencies import get_db, get_redis_client


class AttendanceService:

    def __init__(
        self,
        db:           AsyncSession,
        repo:         AttendanceRepository,
        staff_repo:   StaffRepository,
        redis_client: redis.Redis,         # ✅ for real-time notifications
    ):
        self.repo       = repo
        self.staff_repo = staff_repo
        self.notif      = NotificationService(  # ✅
            db           = db,
            redis_client = redis_client,
        )

    # -----------------------------------------------------------------------
    # Generate office QR
    # -----------------------------------------------------------------------

    async def generate_office_qr(self) -> dict:
        token    = create_office_qr_token()
        qr_image = generate_qr_image_base64(token)
        return {
            "office_id":  settings.OFFICE_ID,
            "qr_token":   token,
            "qr_image":   qr_image,
            "expires_in": "1 year",
            "note":       "Print and stick on office wall. Staff scan this QR after entering password.",
        }

    # -----------------------------------------------------------------------
    # CHECK-IN — notify staff + notify managers if late
    # -----------------------------------------------------------------------

    async def check_in(
        self,
        scan_token:      str,
        office_qr_token: str,
        latitude:        str,
        longitude:       str,
        company_id:      int,
    ) -> dict:

        # 1. Decode scan token → staff_id
        staff_id = decode_scan_token(scan_token)

        # 2. Validate office QR
        decode_office_qr_token(office_qr_token)

        # 3. Validate GPS
        distance = validate_gps_at_office(latitude, longitude)

        # 4. No duplicate check-in
        today    = date.today()
        existing = await self.repo.get_today_record(staff_id, company_id, today)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Already checked in today at {existing.check_in_time}.",
            )

        # 5. Save check-in
        record = await self.repo.create_check_in(
            staff_id   = staff_id,
            company_id = company_id,
            today      = today,
            latitude   = latitude,
            longitude  = longitude,
        )

        # 6. Fetch staff for notifications
        staff      = await self.staff_repo.get_by_id(staff_id, company_id)
        staff_name = staff.name if staff else "Staff"

        # ✅ notify staff — check-in confirmation
        if staff:
            await self.notif.send(
                company_id     = company_id,
                user_id        = staff.user_id,
                title          = "Check-in recorded",
                message        = f"You checked in at {record.check_in_time}. Have a great day!",
                notif_type     = "success",
                reference_id   = record.attendance_id,
                reference_type = "attendance",
            )

        # ✅ check if late — notify staff + all managers
        office_open = _get_office_open_time()


        if record.check_in_time > office_open and staff:

            # notify staff — late warning
            await self.notif.send(
                company_id     = company_id,
                user_id        = staff.user_id,
                title          = "Late check-in",
                message        = f"You checked in late at {record.check_in_time}. Expected by {office_open}.",
                notif_type     = "warning",
                reference_id   = record.attendance_id,
                reference_type = "attendance",
            )

            # notify all managers — late alert
            managers = await self.staff_repo.get_managers(company_id)
            for manager in managers:
                await self.notif.send(
                    company_id     = company_id,
                    user_id        = manager.user_id,
                    title          = "Late check-in alert",
                    message        = f"{staff_name} checked in late at {record.check_in_time}.",
                    notif_type     = "warning",
                    reference_id   = record.attendance_id,
                    reference_type = "attendance",
                )

        return {
            "attendance":      record,
            "staff_name":      staff_name,
            "distance_meters": round(distance, 1),
            "message":         f"Check-in successful! Welcome {staff_name}. ({distance:.0f}m from office)",
        }

    # -----------------------------------------------------------------------
    # CHECK-OUT — notify staff
    # -----------------------------------------------------------------------

    async def check_out(
        self,
        scan_token:      str,
        office_qr_token: str,
        latitude:        str,
        longitude:       str,
        company_id:      int,
    ) -> dict:

        staff_id = decode_scan_token(scan_token)
        decode_office_qr_token(office_qr_token)
        distance = validate_gps_at_office(latitude, longitude)

        today  = date.today()
        record = await self.repo.get_today_record(staff_id, company_id, today)

        if not record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have not checked in today.",
            )
        if record.check_out_time:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Already checked out today at {record.check_out_time}.",
            )

        record = await self.repo.update_check_out(
            record    = record,
            latitude  = latitude,
            longitude = longitude,
        )

        # ✅ notify staff — check-out confirmation
        staff = await self.staff_repo.get_by_id(staff_id, company_id)
        if staff:
            await self.notif.send(
                company_id     = company_id,
                user_id        = staff.user_id,
                title          = "Check-out recorded",
                message        = f"You checked out at {record.check_out_time}. See you tomorrow!",
                notif_type     = "success",
                reference_id   = record.attendance_id,
                reference_type = "attendance",
            )

        return {
            "attendance":      record,
            "distance_meters": round(distance, 1),
            "message":         f"Check-out successful! ({distance:.0f}m from office)",
        }


    # -----------------------------------------------------------------------
    # GET MY ATTENDANCE
    # -----------------------------------------------------------------------

    async def get_my_attendance(
        self,
        staff_id:   int,
        company_id: int,
        month:      Optional[int] = None,
        year:       Optional[int] = None,
    ) -> list:
        return await self.repo.get_by_staff_id(
            staff_id   = staff_id,
            company_id = company_id,
            month      = month,
            year       = year,
        )

    # -----------------------------------------------------------------------
    # GET ALL
    # -----------------------------------------------------------------------

    async def get_all_attendance(
        self,
        company_id:  int,
        filter_date: Optional[date] = None,
    ) -> list:
        return await self.repo.get_all(
            company_id  = company_id,
            filter_date = filter_date,
        )

    # -----------------------------------------------------------------------
    # GET ONE
    # -----------------------------------------------------------------------

    async def get_by_id(self, attendance_id: int, company_id: int):
        record = await self.repo.get_by_id(attendance_id, company_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attendance record id={attendance_id} not found.",
            )
        return record

    # -----------------------------------------------------------------------
    # TODAY SUMMARY
    # -----------------------------------------------------------------------

    async def get_today_summary(self, company_id: int) -> dict:
        return await self.repo.get_today_summary(
            company_id = company_id,
            today      = date.today(),
        )

    # -----------------------------------------------------------------------
    # GET BY DATE RANGE
    # -----------------------------------------------------------------------

    async def get_by_date_range(
        self,
        company_id:  int,
        start_date:  date,
        end_date:    date,
        staff_id:    Optional[int] = None,
    ) -> list:
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date must be before end_date.",
            )
        return await self.repo.get_by_date_range(
            company_id = company_id,
            start_date = start_date,
            end_date   = end_date,
            staff_id   = staff_id,
        )

    # -----------------------------------------------------------------------
    # MONTHLY STATS
    # -----------------------------------------------------------------------

    async def get_monthly_stats(
        self,
        staff_id:   int,
        company_id: int,
        month:      int,
        year:       int,
    ) -> dict:
        return await self.repo.get_monthly_stats(
            staff_id   = staff_id,
            company_id = company_id,
            month      = month,
            year       = year,
        )


# =============================================================================
# FACTORY
# =============================================================================

async def get_attendance_service(
    db:           AsyncSession = Depends(get_db),
    redis_client: redis.Redis  = Depends(get_redis_client),  # ✅ inject redis
) -> AttendanceService:
    return AttendanceService(
        db           = db,
        repo         = AttendanceRepository(db),
        staff_repo   = StaffRepository(db),
        redis_client = redis_client,
    )