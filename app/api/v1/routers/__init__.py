from fastapi import APIRouter
from .auth import router_auth
from .hr import router_hr
from .inventory import router_inventory
from .communication import router_communication
from .company import company_router

api_router = APIRouter()
api_router.include_router(router_auth)
api_router.include_router(router_hr)
api_router.include_router(router_inventory)
api_router.include_router(router_communication)
api_router.include_router(company_router)