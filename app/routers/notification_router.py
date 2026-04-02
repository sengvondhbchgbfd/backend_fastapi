from fastapi import APIRouter, Depends, status, Query

from app.schemas.schema import (
    NotificationCreate,
    NotificationResponse,
    NotificationSummaryResponse,
    BulkMarkReadRequest,
)
from app.services.notifications_service import NotificationService, get_notification_service
from app.utils.auth import  require_login, require_admin

notification_router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)




# ===========================================================================
# USER — own notifications
# ===========================================================================

@notification_router.get(
    "/my",
    response_model=list[NotificationResponse],
    summary="Get my notifications",
)
async def get_my_notifications(
    unread_only:  bool = Query(False, description="Show only unread"),
    current_user: dict = Depends(require_login),
    service:      NotificationService = Depends(get_notification_service),
): 
    """Get all notifications for the logged-in user."""
    return await service.get_my_notifications(
        user_id     = int(current_user["sub"]),
        company_id  = current_user["company_id"],
        unread_only = unread_only,
    )







@notification_router.get(
    "/my/summary",
    response_model=NotificationSummaryResponse,
    summary="Get my notification counts",
)
async def get_my_summary(
    current_user: dict = Depends(require_login),
    service:      NotificationService = Depends(get_notification_service),
):
    """Returns total, unread and read counts — useful for badge on app icon."""
    return await service.get_summary(
        user_id    = int(current_user["sub"]),
        company_id = current_user["company_id"],
    )


@notification_router.patch(
    "/my/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark one notification as read",
)
async def mark_one_read(
    notification_id: int,
    current_user:    dict = Depends(require_login),
    service:         NotificationService = Depends(get_notification_service),
):
    return await service.mark_read(
        notification_id = notification_id,
        user_id         = int(current_user["sub"]),
        company_id      = current_user["company_id"],
    )


@notification_router.patch(
    "/my/read-all",
    summary="Mark all my notifications as read",
)
async def mark_all_read(
    current_user: dict = Depends(require_login),
    service:      NotificationService = Depends(get_notification_service),
):
    return await service.mark_all_read(
        user_id    = int(current_user["sub"]),
        company_id = current_user["company_id"],
    )


@notification_router.patch(
    "/my/bulk-read",
    summary="Mark multiple notifications as read",
)
async def bulk_mark_read(
    data:         BulkMarkReadRequest,
    current_user: dict = Depends(require_login),
    service:      NotificationService = Depends(get_notification_service),
):
    return await service.bulk_mark_read(
        data       = data,
        user_id    = int(current_user["sub"]),
        company_id = current_user["company_id"],
    )


@notification_router.delete(
    "/my/{notification_id}",
    summary="Delete one notification",
)
async def delete_one(
    notification_id: int,
    current_user:    dict = Depends(require_login),
    service:         NotificationService = Depends(get_notification_service),
):
    return await service.delete(
        notification_id = notification_id,
        user_id         = int(current_user["sub"]),
        company_id      = current_user["company_id"],
    )


@notification_router.delete(
    "/my/clear-read",
    summary="Delete all read notifications",
)
async def delete_all_read(
    current_user: dict = Depends(require_login),
    service:      NotificationService = Depends(get_notification_service),
):
    return await service.delete_all_read(
        user_id    = int(current_user["sub"]),
        company_id = current_user["company_id"],
    )


# ===========================================================================
# ADMIN — send + view all notifications
# ===========================================================================

@notification_router.get(
    "/",
    response_model=list[NotificationResponse],
    summary="[Admin] List all company notifications",
)


async def get_all_notifications(
    unread_only:  bool = Query(False),
    current_user: dict = Depends(require_admin),
    service:      NotificationService = Depends(get_notification_service),
):
    return await service.get_all(
        company_id  = current_user["company_id"],
        unread_only = unread_only,
    )


@notification_router.post(
    "/",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Send notification to a user",
)



async def create_notification(
    data:         NotificationCreate,
    current_user: dict = Depends(require_admin),
    service:      NotificationService = Depends(get_notification_service),
):
    """
    Admin manually sends notification to a specific user.
    For automatic notifications (leave approved, salary created)
    use the internal send() helper from other services.
    """
    return await service.create(
        data       = data,
        company_id = current_user["company_id"],
    )