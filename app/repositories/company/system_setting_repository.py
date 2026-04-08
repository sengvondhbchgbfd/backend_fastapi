from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.system_setting import SystemSetting

class SystemSettingRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, company_id: int) -> list[SystemSetting]:
        result = await self.db.execute(
            select(SystemSetting)
            .where(SystemSetting.company_id == company_id)
            .order_by(SystemSetting.key)
        )
        return result.scalars().all()

    async def get_by_id(
        self, setting_id: int, company_id: int
    ) -> SystemSetting | None:
        result = await self.db.execute(
            select(SystemSetting).where(
                SystemSetting.setting_id == setting_id,
                SystemSetting.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_key(
        self, key: str, company_id: int
    ) -> SystemSetting | None:
        result = await self.db.execute(
            select(SystemSetting).where(
                SystemSetting.key        == key,
                SystemSetting.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()
    
   

    async def bulk_create(
        self,
        data:       list[dict],
        company_id: int,
    ) -> list[SystemSetting]:
        settings = [
            SystemSetting(**item, company_id=company_id)
            for item in data
        ]
        self.db.add_all(settings)        
        await self.db.commit()
        for s in settings:
            await self.db.refresh(s)
        return settings




    async def create(self, data: dict) -> SystemSetting:
        setting = SystemSetting(**data)
        self.db.add(setting)
        await self.db.commit()
        await self.db.refresh(setting)
        return setting
    



    async def update(
        self, setting: SystemSetting, data: dict
    ) -> SystemSetting:
        for key, value in data.items():
            if value is not None:
                setattr(setting, key, value)
        await self.db.commit()
        await self.db.refresh(setting)
        return setting
    

    


    async def delete(self, setting: SystemSetting) -> None:
        await self.db.delete(setting)
        await self.db.commit()




    async def upsert(
            self, company_id: int, key: str, value: str, description: str | None = None
        ) -> SystemSetting:
            existing = await self.get_by_key(key, company_id)
            if existing:                              # ← record FOUND in DB
                existing.value      = value           # ← UPDATE the value
                existing.updated_at = func.now()      # ← UPDATE the timestamp
                await self.db.commit()                # ← SAVE to DB
                await self.db.refresh(existing)       # ← reload fresh data
                return existing                       # ← return updated record
            
            setting = SystemSetting(
                company_id  = company_id,
                key         = key,
                value       = value,
                description = description,
                # ✅ updated_at set automatically via default=func.now()
            )

            self.db.add(setting)
            await self.db.commit()
            await self.db.refresh(setting)
            return setting