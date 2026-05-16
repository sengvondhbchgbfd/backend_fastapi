from fastapi import APIRouter
from .staff_router import staff_router, staff_role_router
from .salaries_router import salary_router
from .leave_requests_router import leave_router
from .attendance_router import attendance_router

router_hr = APIRouter()
router_hr.include_router(staff_role_router)
router_hr.include_router(staff_router)
router_hr.include_router(salary_router)
router_hr.include_router(leave_router)
router_hr.include_router(attendance_router)