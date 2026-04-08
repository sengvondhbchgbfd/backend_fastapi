import os
import uuid
import base64
from fastapi import HTTPException, status, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.repositories.communication.chat_repository import ChatRepository
from app.repositories.hr.staff_repository import StaffRepository
from app.models.chat.chat_group import ChatType
from app.models.chat.chat_message import  MessageType
from app.schemas.chatSchema import (
    ChatGroupCreate, DirectMessageCreate,
    SendMessageRequest,
)
from app.websockets.chat_ws_manager import publish_chat_message
from app.dependencies import get_db, get_redis_client
from app.websockets.chat_ws_manager import chat_ws_manager



class ChatService:

    def __init__(
        self,
        db:           AsyncSession,
        redis_client: redis.Redis,
    ):
        self.repo       = ChatRepository(db)
        self.staff_repo = StaffRepository(db)
        self.redis      = redis_client

    # -----------------------------------------------------------------------
    # HELPER — verify staff is member of group
    # -----------------------------------------------------------------------

    async def _verify_member(
        self, group_id: int, staff_id: int, company_id: int
    ) -> None:
        member = await self.repo.get_member(group_id, staff_id, company_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this group.",
            )

    async def _verify_group(
        self, group_id: int, company_id: int
    ):
        group = await self.repo.get_group_by_id(group_id, company_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat group id={group_id} not found.",
            )
        return group




    # -----------------------------------------------------------------------
    # CREATE GROUP — manager/admin only
    # -----------------------------------------------------------------------

    async def create_group(self, data: ChatGroupCreate, user_id: int, company_id: int):
        # Map User → Staff
        creator_staff = await self.staff_repo.get_by_user_id(user_id, company_id)

        if not creator_staff:
            raise HTTPException(403, "Manager must have a staff profile to create chat.")
        creator_staff_id = creator_staff.staff_id

        # Create group
        group = await self.repo.create_group({
            "company_id": company_id,
            "group_name": data.group_name,
            "chat_type": data.chat_type,
            "created_by": user_id,
            "is_active": True,
        })
        if not group:
            raise HTTPException(status_code=500, detail="Group creation failed")

        # Add creator as admin
        await self.repo.add_member({
            "group_id": group.group_id,
            "staff_id": creator_staff_id,
            "company_id": company_id,
            "is_admin": True,
        })

        # Add other members
        for sid in data.member_ids or []:
            if sid == user_id:
                continue
            staff = await self.staff_repo.get_by_user_id(sid, company_id)
            if not staff:
                raise HTTPException(status_code=404, detail=f"Staff id {sid} not found")

            await self.repo.add_member({
                "group_id": group.group_id,
                "staff_id": staff.staff_id,
                "company_id": company_id,
                "is_admin": False,
            })

        await self.repo.commit()
        return group

    # -----------------------------------------------------------------------
    # CREATE DIRECT MESSAGE (1 to 1)
    # -----------------------------------------------------------------------




    async def create_direct_chat(
        self,
        data:       DirectMessageCreate,
        staff_id:   int,
        company_id: int,
    ):
        # Check target staff exists
        target = await self.staff_repo.get_by_id(data.staff_id, company_id)
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Staff id={data.staff_id} not found.",
            )

        if data.staff_id == staff_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create a direct message with yourself.",
            )

        # Check if DM already exists
        existing = await self.repo.find_direct_chat(
            staff_id, data.staff_id, company_id
        )
        if existing:
            return existing   # return existing DM group

        # Create DM group
        me = await self.staff_repo.get_by_id(staff_id, company_id)
        dm_name = f"{me.name if me else 'Staff'} & {target.name}"

        group = await self.repo.create_group({
            "company_id": company_id,
            "name":       dm_name,
            "chat_type":  ChatType.direct,
            "created_by": staff_id,
            "is_active":  True,
        })

        # Add both members
        for sid in [staff_id, data.staff_id]:
            await self.repo.add_member({
                "group_id":   group.group_id,
                "staff_id":   sid,
                "company_id": company_id,
                "is_admin":   False,
            })

        await self.repo.commit()
        return group





    # -----------------------------------------------------------------------
    # GET MY GROUPS
    # -----------------------------------------------------------------------

    async def get_my_groups(self, staff_id: int, company_id: int) -> list:
        return await self.repo.get_my_groups(staff_id, company_id)

    async def get_all_groups(self, company_id: int) -> list:
        return await self.repo.get_all_groups(company_id)

    async def get_group(self, group_id: int, company_id: int):
        return await self._verify_group(group_id, company_id)

    # -----------------------------------------------------------------------
    # ADD MEMBER
    # -----------------------------------------------------------------------



    async def add_members(
        self,
        group_id:   int,
        staff_ids:  list[int],
        company_id: int,
        by_staff_id: int,
    ):
        await self._verify_group(group_id, company_id)
        await self._verify_member(group_id, by_staff_id, company_id)

        added = []
        for sid in staff_ids:
            # check not already a member
            existing = await self.repo.get_member(group_id, sid, company_id)
            if existing:
                continue

            staff = await self.staff_repo.get_by_id(sid, company_id)
            if not staff:
                continue

            await self.repo.add_member({
                "group_id":   group_id,
                "staff_id":   sid,
                "company_id": company_id,
                "is_admin":   False,
            })
            added.append(sid)

        await self.repo.commit()

        # ✅ notify group — new members joined
        if added:
            await publish_chat_message(
                redis_client = self.redis,
                group_id     = group_id,
                data         = {
                    "event":    "members_added",
                    "group_id": group_id,
                    "added":    added,
                },
            )

        return {"message": f"{len(added)} member(s) added.", "added": added}






    # -----------------------------------------------------------------------
    # REMOVE MEMBER
    # -----------------------------------------------------------------------

    async def remove_member(
        self,
        group_id:    int,
        staff_id:    int,
        company_id:  int,
        by_staff_id: int,
    ):
        await self._verify_group(group_id, company_id)

        member = await self.repo.get_member(group_id, staff_id, company_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in this group.",
            )

        await self.repo.remove_member(member)
        await self.repo.commit()

        await publish_chat_message(
            redis_client = self.redis,
            group_id     = group_id,
            data         = {
                "event":      "member_removed",
                "group_id":   group_id,
                "staff_id":   staff_id,
            },
        )

        return {"message": "Member removed."}

    # -----------------------------------------------------------------------
    # GET MEMBERS
    # -----------------------------------------------------------------------

    async def get_members(self, group_id: int, company_id: int) -> list:
        await self._verify_group(group_id, company_id)
        members = await self.repo.get_members(group_id, company_id)
        return [
            {
                "member_id":  m.id,
                "group_id":   m.group_id,
                "staff_id":   m.staff_id,
                "company_id": m.company_id,
                "joined_at":  m.joined_at,
                "is_admin":   m.is_admin,
                "staff_name": m.staff.name if m.staff else None,
            }
            for m in members
        ]
    



    # -----------------------------------------------------------------------
    # SEND TEXT MESSAGE — real-time via Redis → WebSocket
    # -----------------------------------------------------------------------

    async def send_message(
        self,
        group_id:   int,
        data:       SendMessageRequest,
        staff_id:   int,
        company_id: int,
    ):
        await self._verify_group(group_id, company_id)
        await self._verify_member(group_id, staff_id, company_id)

        if not data.content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content cannot be empty.",
            )

        # Save to DB
        message = await self.repo.create_message({
            "group_id":     group_id,
            "company_id":   company_id,
            "sender_id":    staff_id,
            "message_type": MessageType.text,
            "content":      data.content,
            "is_deleted":   False,
        })

        # Get sender name
        staff      = await self.staff_repo.get_by_id(staff_id, company_id)
        staff_name = staff.name if staff else "Staff"

        # ✅ publish to Redis → all group members receive via WebSocket
        await publish_chat_message(
            redis_client = self.redis,
            group_id     = group_id,
            data         = {
                "event":        "new_message",
                "message_id":   message.message_id,
                "group_id":     group_id,
                "sender_id":    staff_id,
                "sender_name":  staff_name,
                "message_type": "text",
                "content":      data.content,
                "is_deleted":   False,
                "created_at":   str(message.created_at),
            },
        )

        return message

    # -----------------------------------------------------------------------
    # SEND FILE/IMAGE — upload + real-time notify
    # -----------------------------------------------------------------------

    async def send_file(
        self,
        group_id:   int,
        file:       UploadFile,
        staff_id:   int,
        company_id: int,
    ):
        await self._verify_group(group_id, company_id)
        await self._verify_member(group_id, staff_id, company_id)

        # Read file content
        content   = await file.read()
        file_size = len(content)

        # Validate size — max 10MB
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 10MB limit.",
            )

        # Determine message type
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        ext              = os.path.splitext(file.filename or "")[1].lower()
        message_type     = MessageType.image if ext in image_extensions else MessageType.file

        # Convert to base64 for storage (or save to disk/S3 in production)
        b64_content = base64.b64encode(content).decode("utf-8")
        file_url    = f"data:{file.content_type};base64,{b64_content}"

        # Save to DB
        message = await self.repo.create_message({
            "group_id":     group_id,
            "company_id":   company_id,
            "sender_id":    staff_id,
            "message_type": message_type,
            "content":      None,
            "file_url":     file_url,
            "file_name":    file.filename,
            "file_size":    file_size,
            "is_deleted":   False,
        })

        staff      = await self.staff_repo.get_by_id(staff_id, company_id)
        staff_name = staff.name if staff else "Staff"

        # ✅ publish to Redis → WebSocket
        await publish_chat_message(
            redis_client = self.redis,
            group_id     = group_id,
            data         = {
                "event":        "new_message",
                "message_id":   message.message_id,
                "group_id":     group_id,
                "sender_id":    staff_id,
                "sender_name":  staff_name,
                "message_type": message_type.value,
                "file_name":    file.filename,
                "file_size":    file_size,
                "is_deleted":   False,
                "created_at":   str(message.created_at),
            },
        )

        return message

    # -----------------------------------------------------------------------
    # GET MESSAGES — paginated
    # -----------------------------------------------------------------------

    async def get_messages(
        self,
        group_id:   int,
        staff_id:   int,
        company_id: int,
        skip:       int = 0,
        limit:      int = 50,
    ) -> list:
        await self._verify_group(group_id, company_id)
        await self._verify_member(group_id, staff_id, company_id)

        messages = await self.repo.get_messages(group_id, company_id, skip, limit)
        return [
            {
                "message_id":   m.message_id,
                "group_id":     m.group_id,
                "company_id":   m.company_id,
                "sender_id":    m.sender_id,
                "sender_name":  m.sender.name if m.sender else None,
                "message_type": m.message_type.value,
                "content":      m.content,
                "file_url":     m.file_url,
                "file_name":    m.file_name,
                "file_size":    m.file_size,
                "is_deleted":   m.is_deleted,
                "created_at":   m.created_at,
            }
            for m in messages
        ]

    # -----------------------------------------------------------------------
    # DELETE MESSAGE — soft delete
    # -----------------------------------------------------------------------

    async def delete_message(
        self,
        message_id: int,
        staff_id:   int,
        company_id: int,
    ) -> dict:
        message = await self.repo.get_message_by_id(message_id, company_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message id={message_id} not found.",
            )

        if message.sender_id != staff_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own messages.",
            )

        await self.repo.delete_message(message)

        # ✅ notify group — message deleted
        await publish_chat_message(
            redis_client = self.redis,
            group_id     = message.group_id,
            data         = {
                "event":      "message_deleted",
                "message_id": message_id,
                "group_id":   message.group_id,
            },
        )

        return {"message": f"Message id={message_id} deleted."}

    # -----------------------------------------------------------------------
    # DELETE GROUP
    # -----------------------------------------------------------------------

    async def delete_group(
        self,
        group_id:   int,
        company_id: int,
    ) -> dict:
        group = await self._verify_group(group_id, company_id)
        await self.repo.delete_group(group)

        await publish_chat_message(
            redis_client = self.redis,
            group_id     = group_id,
            data         = {
                "event":    "group_deleted",
                "group_id": group_id,
            },
        )

        return {"message": f"Chat group id={group_id} deleted."}

    # -----------------------------------------------------------------------
    # ONLINE MEMBERS
    # -----------------------------------------------------------------------

    async def get_online_members(self, group_id: int) -> list[int]:
        return chat_ws_manager.get_online_members(group_id)


# =============================================================================
# FACTORY
# =============================================================================

async def get_chat_service(
    db:           AsyncSession = Depends(get_db),
    redis_client: redis.Redis  = Depends(get_redis_client),
) -> ChatService:
    return ChatService(db=db, redis_client=redis_client)