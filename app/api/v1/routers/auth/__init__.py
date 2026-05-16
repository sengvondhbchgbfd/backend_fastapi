from fastapi import APIRouter
from .auth_router import router as auth_router
from .setup_router import setup_router          # ← fix: no alias needed
from .users_router import router, role_router, department_router

router_auth = APIRouter()
router_auth.include_router(auth_router)
router_auth.include_router(setup_router)
router_auth.include_router(role_router)
router_auth.include_router(department_router)
router_auth.include_router(router)              # users