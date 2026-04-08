from datetime import datetime, timedelta, time
from app.core.config import settings
from app.schemas.schema import AuditLogResponse
from app.schemas.schema import LeaveRequestResponse
from app.models.staffs import LeaveRequest 

from fastapi import Request,Response
import jwt
def _create_token(data: dict) -> str:
      payload = data.copy()
      payload["exp"] = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
      )
      payload['iat'] = datetime.utcnow()
      return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
def _serialize(log) -> AuditLogResponse:
    return AuditLogResponse(
        log_id=log.log_id,
        user_id=log.user_id,
        username=log.user.username if log.user else None,
        action=log.action,
        table_name=log.table_name,
        record_id=log.record_id,
        old_value=log.old_value,
        new_value=log.new_value,
        ip_address=log.ip_address,
        created_at=log.created_at,
    )

# =========================================================================
# HELPER METHODS
# =========================================================================

async def _to_response(
        self,
        leave_request: LeaveRequest,
    ) -> LeaveRequestResponse:
        """Convert LeaveRequest model to response DTO."""
        staff_name = (
            f"{leave_request.staff.name}"
            if leave_request.staff
            else "Unknown"
        )
        return LeaveRequestResponse(
            leave_id=leave_request.leave_id,
            staff_id=leave_request.staff_id,
            staff_name=staff_name,
            leave_type=leave_request.leave_type.value,
            start_date=leave_request.start_date,
            end_date=leave_request.end_date,
            reason=leave_request.reason,
            status=leave_request.status.value,
            approved_by=leave_request.approved_by,
            created_at=leave_request.created_at,
        )
# ===============================================================
# OPEN & CLOSE TIME
# ===============================================================
def _get_office_open_time(self) -> time:
    try:
        # reads "09:00" from settings
        open_time = getattr(settings, "OFFICE_OPEN_TIME", "09:00")
        parts     = open_time.split(":")      # "09:00" → ["09", "00"]
        return time(int(parts[0]), int(parts[1]))  # → time(9, 0)
    except Exception:
        return time(9, 0)
    # -----------------------------------------------------------------------
    # HELPER — notify all managers
    # -----------------------------------------------------------------------

# ===============================================================
#     is mobile and set_refresh token
# ===============================================================

def is_mobile(request: Request) -> bool:
    agent = request.headers.get("user-agent", "").lower()
    return any(k in agent for k in ["dart", "okhttp", "swift", "android", "ios"])







def set_refresh_cookie(response: Response, token: str):
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",  # ← False on localhost
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/auth/refresh",
    )


