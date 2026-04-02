from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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
        self, company_id: int, key: str, value: str
    ) -> SystemSetting:
        """Update if exists, create if not."""
        existing = await self.get_by_key(key, company_id)
        if existing:
            existing.value = value
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        setting = SystemSetting(
            company_id = company_id,
            key        = key,
            value      = value,
        )
        self.db.add(setting)
        await self.db.commit()
        await self.db.refresh(setting)
        return setting