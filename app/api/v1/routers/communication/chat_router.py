from fastapi import APIRouter, Depends, status, Query, UploadFile, File, HTTPException
from app.schemas.chatSchema import (
    ChatGroupCreate,
    DirectMessageCreate,
    SendMessageRequest,
    AddMemberRequest,
)
from app.services.communication.chat_service import ChatService, get_chat_service
from app.utils.auth import require_login, require_manager
from app.websockets.chat_ws_manager import chat_ws_manager
chat_router = APIRouter(prefix="/chat", tags=["Chat"])

# ==============================================================================
# GROUPS
# ==============================================================================

@chat_router.post(
    "/groups",
    status_code=status.HTTP_201_CREATED,
    summary="[Manager] Create a group chat",
)
async def create_group(
    data:         ChatGroupCreate,
    current_user: dict        = Depends(require_manager),
    service:      ChatService = Depends(get_chat_service),
):
    """Manager creates a group chat and adds initial members."""
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(403, "Manager must have a staff profile to create chat.")
    return await service.create_group(
        data       = data,
        user_id    = int(user_id),
        company_id = current_user["company_id"],
    )




@chat_router.post(
    "/direct",
    status_code=status.HTTP_201_CREATED,
    summary="Start or get a direct message with another staff",
)
async def create_direct_chat(
    data:         DirectMessageCreate,
    current_user: dict        = Depends(require_login),
    service:      ChatService = Depends(get_chat_service),
):
    """Any staff can start a 1-to-1 DM. Returns existing DM if already created."""
    staff_id = current_user.get("staff_id")
    if not staff_id:
        raise HTTPException(403, "Only staff can use direct messages.")
    return await service.create_direct_chat(
        data       = data,
        staff_id   = staff_id,
        company_id = current_user["company_id"],
    )



@chat_router.get(
    "/groups/my",
    summary="Get my chat groups",
)
async def get_my_groups(
    current_user: dict        = Depends(require_login),
    service:      ChatService = Depends(get_chat_service),
):
    staff_id = current_user.get("staff_id")
    if not staff_id:
        return []
    return await service.get_my_groups(
        staff_id   = staff_id,
        company_id = current_user["company_id"],
    )




@chat_router.get(
    "/groups",
    summary="[Manager] Get all groups in company",
)
async def get_all_groups(
    current_user: dict        = Depends(require_manager),
    service:      ChatService = Depends(get_chat_service),
):
    return await service.get_all_groups(company_id=current_user["company_id"])




@chat_router.get(
    "/groups/{group_id}",
    summary="Get group info",
)
async def get_group(
    group_id:     int,
    current_user: dict        = Depends(require_login),
    service:      ChatService = Depends(get_chat_service),
):
    return await service.get_group(
        group_id   = group_id,
        company_id = current_user["company_id"],
    )




@chat_router.delete(
    "/groups/{group_id}",
    summary="[Manager] Delete group + all Cloudinary assets",
)
async def delete_group(
    group_id:     int,
    current_user: dict        = Depends(require_manager),
    service:      ChatService = Depends(get_chat_service),
):
    """Deletes group, all messages, and removes all Cloudinary assets."""
    return await service.delete_group(
        group_id   = group_id,
        company_id = current_user["company_id"],
    )


# ==============================================================================
# MEMBERS
# ==============================================================================

@chat_router.get(
    "/groups/{group_id}/members",
    summary="Get group members",
)
async def get_members(
    group_id:     int,
    current_user: dict        = Depends(require_login),
    service:      ChatService = Depends(get_chat_service),
):
    return await service.get_members(
        group_id   = group_id,
        company_id = current_user["company_id"],
    )


@chat_router.post(
    "/groups/{group_id}/members",
    summary="[Manager] Add members to group",
)
async def add_members(
    group_id:     int,
    data:         AddMemberRequest,
    current_user: dict        = Depends(require_manager),
    service:      ChatService = Depends(get_chat_service),
):
    return await service.add_members(
        group_id    = group_id,
        staff_ids   = data.staff_ids,
        company_id  = current_user["company_id"],
        by_staff_id = current_user.get("staff_id", 0),
    )


@chat_router.delete(
    "/groups/{group_id}/members/{staff_id}",
    summary="[Manager] Remove member from group",
)
async def remove_member(
    group_id:     int,
    staff_id:     int,
    current_user: dict        = Depends(require_manager),
    service:      ChatService = Depends(get_chat_service),
):
    return await service.remove_member(
        group_id    = group_id,
        staff_id    = staff_id,
        company_id  = current_user["company_id"],
        by_staff_id = current_user.get("staff_id", 0),
    )


