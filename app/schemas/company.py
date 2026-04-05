from pydantic import BaseModel, Field, EmailStr
from typing   import Optional
from datetime import datetime
from decimal  import Decimal
from enum     import Enum


class PlanTypeEnum(str, Enum):
    free       = "free"
    pro        = "pro"
    enterprise = "enterprise"


class CompanyStatusEnum(str, Enum):
    active    = "active"
    suspended = "suspended"
    cancelled = "cancelled"


# ─────────────────────────────────────────────────────────────────────────────
# CRUD
# ─────────────────────────────────────────────────────────────────────────────

class CompanyCreate(BaseModel):
    company_name: str           = Field(..., min_length=2, max_length=255)
    company_code: str           = Field(..., min_length=2, max_length=50)
    email:        Optional[str] = None
    phone:        Optional[str] = Field(None, max_length=50)
    address:      Optional[str] = None
    logo_url:     Optional[str] = None
    plan_type:    PlanTypeEnum  = PlanTypeEnum.free
    timezone:     str           = "UTC"
    currency:     str           = "USD"
    max_users:    int           = Field(default=10, ge=1)

    class Config:
        json_schema_extra = {
            "example": {
                "company_name": "Acme Corp",
                "company_code": "ACME",
                "email":        "info@acme.com",
                "plan_type":    "pro",
                "timezone":     "Asia/Phnom_Penh",
                "currency":     "USD",
                "max_users":    50,
            }
        }


class CompanyUpdate(BaseModel):
    company_name:     Optional[str] = Field(None, min_length=2, max_length=255)
    email:            Optional[str] = None
    phone:            Optional[str] = Field(None, max_length=50)
    address:          Optional[str] = None
    timezone:         Optional[str] = None
    currency:         Optional[str] = None
    max_users:        Optional[int] = Field(None, ge=1)
    # ── image fields (set by service after Cloudinary upload) ────────────────
    logo_url:         Optional[str] = None
    logo_public_id:   Optional[str] = None
    banner_url:       Optional[str] = None
    banner_public_id: Optional[str] = None


class CompanyResponse(BaseModel):
    company_id:       int
    company_name:     str
    company_code:     str
    email:            Optional[str]
    phone:            Optional[str]
    address:          Optional[str]
    plan_type:        str
    status:           str
    timezone:         Optional[str]
    currency:         Optional[str]
    max_users:        Optional[int]
    created_at:       datetime
    expires_at:       Optional[datetime]
    # ── image fields ─────────────────────────────────────────────────────────
    logo_url:         Optional[str] = None
    logo_public_id:   Optional[str] = None
    banner_url:       Optional[str] = None
    banner_public_id: Optional[str] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# Plan / Status  (superuser only)
# ─────────────────────────────────────────────────────────────────────────────

class UpdatePlanRequest(BaseModel):
    plan_type:  PlanTypeEnum
    max_users:  Optional[int]      = Field(None, ge=1)
    expires_at: Optional[datetime] = None


class UpdateStatusRequest(BaseModel):
    status: CompanyStatusEnum
    reason: Optional[str] = None

class SystemSettingResponse(BaseModel):
    key: str
    value: Optional[str]
    description: Optional[str]
    updated_at: datetime


class CompanyStatusHistoryResponse(BaseModel):
        old_status: CompanyStatusEnum
        new_status: CompanyStatusEnum
        reason: str | None
        changed_by: int
        changed_at: datetime

        class Config:
            orm_mode = True


# ─────────────────────────────────────────────────────────────────────────────
# Settings
# ─────────────────────────────────────────────────────────────────────────────

class CompanySettingsResponse(BaseModel):
    company_id:   int
    company_name: str
    company_code: str
    plan_type:    str
    status:       str
    timezone:     Optional[str]
    currency:     Optional[str]
    max_users:    Optional[int]
    expires_at:   Optional[datetime]

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────────────────────
# Stats
# ─────────────────────────────────────────────────────────────────────────────

class CompanyStatsResponse(BaseModel):
    company_id:        int
    company_name:      str
    total_staff:       int
    total_departments: int
    total_users:       int
    active_users:      int
    total_roles:       int