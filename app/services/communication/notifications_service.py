from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.repositories.communication.notifications_repository import NotificationRepository
from app.schemas.schema import NotificationCreate, BulkMarkReadRequest, NotificationUpdate
from app.dependencies import get_db
from app.db.redis import get_redis_client
from app.websockets.ws_manager import publish_notification


class NotificationService:

    def __init__(
        self,
        db:           AsyncSession,
        redis_client: redis.Redis | None = None,
    ):
        self.repo         = NotificationRepository(db)
        self.redis_client = redis_client   # ✅ for real-time push

    # -----------------------------------------------------------------------
    # SEND — save to DB + push via Redis Pub/Sub → WebSocket
    # -----------------------------------------------------------------------

    async def send(
        self,
        company_id:     int,
        user_id:        int,
        title:          str,
        message:        str,
        notif_type:     str = "info",
        reference_id:   int | None = None,
        reference_type: str | None = None,
    ):
        """
        Internal helper — called from other services.
        1. Saves notification to DB
        2. Publishes to Redis → WebSocket → client sees it instantly
        """
        # 1. Save to DB
        notif = await self.repo.create({
            "company_id":     company_id,
            "user_id":        user_id,
            "title":          title,
            "message":        message,
            "type":           notif_type,
            "is_read":        False,
            "reference_id":   reference_id,
            "reference_type": reference_type,
        })



        # 2. Push real-time via Redis Pub/Sub → WebSocket
        if self.redis_client:
            await publish_notification(
                redis_client = self.redis_client,
                user_id      = user_id,
                data         = {
                    "event":           "new_notification",
                    "notification_id": notif.notification_id,
                    "user_id":         user_id,
                    "title":           title,
                    "message":         message,
                    "type":            notif_type,
                    "is_read":         False,
                    "reference_id":    reference_id,
                    "reference_type":  reference_type,
                    "created_at":      str(notif.created_at),
                },
            )

        return notif

    # -----------------------------------------------------------------------
    # GET my notifications
    # -----------------------------------------------------------------------

    async def get_my_notifications(
        self,
        user_id:     int,
        company_id:  int,
        unread_only: bool = False,
    ) -> list:
        
        return await self.repo.get_by_user(
            user_id     = user_id,
            company_id  = company_id,
            unread_only = unread_only,
    )


    

    # -----------------------------------------------------------------------
    # GET all (admin)
    # -----------------------------------------------------------------------

    async def get_all(
        self,
        company_id:  int,
        unread_only: bool = False,
    ) -> list:
        return await self.repo.get_all(
            company_id  = company_id,
            unread_only = unread_only,
        )

    # -----------------------------------------------------------------------
    # GET one
    # -----------------------------------------------------------------------

    async def get_by_id(self, notification_id: int, company_id: int):
        notif = await self.repo.get_by_id(notification_id, company_id)
        if not notif:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification id={notification_id} not found.",
            )
        return notif

    # -----------------------------------------------------------------------
    # GET summary (unread count)
    # -----------------------------------------------------------------------

    async def get_summary(self, user_id: int, company_id: int) -> dict:
        return await self.repo.get_summary(user_id, company_id)

    # -----------------------------------------------------------------------
    # CREATE (admin sends manually)
    # -----------------------------------------------------------------------

    async def create(self, data: NotificationCreate, company_id: int):
        return await self.send(
            company_id     = company_id,
            user_id        = data.user_id,
            title          = data.title,
            message        = data.message,
            notif_type     = data.type,
            reference_id   = data.reference_id,
            reference_type = data.reference_type,
        )

    # -----------------------------------------------------------------------
    # MARK READ
    # -----------------------------------------------------------------------
    async def mark_read(
        self, notification_id: int, user_id: int, company_id: int
    ) -> NotificationUpdate:
        notif = await self.get_by_id(notification_id, company_id)

        if notif.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only mark your own notifications as read.",
            )

        await self.repo.mark_as_read(
            notification_id = notification_id,
            user_id         = user_id,
        )
        return await self.get_by_id(notification_id, company_id)
    


    



    async def mark_all_read(self, user_id: int, company_id: int) -> dict:
        count = await self.repo.mark_all_read(user_id, company_id)
        return {"message": f"{count} notifications marked as read."}

    async def bulk_mark_read(
        self, data: BulkMarkReadRequest, user_id: int, company_id: int
    ) -> dict:
        count = await self.repo.mark_bulk_read(
            notification_ids = data.notification_ids,
            user_id          = user_id,
            company_id       = company_id,
        )
        return {"message": f"{count} notifications marked as read."}

    # -----------------------------------------------------------------------
    # DELETE
    # -----------------------------------------------------------------------

    async def delete(
        self, notification_id: int, user_id: int, company_id: int
    ) -> dict:
        notif = await self.get_by_id(notification_id, company_id)
        if notif.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own notifications.",
            )
        await self.repo.delete(notif)
        return {"message": f"Notification id={notification_id} deleted."}

    async def delete_all_read(self, user_id: int, company_id: int) -> dict:
        count = await self.repo.delete_all_read(user_id, company_id)
        return {"message": f"{count} read notifications deleted."}


# =============================================================================
# FACTORY — inject both db and redis
# =============================================================================




async def get_notification_service(
    db:           AsyncSession  = Depends(get_db),
    redis_client: redis.Redis   = Depends(get_redis_client),
) -> NotificationService:
    return NotificationService(db=db, redis_client=redis_client)