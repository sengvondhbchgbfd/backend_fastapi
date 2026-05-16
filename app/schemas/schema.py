from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum





# ============================================================================
# ENUMS
# ============================================================================

class PaymentStatusEnum(str, Enum):
    pending   = "pending"
    paid      = "paid"
    cancelled = "cancelled"


class PaymentTypeEnum(str, Enum):
    cash     = "cash"
    card     = "card"
    transfer = "transfer"


class LeaveTypeEnum(str, Enum):
    annual    = "annual"
    sick      = "sick"
    unpaid    = "unpaid"
    other     = "other"


class LeaveStatusEnum(str, Enum):
    pending   = "pending"
    approved  = "approved"
    rejected  = "rejected"
    cancelled = "cancelled"


class AdjustmentTypeEnum(str, Enum):
    bonus     = "bonus"
    deduction = "deduction"



class NotificationTypeEnum(str, Enum):
    info    = "info"
    warning = "warning"
    error   = "error"
    success = "success"


class MovementTypeEnum(str, Enum):
    stock_in   = "stock_in"
    stock_out  = "stock_out"
    adjustment = "adjustment"


class UserStatus(str, Enum):
    active   = "active"
    inactive = "inactive"

class GenderEnum(str, Enum):
    male = "male"
    female = "female"
    other = "other"

# ==========================================================
# 
# ==========================================================

class SetupRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=255)
    company_code: str = Field(..., min_length=2, max_length=50)
    username:     str = Field(..., min_length=3, max_length=100)
    password:     str = Field(..., min_length=8)
    full_name:    str = Field(..., min_length=2, max_length=150)
    timezone:     Optional[str] = "UTC"
    currency:     Optional[str] = "USD"
 
    class Config:
        json_schema_extra = {
            "example": {
                "company_name": "Acme Corp",
                "company_code": "ACME",
                "username":     "admin",
                "password":     "Admin@1234",
                "full_name":    "System Admin",
                "timezone":     "Asia/Phnom_Penh",
                "currency":     "USD"
            }
        }


      
 
 
class SetupResponse(BaseModel):
    message:      str
    company_id:   int
    company_name: str
    username:     str
    role:         str
 
 
class SetupStatusResponse(BaseModel):
    initialized: bool
    message:     str

# ============================================================================
# AUTHENTICATION SCHEMAS
# ============================================================================

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)




class LoginResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    # ✅ FIX 1: added missing token expiry fields
    access_expires_in:  int
    refresh_expires_in: int
    # staff_id:   Optional[int] = None
    # staff_name: Optional[str] = None
    # is_manager: bool = False
    user: Dict[str, Any]


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token:      str
    token_type:        str = "bearer"
    access_expires_in: int


class LogoutRequest(BaseModel):
    refresh_token: str


# ✅ FIX 2: ScanAuthRequest uses password only — staff_id comes from JWT
class ScanAuthRequest(BaseModel):
    """Staff re-enters password to get short-lived scan token"""
    password: str = Field(..., min_length=6)


class ScanTokenResponse(BaseModel):
    scan_token:      str
    expires_in_secs: int
    staff_name:      str
    message:         str


class ScanRequest(BaseModel):
    scan_token:      str
    office_qr_token: str
    latitude:        str
    longitude:       str
    company_id:      str


class ScanResponse(BaseModel):
    attendance:      "AttendanceResponse"
    distance_meters: float
    message:         str


class OfficeQRResponse(BaseModel):
    office_id:  str
    qr_token:   str
    qr_image:   str
    expires_in: str
    note:       str




class RegisterRequest(BaseModel):
    username:      str = Field(..., min_length=3, max_length=100)
    password:      str = Field(..., min_length=8)
    full_name:     str = Field(..., min_length=2, max_length=150)
    role_id:       int
    department_id: Optional[int] = None

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v):
        assert v.isalnum(), 'must be alphanumeric'
        return v


class RegisterResponse(BaseModel):
    user_id:       int
    username:      str
    full_name:     str
    role:          Optional[str]      = None
    department_id: Optional[int]      = None
    status:        str
    created_at:    Optional[datetime] = None  

    
