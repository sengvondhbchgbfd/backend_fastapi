from fastapi import APIRouter, Depends, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.schemas.chatSchema import (
    ChatGroupCreate,
    DirectMessageCreate,
    SendMessageRequest,
    AddMemberRequest,
    RemoveMemberRequest,
)
from app.services.chat_service import ChatService, get_chat_service
from app.utils.auth import require_login, require_manager
from app.websockets.chat_ws_manager import chat_ws_manager

chat_router = APIRouter(prefix="/chat", tags=["Chat"])



# ===========================================================================
# GROUPS
# ===========================================================================



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
    """Manager/Admin creates a group chat and adds members."""
    user_id = current_user.get("sub")
    if not user_id:
        from fastapi import HTTPException
        raise HTTPException(403, "Manager must have a staff profile to create chat.")
    
    
    return await service.create_group(
        data       = data,
        user_id   = int(user_id),
        company_id = current_user["company_id"],
    )



# ======================================================================
# 
# ======================================================================

@chat_router.post(
    "/direct",
    status_code=status.HTTP_201_CREATED,
    summary="Start or get direct message with another staff",
)
async def create_direct_chat(
    data:         DirectMessageCreate,
    current_user: dict        = Depends(require_login),
    service:      ChatService = Depends(get_chat_service),
):
    """Any staff can start a 1-to-1 direct message."""
    staff_id = current_user.get("staff_id")
    if not staff_id:
        from fastapi import HTTPException
        raise HTTPException(403, "Only staff can use direct messages.")
    return await service.create_direct_chat(
        data       = data,
        staff_id   = staff_id,
        company_id = current_user["company_id"],
    )

@chat_router.get(
    "/groups/my",
    summary="Staff: get my chat groups",
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

# =====================================================================

@chat_router.get(
    "/groups",
    summary="[Manager] Get all groups in company",
)
async def get_all_groups(
    current_user: dict        = Depends(require_manager),
    service:      ChatService = Depends(get_chat_service),
):
    return await service.get_all_groups(
        company_id=current_user["company_id"]
    )





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
    summary="[Manager] Delete group",
)
async def delete_group(
    group_id:     int,
    current_user: dict        = Depends(require_manager),
    service:      ChatService = Depends(get_chat_service),
):
    return await service.delete_group(
        group_id   = group_id,
        company_id = current_user["company_id"],
    )




# ===========================================================================
# MEMBERS
# ===========================================================================

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


# ========================================================================
# 
# =======================================================================





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
        "group_id": group_id, 
        "online_staff_ids": online, 
        "count": len(online)
    }




# ===========================================================================
# MESSAGES
# ===========================================================================

@chat_router.post(
    "/groups/{group_id}/messages",
    status_code=status.HTTP_201_CREATED,
    summary="Send text message to group",
)
async def send_message(
    group_id:     int,
    data:         SendMessageRequest,
    current_user: dict        = Depends(require_login),
    service:      ChatService = Depends(get_chat_service),
):
    staff_id = current_user.get("staff_id")
    if not staff_id:
        from fastapi import HTTPException
        raise HTTPException(403, "Only staff can send messages.")
    return await service.send_message(
        group_id   = group_id,
        data       = data,
        staff_id   = staff_id,
        company_id = current_user["company_id"],
    )


@chat_router.post(
    "/groups/{group_id}/files",
    status_code=status.HTTP_201_CREATED,
    summary="Send file or image to group",
)
async def send_file(
    group_id:     int,
    file:         UploadFile   = File(...),
    current_user: dict         = Depends(require_login),
    service:      ChatService  = Depends(get_chat_service),
):
    """Upload file or image — max 10MB. Images: jpg, jpeg, png, gif, webp."""
    staff_id = current_user.get("staff_id")
    if not staff_id:
        from fastapi import HTTPException
        raise HTTPException(403, "Only staff can send files.")
    return await service.send_file(
        group_id   = group_id,
        file       = file,
        staff_id   = staff_id,
        company_id = current_user["company_id"],
    )


@chat_router.get(
    "/groups/{group_id}/messages",
    summary="Get group messages (paginated, newest first)",
)
async def get_messages(
    group_id:     int,
    skip:         int          = Query(0, ge=0),
    limit:        int          = Query(50, ge=1, le=100),
    current_user: dict         = Depends(require_login),
    service:      ChatService  = Depends(get_chat_service),
):
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


@chat_router.delete(
    "/groups/{group_id}/messages/{message_id}",
    summary="Delete own message (soft delete)",
)
async def delete_message(
    group_id:     int,
    message_id:   int,
    current_user: dict        = Depends(require_login),
    service:      ChatService = Depends(get_chat_service),
):
    staff_id = current_user.get("staff_id")
    if not staff_id:
        from fastapi import HTTPException
        raise HTTPException(403, "Only staff can delete messages.")
    return await service.delete_message(
        message_id = message_id,
        staff_id   = staff_id,
        company_id = current_user["company_id"],
    )