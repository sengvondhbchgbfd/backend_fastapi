from sqlalchemy import and_, or_, func
from sqlalchemy.orm import DeclarativeBase
from typing import Type
from datetime import datetime, date


# ============================================================
# PATTERN 1 — Generic: has BOTH is_active + deleted_at
# ============================================================

def active_not_deleted(model):
    return and_(
        model.is_active.is_(True),
        model.deleted_at.is_(None),
    )

def not_deleted(model):
    return model.deleted_at.is_(None)

def is_active_only(model):
    return model.is_active.is_(True)


# ============================================================
# DATE RANGE — works on any model with created_at / updated_at
# ============================================================

def created_between(model, start: datetime, end: datetime):
    return and_(
        model.created_at >= start,
        model.created_at <= end,
    )

def updated_between(model, start: datetime, end: datetime):
    return and_(
        model.updated_at >= start,
        model.updated_at <= end,
    )


# ============================================================
# USER FILTERS  ✅ status=Enum | NO is_active | NO deleted_at
# ============================================================
from app.models.users.user import UserStatus

def user_active(User):
    """User is active — uses Enum status."""
    return User.status == UserStatus.active

def refresh_token_valid_for_user(RefreshToken, user_id: int):
    return and_(
        RefreshToken.user_id == user_id,
        RefreshToken.expires_at > func.now(),   # ✅ not expired
        RefreshToken.revoked.is_(False),         # ✅ not revoked
    )

def user_inactive(User):
    return User.status == UserStatus.inactive

def user_by_company(User, company_id: int):
    return and_(
        User.company_id == company_id,
        User.status == UserStatus.active,
    )

def user_by_role(User, role_id: int):
    return and_(
        User.role_id == role_id,
        User.status == UserStatus.active,
    )

def user_by_department(User, department_id: int):
    return and_(
        User.department_id == department_id,
        User.status == UserStatus.active,
    )

def user_search(User, keyword: str):
    """Search by full_name or username."""
    kw = f"%{keyword.lower()}%"
    return and_(
        or_(
            func.lower(User.full_name).like(kw),
            func.lower(User.username).like(kw),
        ),
        User.status == UserStatus.active,
    )

def user_created_between(User, start: datetime, end: datetime):
    return and_(
        User.created_at >= start,
        User.created_at <= end,
        User.status == UserStatus.active,
    )


# ============================================================
# STAFF FILTERS  (share your Staff model to confirm columns)
# ============================================================

def staff_active(Staff):
    return and_(
        Staff.is_active.is_(True),
        Staff.deleted_at.is_(None),
    )

def staff_by_department(Staff, department_id: int):
    return and_(
        Staff.department_id == department_id,
        Staff.is_active.is_(True),
        Staff.deleted_at.is_(None),
    )

def staff_by_role(Staff, role_id: int):
    return and_(
        Staff.role_id == role_id,
        Staff.is_active.is_(True),
        Staff.deleted_at.is_(None),
    )

def staff_search(Staff, keyword: str):
    kw = f"%{keyword.lower()}%"
    return and_(
        or_(
            func.lower(Staff.full_name).like(kw),
            func.lower(Staff.email).like(kw),
        ),
        Staff.is_active.is_(True),
        Staff.deleted_at.is_(None),
    )


# ============================================================
# ROLE FILTERS  (share your Role model to confirm columns)
# ============================================================

def role_active(Role):
    return and_(
        Role.is_active.is_(True),
        Role.deleted_at.is_(None),
    )

def role_search(Role, keyword: str):
    return and_(
        func.lower(Role.name).like(f"%{keyword.lower()}%"),
        Role.is_active.is_(True),
        Role.deleted_at.is_(None),
    )


# ============================================================
# DEPARTMENT FILTERS
# ============================================================

def department_active(Department):
    return and_(
        Department.is_active.is_(True),
        Department.deleted_at.is_(None),
    )

def department_search(Department, keyword: str):
    return and_(
        func.lower(Department.name).like(f"%{keyword.lower()}%"),
        Department.is_active.is_(True),
        Department.deleted_at.is_(None),
    )


# ============================================================
# REFRESH TOKEN FILTERS  (models/refresh_token)
# ============================================================

def refresh_token_valid(RefreshToken):
    return and_(
        RefreshToken.expires_at > func.now(),
        RefreshToken.revoked.is_(False),
    )

def refresh_token_by_user(RefreshToken, user_id: int):
    return and_(
        RefreshToken.user_id == user_id,
        RefreshToken.expires_at > func.now(),
        RefreshToken.revoked.is_(False),
    )


# ============================================================
# NOTIFICATION FILTERS
# ============================================================

def notification_unread(Notification, user_id: int):
    return and_(
        Notification.user_id == user_id,
        Notification.is_read.is_(False),
    )

def notification_by_type(Notification, user_id: int, notif_type: str):
    return and_(
        Notification.user_id == user_id,
        Notification.type == notif_type,
    )


# ============================================================
# CHAT FILTERS
# ============================================================

def chat_conversation(Chat, user_a_id: int, user_b_id: int):
    return or_(
        and_(Chat.sender_id == user_a_id,   Chat.receiver_id == user_b_id),
        and_(Chat.sender_id == user_b_id,   Chat.receiver_id == user_a_id),
    )

def chat_unread(Chat, receiver_id: int):
    return and_(
        Chat.receiver_id == receiver_id,
        Chat.is_read.is_(False),
    )


# ============================================================
# AUDIT LOG FILTERS
# ============================================================

def audit_by_user(AuditLog, user_id: int):
    return AuditLog.user_id == user_id

def audit_by_action(AuditLog, action: str):
    return AuditLog.action == action.upper()

def audit_date_range(AuditLog, start: datetime, end: datetime):
    return and_(
        AuditLog.created_at >= start,
        AuditLog.created_at <= end,
    )