class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    role_id: Optional[int] = None
    department_id: Optional[int] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=8)


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8)


# ============================================================================
# USER SCHEMAS
# ============================================================================
class RoleSimple(BaseModel):
    role_id: int
    role_name: str
    model_config = {"from_attributes": True}


class DepartmentSimple(BaseModel):
    department_id: int
    department_name: str

    model_config = {"from_attributes": True}



class UserBase(BaseModel):
    username:      str        = Field(..., min_length=2, max_length=100)
    full_name:     str        = Field(..., min_length=2, max_length=150)
    department_id: Optional[int]        = None
    role_id:       Optional[int]        = None
    status:        UserStatus = UserStatus.active

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    username:      Optional[str]        = Field(None, min_length=3, max_length=100)
    full_name:     Optional[str]        = Field(None, min_length=2, max_length=150)
    department_id: Optional[int]        = None
    role_id:       Optional[int]        = None
    # avatar_url: Optional[str] = None
    # avatar_public_id: Optional[str] = None
    status:        Optional[UserStatus] = None




class UserResponse(BaseModel):
    user_id: int
    username: str
    full_name: str
    status: UserStatus

    department_id: Optional[int] = None
    role_id: Optional[int] = None

    department: Optional[DepartmentSimple] = None
    role: Optional[RoleSimple] = None

    avatar_url: Optional[str] = None
    avatar_public_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }





class TokenResponse(BaseModel):
    access_token: str
    token_type:   str  = "bearer"
    is_admin:     bool


# ============================================================================
# ROLE SCHEMAS
# ============================================================================

class RoleBase(BaseModel):
    role_name: str = Field(..., min_length=2, max_length=100)



class RoleCreate(RoleBase):
    company_id: int



class RoleUpdate(BaseModel):
    role_name: Optional[str] = Field(None, min_length=2, max_length=100)


class RoleResponse(BaseModel):
    role_id: int
    role_name: str
    company_id: int

    class Config:
        from_attributes = True

# ============================================================================
# Staff
# ============================================================================


class StaffRoleCreate(BaseModel):
    role_name:   str            = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    base_salary: Optional[Decimal] = Field(None, ge=0)
    is_manager:  bool           = False


class StaffRoleUpdate(BaseModel):
    role_name:   Optional[str]     = Field(None, min_length=2, max_length=100)
    description: Optional[str]     = Field(None, max_length=500)
    base_salary: Optional[Decimal] = Field(None, ge=0)
    is_manager:  Optional[bool]    = None


class StaffRoleResponse(StaffRoleCreate):
    staff_role_id: int
    company_id: int
    created_at:    datetime

    class Config:
        from_attributes = True


# ============================================================================
# DEPARTMENT SCHEMAS
# ============================================================================

class DepartmentBase(BaseModel):
    department_name: str         = Field(..., min_length=2, max_length=100)
    manager_id:      Optional[int] = None


class DepartmentCreate(DepartmentBase):
    company_id: int



class DepartmentUpdate(BaseModel):
    department_name: Optional[str] = Field(None, min_length=2, max_length=100)
    manager_id:      Optional[int] = None


class DepartmentResponse(DepartmentBase):    
    department_id: int
    department_id: int

    class Config:
        from_attributes = True

# ============================================================================
# STAFF SCHEMAS
# ============================================================================

class StaffBase(BaseModel):
    user_id: Optional[int] = None
    company_id: int
    staff_role_id: Optional[int] = None
    name: str = Field(..., min_length=2, max_length=150)
    gender: Optional[GenderEnum] = None 
    date_of_birth: Optional[date] = None 
    address: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^\+?[0-9]{7,20}$")


class StaffCreate(StaffBase):
    pass

class StaffUpdate(StaffBase):
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    avatar_url: Optional[str] = None
    avatar_public_id: Optional[str] = None


class StaffResponse(StaffBase):
    staff_id: int
    company_id:       int
    age: Optional[int] = None 
    avatar_url: Optional[str] = None
    avatar_public_id: Optional[str] = None
    created_at: datetime
    

    class Config:
        from_attributes = True


class StaffRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=150)
    gender: Optional[GenderEnum] = None
    email: EmailStr
    phone: Optional[str] = Field(None, pattern=r"^\+?[0-9]{7,20}$")
    role_id: int
    department_id: int
    staff_role_id: Optional[int] = None
    base_salary: Optional[Decimal] = Field(None, ge=0)

# ============================================================================
# SALARY SCHEMAS
# ============================================================================

class SalaryBase(BaseModel):
    staff_id:         int
    managed_by:       Optional[int]     = None
    base_salary:      Decimal           = Field(..., ge=0)
    bonus:            Decimal           = Field(default=Decimal("0"), ge=0)
    deductions:       Decimal           = Field(default=Decimal("0"), ge=0)
    net_salary:       Optional[Decimal] = None
    pay_period_start: date
    pay_period_end:   date
    payment_status:   PaymentStatusEnum = PaymentStatusEnum.pending
    payment_date:     Optional[date]    = None

    @model_validator(mode='after')
    def validate_dates_and_salary(self):
        if self.pay_period_start and self.pay_period_end:
            if self.pay_period_start > self.pay_period_end:
                raise ValueError('pay_period_start must be before pay_period_end')
        if self.base_salary is not None:
            bonus      = self.bonus      or Decimal("0")
            deductions = self.deductions or Decimal("0")
            self.net_salary = self.base_salary + bonus - deductions
        return self


class SalaryCreate(SalaryBase):
    pass


class SalaryUpdate(BaseModel):
    base_salary:    Optional[Decimal]           = Field(None, ge=0)
    bonus:          Optional[Decimal]           = Field(None, ge=0)
    deductions:     Optional[Decimal]           = Field(None, ge=0)
    net_salary:     Optional[Decimal]           = None
    payment_status: Optional[PaymentStatusEnum] = None
    payment_date:   Optional[date]              = None


class SalaryResponse(SalaryBase):
    salary_id:  int
    created_at: datetime

    class Config:
        from_attributes = True

# ============================================================================
# SALARY ADJUSTMENT SCHEMAS
# ============================================================================

class SalaryAdjustmentBase(BaseModel):
    salary_id:       int
    adjusted_by:     Optional[int]         = None
    adjustment_type: AdjustmentTypeEnum
    amount:          Decimal               = Field(..., ge=0)
    reason:          Optional[str]         = Field(None, max_length=500)


class SalaryAdjustmentCreate(SalaryAdjustmentBase):
    pass


class SalaryAdjustmentUpdate(BaseModel):
    amount:  Optional[Decimal] = Field(None, ge=0)
    reason:  Optional[str]     = Field(None, max_length=500)


class SalaryAdjustmentResponse(SalaryAdjustmentBase):
    adjustment_id: int
    created_at:    datetime

class MarkPaidRequest(BaseModel):
    payment_date: date = Field(default_factory=date.today)
 

class SalarySummaryResponse(BaseModel):
    total_salaries:   int
    total_paid:       int
    total_pending:    int
    total_net_amount: Decimal

    class Config:
        from_attributes = True


# ============================================================================
# LEAVE REQUEST SCHEMAS
# ============================================================================

