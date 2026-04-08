from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, update

from app.models.notification import Notification


class NotificationRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    # -----------------------------------------------------------------------
    # Get all notifications for a user
    # -----------------------------------------------------------------------

    async def get_by_user(
            self,
            user_id:     int,
            company_id:  int,
            unread_only: bool = False,
        ) -> list[Notification]:
            
            query = select(Notification).where(
                Notification.user_id    == user_id,
                Notification.company_id == company_id,
            )

            if unread_only:
                query = query.where(Notification.is_read == False)  

            query = query.order_by(Notification.created_at.desc()) 

            result = await self.db.execute(query)
            return result.scalars().all()

    
    # -----------------------------------------------------------------------
    # Get all notifications for a company (admin view)
    # -----------------------------------------------------------------------

    async def get_all(
        self,
        company_id:  int,
        unread_only: bool = False,
    ) -> list[Notification]:
        query = (
            select(Notification)
            .where(Notification.company_id == company_id)
            .order_by(Notification.created_at.desc())
        )
        if unread_only:
            query = query.where(Notification.is_read == False)
        result = await self.db.execute(query)
        return result.scalars().all()

    # -----------------------------------------------------------------------
    # Get one notification
    # -----------------------------------------------------------------------

    async def get_by_id(
        self, notification_id: int, company_id: int
    ) -> Notification | None:
        result = await self.db.execute(
            select(Notification).where(
                Notification.notification_id == notification_id,
                Notification.company_id      == company_id,
            )
        )
        return result.scalar_one_or_none()

    # -----------------------------------------------------------------------
    # Create notification
    # -----------------------------------------------------------------------

    async def create(self, data: dict) -> Notification:
        notification = Notification(**data)
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    # -----------------------------------------------------------------------
    # Mark one as read
    # -----------------------------------------------------------------------

    async def mark_as_read(self, notification_id: int, user_id: int) -> None:
        await self.db.execute(
            update(Notification)
            .where(
                Notification.notification_id == notification_id,
                Notification.user_id         == user_id,
            )
            .values(is_read=True)
        )
        await self.db.commit()


        

    # -----------------------------------------------------------------------
    # Mark all as read for a user
    # -----------------------------------------------------------------------

    async def mark_all_read(self, user_id: int, company_id: int) -> int:
        result = await self.db.execute(
            update(Notification)
            .where(
                Notification.user_id    == user_id,
                Notification.company_id == company_id,
                Notification.is_read    == False,
            )
            .values(is_read=True)
        )
        await self.db.commit()
        return result.rowcount

    # -----------------------------------------------------------------------
    # Mark multiple as read (bulk)
    # -----------------------------------------------------------------------

    async def mark_bulk_read(
        self,
        notification_ids: list[int],
        user_id:          int,
        company_id:       int,
    ) -> int:
        result = await self.db.execute(
            update(Notification)
            .where(
                Notification.notification_id.in_(notification_ids),
                Notification.user_id         == user_id,
                Notification.company_id      == company_id,
            )
            .values(is_read=True)
        )
        await self.db.commit()
        return result.rowcount

    # -----------------------------------------------------------------------
    # Delete one notification
    # -----------------------------------------------------------------------

    async def delete(self, notification: Notification) -> None:
        await self.db.delete(notification)
        await self.db.commit()

    # -----------------------------------------------------------------------
    # Delete all read notifications for a user
    # -----------------------------------------------------------------------

    async def delete_all_read(self, user_id: int, company_id: int) -> int:
        notifications = await self.db.execute(
            select(Notification).where(
                Notification.user_id    == user_id,
                Notification.company_id == company_id,
                Notification.is_read    == True,
            )
        )
        items = notifications.scalars().all()
        for item in items:
            await self.db.delete(item)
        await self.db.commit()
        return len(items)

    # -----------------------------------------------------------------------
    # Summary counts
    # -----------------------------------------------------------------------

    async def get_summary(self, user_id: int, company_id: int) -> dict:
        total = await self.db.execute(
            select(func.count()).select_from(Notification)
            .where(
                Notification.user_id    == user_id,
                Notification.company_id == company_id,
            )
        )
        unread = await self.db.execute(
            select(func.count()).select_from(Notification)
            .where(
                Notification.user_id    == user_id,
                Notification.company_id == company_id,
                Notification.is_read    == False,
            )
        )
        total_count  = total.scalar()  or 0
        unread_count = unread.scalar() or 0
        return {
            "total":  total_count,
            "unread": unread_count,
            "read":   total_count - unread_count,
        }