@chat_router.get(
    "/groups/{group_id}/online",
    summary="Get online members in group",
)
async def get_online_members(
    group_id:     int,
    current_user: dict        = Depends(require_login),
    service:      ChatService = Depends(get_chat_service),
):
    online = await service.get_online_members(group_id)
    return {
        "group_id":         group_id,
        "online_staff_ids": online,
        "count":            len(online),
    }


# ==============================================================================
# MESSAGES — TEXT
# ==============================================================================

@chat_router.post(
    "/groups/{group_id}/messages",
    status_code=status.HTTP_201_CREATED,
    summary="Send a text message (supports reply_to_id)",
)
async def send_message(
    group_id:     int,
    data:         SendMessageRequest,
    current_user: dict        = Depends(require_login),
    service:      ChatService = Depends(get_chat_service),
):
    """
    Send a text message to the group.
    Include `reply_to_id` in the body to reply to a specific message.
    """
    staff_id = current_user.get("staff_id")
    if not staff_id:
        raise HTTPException(403, "Only staff can send messages.")
    return await service.send_message(
        group_id   = group_id,
        data       = data,
        staff_id   = staff_id,
        company_id = current_user["company_id"],
    )


# ==============================================================================
# MESSAGES — IMAGE
# ==============================================================================

@chat_router.post(
    "/groups/{group_id}/images",
    status_code=status.HTTP_201_CREATED,
    summary="Send an image (jpg, png, gif, webp, svg — max 10MB)",
)
async def send_image(
    group_id:     int,
    file:         UploadFile   = File(...),
    reply_to_id:  int | None   = Query(None, description="Reply to message id"),
    current_user: dict         = Depends(require_login),
    service:      ChatService  = Depends(get_chat_service),
):
    """
    Uploads image to Cloudinary with auto quality + format.
    Allowed: image/jpeg, image/png, image/webp, image/gif, image/svg+xml.
    Max size: 10MB.
    """
    staff_id = current_user.get("staff_id")
    if not staff_id:
        raise HTTPException(403, "Only staff can send images.")
    return await service.send_image(
        group_id    = group_id,
        file        = file,
        staff_id    = staff_id,
        company_id  = current_user["company_id"],
        reply_to_id = reply_to_id,
    )


# ==============================================================================
# MESSAGES — VIDEO
# ==============================================================================

@chat_router.post(
    "/groups/{group_id}/videos",
    status_code=status.HTTP_201_CREATED,
    summary="Send a video (mp4, mov, avi, webm — max 200MB)",
)
async def send_video(
    group_id:     int,
    file:         UploadFile   = File(...),
    reply_to_id:  int | None   = Query(None, description="Reply to message id"),
    current_user: dict         = Depends(require_login),
    service:      ChatService  = Depends(get_chat_service),
):
    """
    Uploads video to Cloudinary with 6MB chunked upload.
    Allowed: video/mp4, video/mov, video/avi, video/webm, video/quicktime.
    Max size: 200MB. Returns duration_secs in response.
    """
    staff_id = current_user.get("staff_id")
    if not staff_id:
        raise HTTPException(403, "Only staff can send videos.")
    return await service.send_video(
        group_id    = group_id,
        file        = file,
        staff_id    = staff_id,
        company_id  = current_user["company_id"],
        reply_to_id = reply_to_id,
    )


# ==============================================================================
# MESSAGES — AUDIO
# ==============================================================================

@chat_router.post(
    "/groups/{group_id}/audio",
    status_code=status.HTTP_201_CREATED,
    summary="Send an audio file (mp3, wav, ogg — max 50MB)",
)
async def send_audio(
    group_id:     int,
    file:         UploadFile   = File(...),
    reply_to_id:  int | None   = Query(None, description="Reply to message id"),
    current_user: dict         = Depends(require_login),
    service:      ChatService  = Depends(get_chat_service),
):
    """Audio files stored in Cloudinary as video resource type."""
    staff_id = current_user.get("staff_id")
    if not staff_id:
        raise HTTPException(403, "Only staff can send audio.")
    return await service.send_audio(
        group_id    = group_id,
        file        = file,
        staff_id    = staff_id,
        company_id  = current_user["company_id"],
        is_voice    = False,
        reply_to_id = reply_to_id,
    )


# ==============================================================================
# MESSAGES — VOICE NOTE
# ==============================================================================

@chat_router.post(
    "/groups/{group_id}/voice",
    status_code=status.HTTP_201_CREATED,
    summary="Send a voice note (recorded in-app)",
)
async def send_voice(
    group_id:     int,
    file:         UploadFile   = File(...),
    reply_to_id:  int | None   = Query(None, description="Reply to message id"),
    current_user: dict         = Depends(require_login),
    service:      ChatService  = Depends(get_chat_service),
):
    """
    Voice notes are stored the same as audio but message_type = voice.
    Frontend can use this to distinguish between uploaded audio files and
    in-app recordings.
    """
    staff_id = current_user.get("staff_id")
    if not staff_id:
        raise HTTPException(403, "Only staff can send voice notes.")
    return await service.send_audio(
        group_id    = group_id,
        file        = file,
        staff_id    = staff_id,
        company_id  = current_user["company_id"],
        is_voice    = True,
        reply_to_id = reply_to_id,
    )