class LeaveRequestBase(BaseModel):
    leave_type:  LeaveTypeEnum
    start_date:  date
    end_date:    date
    reason:      Optional[str]            = Field(None, max_length=500)
    status:      LeaveStatusEnum          = LeaveStatusEnum.pending
    approved_by: Optional[int]            = None

    @model_validator(mode='after')
    def validate_dates(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError('start_date must be before end_date')
        return self


class LeaveRequestCreate(BaseModel):
    """Staff submits leave — no status/approved_by needed"""
    leave_type: LeaveTypeEnum
    start_date: date
    end_date:   date
    reason:     Optional[str] = Field(None, max_length=500)
    

    @model_validator(mode='after')
    def validate_dates(self):
        if self.start_date > self.end_date:
            raise ValueError('start_date must be before end_date')
        return self


class LeaveRequestUpdate(BaseModel):
    status:      Optional[LeaveStatusEnum] = None
    approved_by: Optional[int]             = None


class LeaveRequestResponse(LeaveRequestBase):
    leave_id:   int
    staff_id:   int     
    created_at: datetime

    class Config:
        from_attributes = True


class LeaveApprovalRequest(BaseModel):
    status: LeaveStatusEnum   # ✅ FIX 4: added status field — required for approval
    reason: Optional[str]     = Field(None, max_length=500)


class LeaveRequestListResponse(BaseModel):
    total: int
    skip:  int
    limit: int
    items: List[LeaveRequestResponse]


# ============================================================================
# ATTENDANCE SCHEMAS
# ============================================================================

class AttendanceBase(BaseModel):
    staff_id:       int
    date:           date
    # ✅ FIX 5: time not str — matches PostgreSQL TIME column
    check_in_time:  Optional[time] = None
    check_out_time: Optional[time] = None
    latitude:       Optional[str]  = None
    longitude:      Optional[str]  = None


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceResponse(AttendanceBase):
    attendance_id: int
    created_at:    datetime

    class Config:
        from_attributes = True


# ============================================================================
# CATEGORY SCHEMAS
# ============================================================================

class CategoryBase(BaseModel):
    category_name:  str     = Field(..., min_length=2, max_length=100)
    category_total: Decimal = Field(default=Decimal("0"), ge=0)
    image_url: Optional[str] = None
    image_public_id: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    category_name:  Optional[str]     = Field(None, min_length=2, max_length=100)
    category_total: Optional[Decimal] = Field(None, ge=0)
    image_url: Optional[str] = None
    image_public_id: Optional[str] = None


class CategoryResponse(CategoryBase):
    category_id: int

    class Config:
        from_attributes = True


# ============================================================================
# PRODUCT SCHEMAS
# ============================================================================

class ProductBase(BaseModel):
    category_id:    Optional[int]    = None
    name:           str              = Field(..., min_length=2, max_length=200)
    unit:           Optional[str]    = Field(None, max_length=50)
    length_width:   Optional[str]    = Field(None, max_length=100)
    descriptions:   Optional[str]    = Field(None, max_length=1000)
    price:          Decimal          = Field(..., ge=0)
    stock_quantity: int              = Field(default=0, ge=0)




class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    category_id:    Optional[int]     = None
    name:           Optional[str]     = Field(None, min_length=2, max_length=200)
    unit:           Optional[str]     = Field(None, max_length=50)
    price:          Optional[Decimal] = Field(None, ge=0)
    stock_quantity: Optional[int]     = Field(None, ge=0)
    descriptions:   Optional[str]     = Field(None, max_length=1000)


class ProductResponse(ProductBase):
    product_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# STOCK MOVEMENT SCHEMAS
# ============================================================================


class ProductImageBase(BaseModel):
    product_id: int
    company_id: int
    image_url: Optional[str] = None
    public_id: Optional[str] = None
    is_primary: Optional[bool] = False
    sort_order: Optional[int] = None

class ProductImageCreate(ProductImageBase):
    pass

class ProductImageUpdate(BaseModel):
    image_url: Optional[str] = None
    public_id: Optional[str] = None
    is_primary: Optional[bool] = None
    sort_order: Optional[int] = None

class ProductImageResponse(ProductImageBase):
    image_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# STOCK MOVEMENT SCHEMAS
# ============================================================================

class StockMovementBase(BaseModel):
    product_id:       int
    qty_in:           int              = Field(default=0, ge=0)
    qty_out:          int              = Field(default=0, ge=0)
    balance_quantity: Optional[int]    = None
    movement_type:    MovementTypeEnum
    date:             date
    reference_id:     Optional[int]    = None
    opening_balance:  Optional[Decimal]= None


class StockMovementCreate(StockMovementBase):
    pass


class StockMovementResponse(StockMovementBase):
    movement_id: int

    class Config:
        from_attributes = True


# ============================================================================
# SUPPLIER SCHEMAS
# ============================================================================

class SupplierBase(BaseModel):
    name:           str              = Field(..., min_length=2, max_length=200)
    company_id:     int                
    contact_person: Optional[str]    = Field(None, max_length=150)
    phone:          Optional[str]    = Field(None, max_length=20)
    email:          Optional[EmailStr] = None
    address:        Optional[str]    = Field(None, max_length=500)
    avatar_url: Optional[str] = None
    avatar_public_id: Optional[str] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name:           Optional[str]      = Field(None, min_length=2, max_length=200)
    contact_person: Optional[str]      = Field(None, max_length=150)
    phone:          Optional[str]      = Field(None, max_length=20)
    email:          Optional[EmailStr] = None
    address:        Optional[str]      = Field(None, max_length=500)


class SupplierResponse(SupplierBase):
    supplier_id: int
    created_at:  datetime


    class Config:
        from_attributes = True



# ============================================================================
# CUSTOMER SCHEMAS
# ============================================================================

class CustomerBase(BaseModel):
    name:           str              = Field(..., min_length=2, max_length=200)
    email:          Optional[EmailStr] = None
    phone:          Optional[str]    = Field(None, max_length=20)
    avatar_url: Optional[str] = None
    avatar_public_id: Optional[str] = None
    total_purchase: Decimal          = Field(default=Decimal("0"), ge=0)


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name:           Optional[str]      = Field(None, min_length=2, max_length=200)
    email:          Optional[EmailStr] = None
    phone:          Optional[str]      = Field(None, max_length=20)
    avatar_url: Optional[str] = None
    avatar_public_id: Optional[str] = None
    total_purchase: Optional[Decimal]  = Field(None, ge=0)


class CustomerResponse(CustomerBase):
    customer_id: int

    class Config:
        from_attributes = True


# ============================================================================
# INVOICE SCHEMAS
# ============================================================================

class InvoiceBase(BaseModel):
    customer_id:  Optional[int]            = None
    staff_id:     Optional[int]            = None
    total_amount: Decimal                  = Field(..., ge=0)
    discount:     Decimal                  = Field(default=Decimal("0"), ge=0)
    tax:          Decimal                  = Field(default=Decimal("0"), ge=0)
    payment_type: Optional[PaymentTypeEnum]= None


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceUpdate(BaseModel):
    total_amount: Optional[Decimal]            = Field(None, ge=0)
    discount:     Optional[Decimal]            = Field(None, ge=0)
    tax:          Optional[Decimal]            = Field(None, ge=0)
    payment_type: Optional[PaymentTypeEnum]    = None


class InvoiceResponse(InvoiceBase):
    invoice_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceItemBase(BaseModel):
    invoice_id:  int
    product_id:  int
    quantity:    int     = Field(..., gt=0)
    unit_price:  Decimal = Field(..., ge=0)
    total_price: Optional[Decimal] = None

    @model_validator(mode='after')
    def calculate_total(self):
        if self.quantity and self.unit_price:
            self.total_price = Decimal(str(self.quantity)) * self.unit_price
        return self


class InvoiceItemCreate(InvoiceItemBase):
    pass


class InvoiceItemResponse(InvoiceItemBase):
    item_id: int

    class Config:
        from_attributes = True


class InvoiceAttachmentResponse(BaseModel):
    attachment_id: int
    company_id:    int
    invoice_id:    int
    file_url:      str
    public_id:     str
    file_name:     Optional[str] = None
    file_type:     Optional[str] = None
    created_at:    datetime
 
    model_config = {"from_attributes": True}


# ============================================================================
# NOTIFICATION SCHEMAS
# ============================================================================

class NotificationBase(BaseModel):
    user_id:        Optional[int]              = None
    title:          str                        = Field(..., max_length=200)
    message:        str                        = Field(..., max_length=1000)
    type:           NotificationTypeEnum       = NotificationTypeEnum.info
    is_read:        bool                       = False
    reference_id:   Optional[int]              = None
    reference_type: Optional[str]              = Field(None, max_length=50)


class NotificationCreate(NotificationBase):
    pass

class BulkMarkReadRequest(BaseModel):
    notification_ids: list[int]

    
class NotificationSummaryResponse(BaseModel):
    total:       int
    unread:      int
    read:        int


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None


class NotificationResponse(NotificationBase):
    notification_id: int
    created_at:      datetime


    class Config:
        from_attributes = True


# ============================================================================
# CHAT SCHEMAS
# ============================================================================

# class ChatGroupBase(BaseModel):
#     group_name: str          = Field(..., min_length=2, max_length=200)
#     created_by: Optional[int] = None


# class ChatGroupCreate(ChatGroupBase):
#     pass


# class ChatGroupResponse(ChatGroupBase):
#     group_id:   int
#     created_at: datetime

#     class Config:
#         from_attributes = True


# class ChatGroupMemberBase(BaseModel):
#     group_id: int
#     # ✅ FIX 6: staff_id not user_id — matches your ChatGroupMember model
#     staff_id: int


# class ChatGroupMemberCreate(ChatGroupMemberBase):
#     pass


# class ChatGroupMemberResponse(ChatGroupMemberBase):
#     id:        int
#     joined_at: datetime

#     class Config:
#         from_attributes = True


# class ChatMessageBase(BaseModel):
#     sender_id:    int
#     receiver_id:  Optional[int] = None
#     # ✅ FIX 7: added group_id for group messages
#     group_id:     Optional[int] = None
#     message_text: str           = Field(..., max_length=5000)
#     is_read:      bool          = False


# class ChatMessageCreate(ChatMessageBase):
#     pass


# class ChatMessageResponse(ChatMessageBase):
#     message_id: int
#     timestamp:  datetime

#     class Config:
#         from_attributes = True


# ============================================================================
# AUDIT LOG SCHEMAS
# ============================================================================

class AuditLogBase(BaseModel):
    user_id:    Optional[int]            = None
    action:     str                      = Field(..., max_length=50)
    table_name: str                      = Field(..., max_length=100)
    record_id:  Optional[int]            = None
    old_value:  Optional[Dict[str, Any]] = None
    new_value:  Optional[Dict[str, Any]] = None
    ip_address: Optional[str]            = Field(None, max_length=50)


class AuditLogResponse(AuditLogBase):
    log_id:     int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SYSTEM SETTINGS SCHEMAS
# ============================================================================

class SystemSettingBase(BaseModel):
    key:         str           = Field(..., min_length=2, max_length=100)
    value:       str           = Field(..., max_length=5000)
    description: Optional[str] = Field(None, max_length=500)


class SystemSettingCreate(SystemSettingBase):
    pass


class SystemSettingUpdate(BaseModel):
    value:       Optional[str] = Field(None, max_length=5000)
    description: Optional[str] = Field(None, max_length=500)


class SystemSettingResponse(SystemSettingBase):
    setting_id: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class BulkUpdateItem(BaseModel):
    key:   str = Field(..., min_length=2, max_length=100)
    value: str = Field(..., max_length=5000)
 
 
class BulkUpdateRequest(BaseModel):
    settings: list[BulkUpdateItem]

class BulkCreateRequest(BaseModel):
    settings: list[SystemSettingCreate] 


# ============================================================================
# COMPANY SCHEMAS
# ============================================================================

class CompanyBase(BaseModel):
    company_name: str           = Field(..., min_length=2, max_length=255)
    company_code: str           = Field(..., min_length=2, max_length=50)
    email:        Optional[str] = None
    phone:        Optional[str] = Field(None, max_length=50)
    address:      Optional[str] = None
    logo_url:     Optional[str] = None
    timezone:     str           = "UTC"
    currency:     str           = "USD"
    max_users:    int           = 10


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    company_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email:        Optional[str] = None
    phone:        Optional[str] = Field(None, max_length=50)
    address:      Optional[str] = None
    logo_url:     Optional[str] = None
    timezone:     Optional[str] = None
    currency:     Optional[str] = None
    max_users:    Optional[int] = None


class CompanyResponse(CompanyBase):
    company_id: int
    plan_type:  str
    status:     str
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# ERROR & PAGINATION SCHEMAS
# ============================================================================

class ErrorResponse(BaseModel):
    status_code: int
    detail:      str
    error_type:  Optional[str] = None

    


class PaginationParams(BaseModel):
    skip:  int = Field(default=0,  ge=0)
    limit: int = Field(default=50, ge=1, le=1000)


class PaginatedResponse(BaseModel):
    total: int
    skip:  int
    limit: int
    items: List[Any]