from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.company.system_setting_repository import SystemSettingRepository
from app.schemas.schema import (
    SystemSettingCreate,
    SystemSettingUpdate,
    BulkUpdateRequest,
)

class SystemSettingService:

    def __init__(self, db: AsyncSession):
        self.repo = SystemSettingRepository(db)

    # -----------------------------------------------------------------------
    # GET all settings for a company
    # -----------------------------------------------------------------------

    async def get_all(self, company_id: int) -> list:
        return await self.repo.get_all(company_id)

    # -----------------------------------------------------------------------
    # GET one setting by id
    # -----------------------------------------------------------------------

    async def get_by_id(self, setting_id: int, company_id: int):
        setting = await self.repo.get_by_id(setting_id, company_id)
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting id={setting_id} not found.",
            )
        return setting
    
    # -----------------------------------------------------------------------
    # GET one setting by key
    # -----------------------------------------------------------------------

    async def get_by_key(self, key: str, company_id: int):
        setting = await self.repo.get_by_key(key, company_id)
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting key='{key}' not found.",
            )
        return setting

    # -----------------------------------------------------------------------
    # CREATE setting
    # -----------------------------------------------------------------------

    async def create(self, data: SystemSettingCreate, company_id: int):
        # key must be unique per company
        existing = await self.repo.get_by_key(data.key, company_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Setting key='{data.key}' already exists. Use PATCH to update.",
            )
        return await self.repo.create({
            "company_id":  company_id,
            "key":         data.key,
            "value":       data.value,
            "description": data.description,
        })
    
    # -----------------------------------------------------------------------
    # UPDATE setting by id
    # -----------------------------------------------------------------------

    async def update(
        self,
        setting_id: int,
        data:       SystemSettingUpdate,
        company_id: int,
    ):
        setting = await self.get_by_id(setting_id, company_id)
        return await self.repo.update(
            setting, data.model_dump(exclude_none=True)
        )
    
    

    # -----------------------------------------------------------------------
    # UPSERT by key — create or update in one call
    # -----------------------------------------------------------------------

    async def upsert_by_key(
        self,
        key:        str,
        value:      str,
        company_id: int,
    ):
        return await self.repo.upsert(company_id, key, value)

    # -----------------------------------------------------------------------
    # BULK UPDATE — update multiple settings at once
    # -----------------------------------------------------------------------

    # -----------------------------------------------------------------------
# BULK UPDATE — update multiple settings at once
# -----------------------------------------------------------------------

    async def bulk_update(
        self,
        data:       BulkUpdateRequest,
        company_id: int,
    ) -> dict:
        updated = []
        for item in data.settings:
            setting = await self.repo.upsert(company_id, item.key, item.value)
            updated.append(setting)

        return {
            "message": f"{len(updated)} settings updated.",
            "updated": updated,
        }



    # -----------------------------------------------------------------------
# BULK CREATE — create multiple settings at once
# -----------------------------------------------------------------------

    async def bulk_create(
        self,
        data:       list[SystemSettingCreate],
        company_id: int,
    ) -> list:
        keys = [item.key for item in data]
        if len(keys) != len(set(keys)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate keys in request.",
            )
        for item in data:
            existing = await self.repo.get_by_key(item.key, company_id)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Setting key='{item.key}' already exists. Use PATCH to update.",
                )

        return await self.repo.bulk_create(
            data       = [item.model_dump() for item in data],
            company_id = company_id,
        )
    

   
   

    # -----------------------------------------------------------------------
    # DELETE setting
    # -----------------------------------------------------------------------

    async def delete(self, setting_id: int, company_id: int) -> dict:
        setting = await self.get_by_id(setting_id, company_id)
        key     = setting.key
        await self.repo.delete(setting)
        return {"message": f"Setting '{key}' deleted successfully."}