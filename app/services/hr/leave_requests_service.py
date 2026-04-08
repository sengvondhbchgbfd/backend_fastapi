from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Optional, List
import redis.asyncio as redis

from app.models.staffs.leave_request import LeaveStatus, LeaveType
from app.repositories.hr.leave_requests_repository import LeaveRequestRepository
from app.repositories.audit.auditlog_repository import AuditLogRepository
from app.repositories.hr.staff_repository import StaffRepository
from app.repositories.communication.notifications_repository import NotificationRepository
from app.services.communication.notifications_service import NotificationService
from app.schemas.schema import (
    LeaveRequestCreate,
    LeaveRequestUpdate,
    LeaveRequestResponse,
)
from app.dependencies import get_db, get_redis_client


class LeaveRequestService:

    def __init__(
        self,
        db:           AsyncSession,        # ✅ need db for NotificationService
        leave_repo:   LeaveRequestRepository,
        audit_repo:   AuditLogRepository,
        staff_repo:   StaffRepository,     # ✅ needed to get staff + managers
        redis_client: redis.Redis,
    ):
        self.leave_repo = leave_repo
        self.audit_repo = audit_repo
        self.staff_repo = staff_repo
        # ✅ pass db — NotificationService needs it for repo
        self.notif      = NotificationService(
            db           = db,
            redis_client = redis_client,
        )

    # -----------------------------------------------------------------------
    # HELPER — notify all managers
    # -----------------------------------------------------------------------

    async def _notify_managers(
        self,
        company_id:    int,
        title:         str,
        message:       str,
        notif_type:    str = "info",
        reference_id:  int | None = None,
    ) -> None:
        managers = await self.staff_repo.get_managers(company_id)
        for manager in managers:
            await self.notif.send(
                company_id     = company_id,
                user_id        = manager.user_id,
                title          = title,
                message        = message,
                notif_type     = notif_type,
                reference_id   = reference_id,
                reference_type = "leave_request",
            )

    # =========================================================================
    # CREATE — notify staff + all managers
    # =========================================================================

    async def create(
        self,
        data:            LeaveRequestCreate,
        staff_id:        int,
        company_id:      int,
        current_user_id: int,
        client_ip:       str,
    ) -> LeaveRequestResponse:

        if data.start_date > data.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date.",
            )

        overlapping = await self.leave_repo.get_overlapping(
            staff_id   = staff_id,
            company_id = company_id,
            start_date = data.start_date,
            end_date   = data.end_date,
        )
        if overlapping:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Leave period overlaps with an existing approved or pending leave.",
            )

        leave = await self.leave_repo.create(data, staff_id, company_id)

        await self.audit_repo.log(
            user_id    = current_user_id,
            company_id = company_id,
            action     = "INSERT",
            table_name = "leave_requests",
            record_id  = leave.leave_id,
            old_value  = None,
            new_value  = {
                "staff_id":   staff_id,
                "leave_type": data.leave_type.value,
                "start_date": str(data.start_date),
                "end_date":   str(data.end_date),
                "reason":     data.reason,
                "status":     leave.status.value,
            },
            ip_address = client_ip,
        )

        # ✅ notify staff — submission confirmation
        staff = await self.staff_repo.get_by_id(staff_id, company_id)
        if staff:
            await self.notif.send(
                company_id     = company_id,
                user_id        = staff.user_id,
                title          = "Leave request submitted",
                message        = f"Your {data.leave_type.value} leave from {data.start_date} to {data.end_date} has been submitted.",
                notif_type     = "info",
                reference_id   = leave.leave_id,
                reference_type = "leave_request",
            )

            

        # ✅ notify all managers
        staff_name = staff.name if staff else f"Staff #{staff_id}"
        await self._notify_managers(
            company_id   = company_id,
            title        = "New leave request",
            message      = f"{staff_name} submitted a {data.leave_type.value} leave from {data.start_date} to {data.end_date}.",
            notif_type   = "info",
            reference_id = leave.leave_id,
        )
        return leave

    # =========================================================================
    # GET BY ID
    # =========================================================================

    async def get_by_id(
        self, leave_id: int, company_id: int
    ) -> LeaveRequestResponse:
        leave = await self.leave_repo.get_by_id(leave_id, company_id)
        if not leave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Leave request id={leave_id} not found.",
            )
        return leave

    # =========================================================================
    # GET MY LEAVES
    # =========================================================================

    async def get_my_leaves(
        self,
        staff_id:   int,
        company_id: int,
        skip:       int = 0,
        limit:      int = 50,
    ) -> List[LeaveRequestResponse]:
        return await self.leave_repo.get_by_staff_id(
            staff_id   = staff_id,
            company_id = company_id,
            skip       = skip,
            limit      = limit,
        )

    # =========================================================================
    # GET ALL
    # =========================================================================

    async def get_all(
        self,
        company_id: int,
        skip:       int                   = 0,
        limit:      int                   = 50,
        status:     Optional[LeaveStatus] = None,
        leave_type: Optional[LeaveType]   = None,
    ) -> List[LeaveRequestResponse]:
        return await self.leave_repo.get_all(
            company_id = company_id,
            skip       = skip,
            limit      = limit,
            status     = status,
            leave_type = leave_type,
        )

    # =========================================================================
    # GET PENDING
    # =========================================================================

    async def get_pending(
        self,
        company_id: int,
        skip:       int = 0,
        limit:      int = 50,
    ) -> List[LeaveRequestResponse]:
        return await self.leave_repo.get_pending(
            company_id = company_id,
            skip       = skip,
            limit      = limit,
        )

    # =========================================================================
    # APPROVE — notify staff + all managers
    # =========================================================================

    async def approve(
        self,
        leave_id:        int,
        company_id:      int,
        approved_by:     int,
        current_user_id: int,
        client_ip:       str,
    ) -> LeaveRequestResponse:
        leave = await self.get_by_id(leave_id, company_id)

        if leave.status != LeaveStatus.pending:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot approve a leave with status '{leave.status.value}'.",
            )

        updated = await self.leave_repo.approve(
            leave_id    = leave_id,
            company_id  = company_id,
            approved_by = approved_by,
        )

        await self.audit_repo.log(
            user_id    = current_user_id,
            company_id = company_id,
            action     = "UPDATE",
            table_name = "leave_requests",
            record_id  = leave_id,
            old_value  = {"status": LeaveStatus.pending.value},
            new_value  = {"status": LeaveStatus.approved.value, "approved_by": approved_by},
            ip_address = client_ip,
        )

        # ✅ notify staff — approved
        if leave.staff:
            await self.notif.send(
                company_id     = company_id,
                user_id        = leave.staff.user_id,
                title          = "Leave approved",
                message        = f"Your leave from {leave.start_date} to {leave.end_date} has been approved.",
                notif_type     = "success",
                reference_id   = leave_id,
                reference_type = "leave_request",
            )

        # ✅ notify all managers
        staff_name = leave.staff.name if leave.staff else "Staff"
        await self._notify_managers(
            company_id   = company_id,
            title        = "Leave approved",
            message      = f"{staff_name}'s leave from {leave.start_date} to {leave.end_date} was approved.",
            notif_type   = "success",
            reference_id = leave_id,
        )

        return updated

    # =========================================================================
    # REJECT — notify staff + all managers
    # =========================================================================

    async def reject(
        self,
        leave_id:        int,
        company_id:      int,
        reason:          Optional[str],
        current_user_id: int,
        client_ip:       str,
    ) -> LeaveRequestResponse:
        leave = await self.get_by_id(leave_id, company_id)

        if leave.status != LeaveStatus.pending:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot reject a leave with status '{leave.status.value}'.",
            )

        updated = await self.leave_repo.reject(
            leave_id   = leave_id,
            company_id = company_id,
            reason     = reason,
        )

        await self.audit_repo.log(
            user_id    = current_user_id,
            company_id = company_id,
            action     = "UPDATE",
            table_name = "leave_requests",
            record_id  = leave_id,
            old_value  = {"status": LeaveStatus.pending.value},
            new_value  = {"status": LeaveStatus.rejected.value, "reason": reason},
            ip_address = client_ip,
        )

        # ✅ notify staff — rejected
        if leave.staff:
            await self.notif.send(
                company_id     = company_id,
                user_id        = leave.staff.user_id,
                title          = "Leave rejected",
                message        = f"Your leave from {leave.start_date} to {leave.end_date} was rejected. Reason: {reason or 'No reason provided'}.",
                notif_type     = "warning",
                reference_id   = leave_id,
                reference_type = "leave_request",
            )

        # ✅ notify all managers
        staff_name = leave.staff.name if leave.staff else "Staff"
        await self._notify_managers(
            company_id   = company_id,
            title        = "Leave rejected",
            message      = f"{staff_name}'s leave was rejected.",
            notif_type   = "warning",
            reference_id = leave_id,
        )

        return updated

    # =========================================================================
    # CANCEL — notify staff + all managers
    # =========================================================================

    async def cancel(
        self,
        leave_id:        int,
        company_id:      int,
        staff_id:        int,
        current_user_id: int,
        client_ip:       str,
    ) -> LeaveRequestResponse:
        leave = await self.get_by_id(leave_id, company_id)

        if leave.staff_id != staff_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own leave requests.",
            )

        if leave.status not in [LeaveStatus.pending, LeaveStatus.approved]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot cancel a leave with status '{leave.status.value}'.",
            )

        updated = await self.leave_repo.cancel(leave_id, company_id)

        await self.audit_repo.log(
            user_id    = current_user_id,
            company_id = company_id,
            action     = "UPDATE",
            table_name = "leave_requests",
            record_id  = leave_id,
            old_value  = {"status": leave.status.value},
            new_value  = {"status": LeaveStatus.cancelled.value},
            ip_address = client_ip,
        )

        # ✅ notify staff — cancelled confirmation
        staff = await self.staff_repo.get_by_id(staff_id, company_id)
        if staff:
            await self.notif.send(
                company_id     = company_id,
                user_id        = staff.user_id,
                title          = "Leave cancelled",
                message        = f"Your leave from {leave.start_date} to {leave.end_date} has been cancelled.",
                notif_type     = "info",
                reference_id   = leave_id,
                reference_type = "leave_request",
            )

        # ✅ notify all managers
        staff_name = staff.name if staff else "Staff"
        await self._notify_managers(
            company_id   = company_id,
            title        = "Leave cancelled",
            message      = f"{staff_name} cancelled their leave from {leave.start_date} to {leave.end_date}.",
            notif_type   = "info",
            reference_id = leave_id,
        )

        return updated

    # =========================================================================
    # DELETE
    # =========================================================================

    async def delete(
        self,
        leave_id:        int,
        company_id:      int,
        current_user_id: int,
        client_ip:       str,
    ) -> dict:
        leave   = await self.get_by_id(leave_id, company_id)
        deleted = await self.leave_repo.delete(leave_id, company_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete leave request.",
            )

        await self.audit_repo.log(
            user_id    = current_user_id,
            company_id = company_id,
            action     = "DELETE",
            table_name = "leave_requests",
            record_id  = leave_id,
            old_value  = {"status": leave.status.value},
            new_value  = None,
            ip_address = client_ip,
        )

        return {"message": f"Leave request id={leave_id} deleted."}

    # =========================================================================
    # BALANCE + SUMMARY
    # =========================================================================

    async def get_balance(
        self,
        staff_id:      int,
        company_id:    int,
        leave_type:    LeaveType,
        total_allowed: int,
        year:          int,
    ) -> dict:
        balance = await self.leave_repo.get_leave_balance(
            staff_id      = staff_id,
            company_id    = company_id,
            leave_type    = leave_type,
            total_allowed = total_allowed,
            year          = year,
        )
        return {
            "staff_id":      staff_id,
            "leave_type":    leave_type.value,
            "year":          year,
            "total_allowed": total_allowed,
            "used":          total_allowed - balance,
            "remaining":     balance,
        }

    async def get_summary(self, company_id: int) -> dict:
        total    = await self.leave_repo.count_total(company_id)
        pending  = await self.leave_repo.count_by_status(company_id, LeaveStatus.pending)
        approved = await self.leave_repo.count_by_status(company_id, LeaveStatus.approved)
        rejected = await self.leave_repo.count_by_status(company_id, LeaveStatus.rejected)
        return {
            "total":    total,
            "pending":  pending,
            "approved": approved,
            "rejected": rejected,
        }


# =============================================================================
# FACTORY
# =============================================================================

async def get_leave_service(
    db:           AsyncSession = Depends(get_db),
    redis_client: redis.Redis  = Depends(get_redis_client),  # ✅ fixed typo redis.Redise
) -> LeaveRequestService:
    return LeaveRequestService(
        db           = db,                              # ✅ pass db
        leave_repo   = LeaveRequestRepository(db),
        audit_repo   = AuditLogRepository(db),
        staff_repo   = StaffRepository(db),             # ✅ added
        redis_client = redis_client,
    )