# ==============================================================================
# MESSAGES — FILE
# ==============================================================================

@chat_router.post(
    "/groups/{group_id}/files",
    status_code=status.HTTP_201_CREATED,
    summary="Send a file (pdf, zip, csv, docx, xlsx — max 50MB)",
)
async def send_file(
    group_id:     int,
    file:         UploadFile   = File(...),
    reply_to_id:  int | None   = Query(None, description="Reply to message id"),
    current_user: dict         = Depends(require_login),
    service:      ChatService  = Depends(get_chat_service),
):
    """
    Uploads file to Cloudinary as raw resource type.
    Allowed: application/pdf, application/zip, text/csv, docx, xlsx.
    Max size: 50MB.
    """
    staff_id = current_user.get("staff_id")
    if not staff_id:
        raise HTTPException(403, "Only staff can send files.")
    return await service.send_file(
        group_id    = group_id,
        file        = file,
        staff_id    = staff_id,
        company_id  = current_user["company_id"],
        reply_to_id = reply_to_id,
    )


# ==============================================================================
# GET MESSAGES
# ==============================================================================

@chat_router.get(
    "/groups/{group_id}/messages",
    summary="Get group messages — paginated, newest first",
)
async def get_messages(
    group_id:     int,
    skip:         int          = Query(0,  ge=0),
    limit:        int          = Query(50, ge=1, le=100),
    current_user: dict         = Depends(require_login),
    service:      ChatService  = Depends(get_chat_service),
):
    """
    Returns messages with sender info, reply_to preview, file metadata,
    duration_secs for audio/video, and is_read status.
    """
    staff_id = current_user.get("staff_id")
    if not staff_id:
        return []
    return await service.get_messages(
        group_id   = group_id,
        staff_id   = staff_id,
        company_id = current_user["company_id"],
        skip       = skip,
        limit      = limit,
    )


# ==============================================================================
# READ RECEIPTS
# ==============================================================================

@chat_router.patch(
    "/groups/{group_id}/messages/{message_id}/read",
    summary="Mark a single message as read",
)
async def mark_message_read(
    group_id:     int,
    message_id:   int,
    current_user: dict        = Depends(require_login),
    service:      ChatService = Depends(get_chat_service),
):
    """Marks message as read and publishes 'message_read' WebSocket event."""
    staff_id = current_user.get("staff_id")
    if not staff_id:
        raise HTTPException(403, "Only staff can mark messages as read.")
    return await service.mark_message_read(
        message_id = message_id,
        staff_id   = staff_id,
        company_id = current_user["company_id"],
    )


@chat_router.patch(
    "/groups/{group_id}/messages/read-all",
    summary="Mark all messages in group as read",
)
async def mark_all_read(
    group_id:     int,
    current_user: dict        = Depends(require_login),
    service:      ChatService = Depends(get_chat_service),
):
    """Marks all messages not sent by current user as read."""
    staff_id = current_user.get("staff_id")
    if not staff_id:
        raise HTTPException(403, "Only staff can mark messages as read.")
    return await service.mark_all_read(
        group_id   = group_id,
        staff_id   = staff_id,
        company_id = current_user["company_id"],
    )


@chat_router.get(
    "/groups/{group_id}/messages/unread-count",
    summary="Get unread message count in group",
)
async def get_unread_count(
    group_id:     int,
    current_user: dict        = Depends(require_login),
    service:      ChatService = Depends(get_chat_service),
):
    staff_id = current_user.get("staff_id")
    if not staff_id:
        raise HTTPException(403, "Only staff can check unread count.")
    return await service.get_unread_count(
        group_id   = group_id,
        staff_id   = staff_id,
        company_id = current_user["company_id"],
    )


# ==============================================================================
# DELETE MESSAGE
# ==============================================================================

@chat_router.delete(
    "/groups/{group_id}/messages/{message_id}",
    summary="Soft-delete own message — removes Cloudinary asset if any",
)
async def delete_message(
    group_id:     int,
    message_id:   int,
    current_user: dict        = Depends(require_login),
    service:      ChatService = Depends(get_chat_service),
):
    """
    Soft-deletes the message (content cleared, row kept for reply references).
    If the message has a Cloudinary asset (image/video/audio/file), it is
    deleted from Cloudinary first.
    """
    staff_id = current_user.get("staff_id")
    if not staff_id:
        raise HTTPException(403, "Only staff can delete messages.")
    return await service.delete_message(
        message_id = message_id,
        staff_id   = staff_id,
        company_id = current_user["company_id"],
    )