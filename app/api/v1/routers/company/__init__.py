from fastapi import APIRouter
from .company_router import company_router

router = APIRouter()
router.include_router(company_router, prefix="/company", tags=["Company"])