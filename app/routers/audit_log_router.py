from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.schema import AuditLogResponse
from app.dependencies import get_db
from app.utils.auth import require_superuser
from app.repositories.audit.auditlog_repository import AuditLogRepository
from app.utils.helper import _serialize
from app.core.exceptions import NotFoundException


audit_router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])




# ─────────────────────────────────────────────────────────────
# GET
# ─────────────────────────────────────────────────────────────


@audit_router.get("/", response_model=list[AuditLogResponse])
async def get_all_logs(limit: int = Query(default=50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_superuser)):
    repo = AuditLogRepository(db)
    logs = await repo.get_all_audit(limit=limit)
    return [_serialize(log) for log in logs]


# ─────────────────────────────────────────────────────────────
#  GET BY USER_ID
# ─────────────────────────────────────────────────────────────


@audit_router.get("/user/{user_id}", response_model=list[AuditLogResponse])
async def get_logs_by_user(
    user_id: int,
    limit: int = Query(default=50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_superuser),
):
    repo = AuditLogRepository(db)
    logs = await repo.get_by_user(user_id=user_id, limit=limit)
    return [_serialize(log) for log in logs]

# ─────────────────────────────────────────────────────────────
# GET /audit-logs/table/{table_name}
# ─────────────────────────────────────────────────────────────

@audit_router.get("/table/{table_name}", response_model=list[AuditLogResponse],summary="Get audit logs for a specific table")
async def get_logs_by_table(
        table_name: str,
        limit: int = Query(default=50, ge=1, le=500),
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(require_superuser),
):
    repo = AuditLogRepository(db)
    logs = await repo.get_by_table(table_name=table_name, limit=limit)
    return [_serialize(log) for log in logs]
    
# ─────────────────────────────────────────────────────────────
# GET /audit-logs/action/{action}
# action = INSERT | UPDATE | DELETE
# ─────────────────────────────────────────────────────────────

@audit_router.get("/action/{action}", response_model=list[AuditLogResponse], summary="Get audit logs by type (INSERT / UPDATE / DELETE)")
async def get_logs_by_action(
    action: str,
    limit: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_superuser)
):
    repo = AuditLogRepository(db)
    logs = await repo.get_by_action(action=action, limit=limit)
    return [_serialize(log) for log in logs]


# ─────────────────────────────────────────────────────────────
# GET /audit-logs/{log_id}  — single entry
# ─────────────────────────────────────────────────────────────

@audit_router.get("/{log_id}", response_model=AuditLogResponse, summary="Get a single audit entry")
async def get_log_by_id(log_id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_superuser)):
    repo = AuditLogRepository(db)
    log = await repo.get_by_id(log_id)
    if not log:
        raise NotFoundException(status_code=404, detail=f"{log_id} not found")
    return _serialize(log)
        
