from fastapi import HTTPException, status, UploadFile, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import asyncio
from app.repositories.company_repository import CompanyRepository
from app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    UpdatePlanRequest,
    UpdateStatusRequest,
)
from app.utils.cloudinary_upload import delete_asset, upload_image


class CompanyService:

    def __init__(self, db: AsyncSession):
        self.repo = CompanyRepository(db)

    # -----------------------------------------------------------------------
    # GET all companies
    # -----------------------------------------------------------------------

    async def get_all(self) -> list:
        return await self.repo.get_all()

    # -----------------------------------------------------------------------
    # GET one company
    # -----------------------------------------------------------------------

    async def get_by_id(self, company_id: int):
        company = await self.repo.get_by_id(company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company id={company_id} not found.",
            )
        return company
    
    

    # -----------------------------------------------------------------------
    # CREATE company
    # -----------------------------------------------------------------------

    async def create(self, data: CompanyCreate):
        # Check company_code unique
        existing = await self.repo.get_by_code(data.company_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Company code '{data.company_code}' already exists.",
            )
        return await self.repo.create({
            "company_name": data.company_name,
            "company_code": data.company_code.upper(),
            "email":        data.email,
            "phone":        data.phone,
            "address":      data.address,
            "logo_url":     data.logo_url,
            "plan_type":    data.plan_type,
            "status":       "active",
            "timezone":     data.timezone,
            "currency":     data.currency,
            "max_users":    data.max_users,
        })

    # -----------------------------------------------------------------------
    # UPDATE company info
    # -----------------------------------------------------------------------

    async def update(
        self,
        company_id:           int,
        data:                 CompanyUpdate,
        logo:                 Optional[UploadFile] = None,
        banner:               Optional[UploadFile] = None,
        old_logo_public_id:   Optional[str]        = None,
        old_banner_public_id: Optional[str]        = None,
    ):
        company = await self.get_by_id(company_id)
        # ── Logo ──────────────────────────────────────────────────────────────
        if logo and logo.filename:
            if old_logo_public_id:
                await delete_asset(old_logo_public_id, resource_type="image")
            result               = await upload_image(logo, folder="companies/logos")
            data.logo_url        = result["secure_url"]
            data.logo_public_id  = result["public_id"]

        # ── Banner ────────────────────────────────────────────────────────────
        if banner and banner.filename:
            if old_banner_public_id:
                await delete_asset(old_banner_public_id, resource_type="image")
 
            result                = await upload_image(banner, folder="companies/banners")
            data.banner_url       = result["secure_url"]
            data.banner_public_id = result["public_id"]


        return await self.repo.update(company, data.model_dump(exclude_none=True))



    # -----------------------------------------------------------------------
    # DELETE company
    # -----------------------------------------------------------------------

    async def delete(self, company_id: int, background_tasks: BackgroundTasks) -> dict:
            company = await self.get_by_id(company_id)

            if not company:
                raise HTTPException(status_code=404, detail="Company not found")

            # delete DB first (fast)
            await self.repo.delete(company)

            # background delete
            if company.logo_public_id:
                background_tasks.add_task(delete_asset, company.logo_public_id)

            if company.banner_public_id:
                background_tasks.add_task(delete_asset, company.banner_public_id)

            return {
                "message": f"Company '{company.company_name}' deleted successfully"
            }



    # -----------------------------------------------------------------------
    # UPDATE plan (superuser only)
    # -----------------------------------------------------------------------

    async def update_plan(self, company_id: int, data: UpdatePlanRequest):
        company = await self.get_by_id(company_id)

        update_data = {"plan_type": data.plan_type}
        if data.max_users:
            update_data["max_users"] = data.max_users
        if data.expires_at:
            update_data["expires_at"] = data.expires_at

        return await self.repo.update(company, update_data)

    # -----------------------------------------------------------------------
    # UPDATE status (superuser only)
    # -----------------------------------------------------------------------

    async def update_status(self, company_id: int, data: UpdateStatusRequest, changed_by: int):
        company = await self.get_by_id(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        old_status = company.status
        #  update status
        company = await self.repo.update(company, {"status": data.status})

        #  Log the reason in history

        history = await self.repo.log_status_history(
                    company_id=company.company_id,
                    old_status=old_status,
                    new_status=data.status,
                    reason=data.reason,
                    changed_by=changed_by
                )

        

        return history
    


    
    


    

    # -----------------------------------------------------------------------
    # GET settings
    # -----------------------------------------------------------------------

    async def get_settings(self, company_id: int):
        return await self.get_by_id(company_id)
    

    

    # -----------------------------------------------------------------------
    # GET stats
    # -----------------------------------------------------------------------

    async def get_stats(self, company_id: int) -> dict:
        company = await self.get_by_id(company_id)
        stats   = await self.repo.get_stats(company_id)
        return {
            "company_id":   company.company_id,
            "company_name": company.company_name,
            **stats,
        }