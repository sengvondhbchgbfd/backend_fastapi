from fastapi import HTTPException, status, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.repositories.communication.chat_repository import ChatRepository
from app.repositories.hr.staff_repository import StaffRepository
from app.models.chat.chat_group import ChatType
from app.models.chat.chat_message import ChatMessage, MessageType
from app.schemas.chatSchema import (
    ChatGroupCreate,
    DirectMessageCreate,
    SendMessageRequest,
)
from app.websockets.chat_ws_manager import publish_chat_message, chat_ws_manager

from app.services.communication.notifications_service import NotificationService



from app.dependencies import get_db, get_redis_client
from app.services.storage import CloudinaryStorage

storage = CloudinaryStorage()


# Resource type mapping for Cloudinary delete
CLOUDINARY_RESOURCE_TYPE: dict[MessageType, str] = {
    MessageType.image: "image",
    MessageType.video: "video",
    MessageType.audio: "video",   # Cloudinary treats audio as video resource
    MessageType.voice: "video",
    MessageType.file:  "raw",
}


class ChatService:

    def __init__(
        self,
        db:           AsyncSession,
        redis_client: redis.Redis,
    ):
        self.repo       = ChatRepository(db)
        self.staff_repo = StaffRepository(db)
        self.redis      = redis_client
        self.notify     = NotificationService(db=db, redis_client=redis_client)

    # --------------------------------------------------------------------------
    # INTERNAL HELPERS
    # --------------------------------------------------------------------------

    async def _verify_group(self, group_id: int, company_id: int):
        group = await self.repo.get_group_by_id(group_id, company_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat group id={group_id} not found.",
            )
        return group

    async def _verify_member(self, group_id: int, staff_id: int, company_id: int) -> None:
        member = await self.repo.get_member(group_id, staff_id, company_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this group.",
            )

    async def _get_staff(self, staff_id: int, company_id: int):
        staff = await self.staff_repo.get_by_id(staff_id, company_id)
        if not staff:
            raise HTTPException(404, f"Staff id={staff_id} not found.")
        return staff

    async def _staff_name(self, staff_id: int, company_id: int) -> str:
        staff = await self.staff_repo.get_by_id(staff_id, company_id)
        return staff.name if staff else "Staff"



    async def _delete_cloudinary_asset(self, message: ChatMessage) -> None:
        """Delete Cloudinary asset for any file-based message type."""
        if not message.publice:   # publice = typo in model for public_id
            return
        resource_type = CLOUDINARY_RESOURCE_TYPE.get(message.message_type, "image")
        await storage.delete_asset(
            public_id=message.publice,
            resource_type=resource_type,
        )



    async def _publish(self, group_id: int, data: dict) -> None:
        await publish_chat_message(
            redis_client=self.redis,
            group_id=group_id,
            data=data,
        )

    # --------------------------------------------------------------------------
    # NOTIFY GROUP MEMBERS (except sender)
    # --------------------------------------------------------------------------

    async def _notify_group_members(
        self,
        group_id:    int,
        company_id:  int,
        sender_id:   int,
        sender_name: str,
        title:       str,
        message:     str,
    ) -> None:
        """Send DB + WebSocket notification to every group member except sender."""
        members = await self.repo.get_members(group_id, company_id)
        for member in members:
            if member.staff_id == sender_id:
                continue
            # Get user_id from staff
            staff = await self.staff_repo.get_by_id(member.staff_id, company_id)
            if not staff or not staff.user_id:
                continue
            await self.notify.send(
                company_id     = company_id,
                user_id        = staff.user_id,
                title          = title,
                message        = message,
                notif_type     = "chat",
                reference_id   = group_id,
                reference_type = "chat_group",
            )

    # ==========================================================================
    # GROUPS
    # ==========================================================================

    async def create_group(
        self, data: ChatGroupCreate, user_id: int, company_id: int
    ):
        creator_staff = await self.staff_repo.get_by_user_id(user_id, company_id)
        if not creator_staff:
            raise HTTPException(403, "Manager must have a staff profile to create chat.")

        group = await self.repo.create_group({
            "company_id": company_id,
            "group_name": data.group_name,
            "chat_type":  data.chat_type,
            "created_by": user_id,
            "is_active":  True,
        })
        if not group:
            raise HTTPException(500, "Group creation failed.")

        # Add creator as admin member
        await self.repo.add_member({
            "group_id":   group.group_id,
            "staff_id":   creator_staff.staff_id,
            "company_id": company_id,
            "is_admin":   True,
        })

        # Add other members
        for sid in data.member_ids or []:
            if sid == user_id:
                continue
            staff = await self.staff_repo.get_by_user_id(sid, company_id)
            if not staff:
                raise HTTPException(404, f"Staff user_id={sid} not found.")
            await self.repo.add_member({
                "group_id":   group.group_id,
                "staff_id":   staff.staff_id,
                "company_id": company_id,
                "is_admin":   False,
            })
            # Notify each added member
            await self.notify.send(
                company_id     = company_id,
                user_id        = staff.user_id,
                title          = "Added to group chat",
                message        = f"You were added to '{data.group_name}'",
                notif_type     = "chat",
                reference_id   = group.group_id,
                reference_type = "chat_group",
            )

        await self.repo.commit()
        return group

    async def create_direct_chat(
        self,
        data:       DirectMessageCreate,
        staff_id:   int,
        company_id: int,
    ):
        if data.staff_id == staff_id:
            raise HTTPException(400, "Cannot create a direct message with yourself.")

        target = await self._get_staff(data.staff_id, company_id)

        # Return existing DM if already exists
        existing = await self.repo.find_direct_chat(staff_id, data.staff_id, company_id)
        if existing:
            return existing

        me      = await self.staff_repo.get_by_id(staff_id, company_id)
        dm_name = f"{me.name if me else 'Staff'} & {target.name}"

        group = await self.repo.create_group({
            "company_id": company_id,
            "name":       dm_name,
            "chat_type":  ChatType.direct,
            "created_by": staff_id,
            "is_active":  True,
        })

        for sid in [staff_id, data.staff_id]:
            await self.repo.add_member({
                "group_id":   group.group_id,
                "staff_id":   sid,
                "company_id": company_id,
                "is_admin":   False,
            })

        await self.repo.commit()

        # Notify target staff
        if target.user_id:
            sender_name = me.name if me else "Someone"
            await self.notify.send(
                company_id     = company_id,
                user_id        = target.user_id,
                title          = "New direct message",
                message        = f"{sender_name} started a direct message with you.",
                notif_type     = "chat",
                reference_id   = group.group_id,
                reference_type = "chat_group",
            )

        return group

    async def get_my_groups(self, staff_id: int, company_id: int) -> list:
        return await self.repo.get_my_groups(staff_id, company_id)




    async def get_all_groups(self, company_id: int) -> list:
        return await self.repo.get_all_groups(company_id)




    async def get_group(self, group_id: int, company_id: int):
        return await self._verify_group(group_id, company_id)

    async def delete_group(self, group_id: int, company_id: int) -> dict:
        group = await self._verify_group(group_id, company_id)

        # Clean up all Cloudinary assets in group
        file_messages = await self.repo.get_all_file_messages(group_id, company_id)
        for msg in file_messages:
            await self._delete_cloudinary_asset(msg)

        await self.repo.delete_group(group)

        await self._publish(group_id, {
            "event":    "group_deleted",
            "group_id": group_id,
        })

        return {"message": f"Chat group id={group_id} deleted."}

    # ==========================================================================
    # MEMBERS
    # ==========================================================================

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

    async def add_members(
        self,
        group_id:    int,
        staff_ids:   list[int],
        company_id:  int,
        by_staff_id: int,
    ) -> dict:
        await self._verify_group(group_id, company_id)
        await self._verify_member(group_id, by_staff_id, company_id)

        added = []
        for sid in staff_ids:
            if await self.repo.get_member(group_id, sid, company_id):
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

            # Notify each new member
            if staff.user_id:
                group = await self.repo.get_group_by_id(group_id, company_id)
                await self.notify.send(
                    company_id     = company_id,
                    user_id        = staff.user_id,
                    title          = "Added to group chat",
                    message        = f"You were added to '{group.group_name if group else 'a group'}'",
                    notif_type     = "chat",
                    reference_id   = group_id,
                    reference_type = "chat_group",
                )

        await self.repo.commit()

        if added:
            await self._publish(group_id, {
                "event":    "members_added",
                "group_id": group_id,
                "added":    added,
            })

        return {"message": f"{len(added)} member(s) added.", "added": added}

    async def remove_member(
        self,
        group_id:    int,
        staff_id:    int,
        company_id:  int,
        by_staff_id: int,
    ) -> dict:
        await self._verify_group(group_id, company_id)

        member = await self.repo.get_member(group_id, staff_id, company_id)
        if not member:
            raise HTTPException(404, "Member not found in this group.")

        await self.repo.remove_member(member)
        await self.repo.commit()

        await self._publish(group_id, {
            "event":    "member_removed",
            "group_id": group_id,
            "staff_id": staff_id,
        })

        return {"message": "Member removed."}

    async def get_online_members(self, group_id: int) -> list[int]:
        return chat_ws_manager.get_online_members(group_id)

    # ==========================================================================
    # MESSAGES — TEXT
    # ==========================================================================

    async def send_message(
        self,
        group_id:   int,
        data:       SendMessageRequest,
        staff_id:   int,
        company_id: int,
    ) -> ChatMessage:
        await self._verify_group(group_id, company_id)
        await self._verify_member(group_id, staff_id, company_id)

        if not data.content or not data.content.strip():
            raise HTTPException(400, "Message content cannot be empty.")

        # Validate reply target exists if provided
        if data.reply_to_id:
            replied = await self.repo.get_message_by_id(data.reply_to_id, company_id)
            if not replied:
                raise HTTPException(404, f"Reply target message id={data.reply_to_id} not found.")

        message = await self.repo.create_message({
            "group_id":     group_id,
            "company_id":   company_id,
            "sender_id":    staff_id,
            "message_type": MessageType.text,
            "content":      data.content,
            "reply_to_id":  getattr(data, "reply_to_id", None),
            "is_deleted":   False,
            "is_read":      False,
        })

        staff_name = await self._staff_name(staff_id, company_id)

        # Publish real-time WebSocket event
        await self._publish(group_id, {
            "event":        "new_message",
            "message_id":   message.message_id,
            "group_id":     group_id,
            "sender_id":    staff_id,
            "sender_name":  staff_name,
            "message_type": "text",
            "content":      data.content,
            "reply_to_id":  getattr(data, "reply_to_id", None),
            "is_deleted":   False,
            "is_read":      False,
            "created_at":   str(message.timestamp),
        })

        # Notify offline members via notification system
        await self._notify_group_members(
            group_id    = group_id,
            company_id  = company_id,
            sender_id   = staff_id,
            sender_name = staff_name,
            title       = f"New message from {staff_name}",
            message     = data.content[:80],   # truncate for preview
        )

        return message

    # ==========================================================================
    # MESSAGES — IMAGE
    # ==========================================================================

    async def send_image(
        self,
        group_id:   int,
        file:       UploadFile,
        staff_id:   int,
        company_id: int,
        reply_to_id: int | None = None,
    ) -> ChatMessage:
        await self._verify_group(group_id, company_id)
        await self._verify_member(group_id, staff_id, company_id)

        result = await storage.upload_image(
            file=file,
            folder=f"chat/{company_id}/{group_id}/images",
        )

        message = await self.repo.create_message({
            "group_id":     group_id,
            "company_id":   company_id,
            "sender_id":    staff_id,
            "message_type": MessageType.image,
            "content":      None,
            "file_url":     result["secure_url"],
            "publice":      result["public_id"],      # typo in model — kept as-is
            "file_name":    file.filename,
            "file_size":    result["size"],
            "reply_to_id":  reply_to_id,
            "is_deleted":   False,
            "is_read":      False,
        })

        staff_name = await self._staff_name(staff_id, company_id)

        await self._publish(group_id, {
            "event":        "new_message",
            "message_id":   message.message_id,
            "group_id":     group_id,
            "sender_id":    staff_id,
            "sender_name":  staff_name,
            "message_type": "image",
            "file_url":     result["secure_url"],
            "file_name":    file.filename,
            "file_size":    result["size"],
            "width":        result.get("width"),
            "height":       result.get("height"),
            "reply_to_id":  reply_to_id,
            "is_deleted":   False,
            "is_read":      False,
            "created_at":   str(message.timestamp),
        })

        await self._notify_group_members(
            group_id    = group_id,
            company_id  = company_id,
            sender_id   = staff_id,
            sender_name = staff_name,
            title       = f"{staff_name} sent an image",
            message     = f"📷 {file.filename}",
        )

        return message

    # ==========================================================================
    # MESSAGES — VIDEO
    # ==========================================================================

    async def send_video(
        self,
        group_id:   int,
        file:       UploadFile,
        staff_id:   int,
        company_id: int,
        reply_to_id: int | None = None,
    ) -> ChatMessage:
        await self._verify_group(group_id, company_id)
        await self._verify_member(group_id, staff_id, company_id)

        result = await storage.upload_video(
            file=file,
            folder=f"chat/{company_id}/{group_id}/videos",
        )

        message = await self.repo.create_message({
            "group_id":       group_id,
            "company_id":     company_id,
            "sender_id":      staff_id,
            "message_type":   MessageType.video,
            "content":        None,
            "file_url":       result["secure_url"],
            "publice":        result["public_id"],
            "file_name":      file.filename,
            "file_size":      result["size"],
            "duration_secs":  int(result.get("duration") or 0),
            "reply_to_id":    reply_to_id,
            "is_deleted":     False,
            "is_read":        False,
        })

        staff_name = await self._staff_name(staff_id, company_id)

        await self._publish(group_id, {
            "event":          "new_message",
            "message_id":     message.message_id,
            "group_id":       group_id,
            "sender_id":      staff_id,
            "sender_name":    staff_name,
            "message_type":   "video",
            "file_url":       result["secure_url"],
            "file_name":      file.filename,
            "file_size":      result["size"],
            "duration_secs":  int(result.get("duration") or 0),
            "reply_to_id":    reply_to_id,
            "is_deleted":     False,
            "is_read":        False,
            "created_at":     str(message.timestamp),
        })

        await self._notify_group_members(
            group_id    = group_id,
            company_id  = company_id,
            sender_id   = staff_id,
            sender_name = staff_name,
            title       = f"{staff_name} sent a video",
            message     = f"🎥 {file.filename}",
        )

        return message

    # ==========================================================================
    # MESSAGES — AUDIO / VOICE
    # ==========================================================================

    async def send_audio(
        self,
        group_id:    int,
        file:        UploadFile,
        staff_id:    int,
        company_id:  int,
        is_voice:    bool = False,     # True = voice note, False = audio file
        reply_to_id: int | None = None,
    ) -> ChatMessage:
        await self._verify_group(group_id, company_id)
        await self._verify_member(group_id, staff_id, company_id)

        result = await storage.upload_video(    # Cloudinary: audio = video resource
            file=file,
            folder=f"chat/{company_id}/{group_id}/audio",
        )

        msg_type = MessageType.voice if is_voice else MessageType.audio

        message = await self.repo.create_message({
            "group_id":      group_id,
            "company_id":    company_id,
            "sender_id":     staff_id,
            "message_type":  msg_type,
            "content":       None,
            "file_url":      result["secure_url"],
            "publice":       result["public_id"],
            "file_name":     file.filename,
            "file_size":     result["size"],
            "duration_secs": int(result.get("duration") or 0),
            "reply_to_id":   reply_to_id,
            "is_deleted":    False,
            "is_read":       False,
        })

        staff_name = await self._staff_name(staff_id, company_id)
        label      = "voice note" if is_voice else "audio file"

        await self._publish(group_id, {
            "event":         "new_message",
            "message_id":    message.message_id,
            "group_id":      group_id,
            "sender_id":     staff_id,
            "sender_name":   staff_name,
            "message_type":  msg_type.value,
            "file_url":      result["secure_url"],
            "file_name":     file.filename,
            "file_size":     result["size"],
            "duration_secs": int(result.get("duration") or 0),
            "reply_to_id":   reply_to_id,
            "is_deleted":    False,
            "is_read":       False,
            "created_at":    str(message.timestamp),
        })



        await self._notify_group_members(
            group_id    = group_id,
            company_id  = company_id,
            sender_id   = staff_id,
            sender_name = staff_name,
            title       = f"{staff_name} sent a {label}",
            message     = f"🎙 {label}",
        )

        return message

    # ==========================================================================
    # MESSAGES — FILE
    # ==========================================================================

    async def send_file(
        self,
        group_id:    int,
        file:        UploadFile,
        staff_id:    int,
        company_id:  int,
        reply_to_id: int | None = None,
    ) -> ChatMessage:
        await self._verify_group(group_id, company_id)
        await self._verify_member(group_id, staff_id, company_id)

        result = await storage.upload_file(
            file=file,
            folder=f"chat/{company_id}/{group_id}/files",
        )

        message = await self.repo.create_message({
            "group_id":     group_id,
            "company_id":   company_id,
            "sender_id":    staff_id,
            "message_type": MessageType.file,
            "content":      None,
            "file_url":     result["secure_url"],
            "publice":      result["public_id"],
            "file_name":    file.filename,
            "file_size":    result["size"],
            "reply_to_id":  reply_to_id,
            "is_deleted":   False,
            "is_read":      False,
        })

        staff_name = await self._staff_name(staff_id, company_id)

        await self._publish(group_id, {
            "event":        "new_message",
            "message_id":   message.message_id,
            "group_id":     group_id,
            "sender_id":    staff_id,
            "sender_name":  staff_name,
            "message_type": "file",
            "file_url":     result["secure_url"],
            "file_name":    file.filename,
            "file_size":    result["size"],
            "reply_to_id":  reply_to_id,
            "is_deleted":   False,
            "is_read":      False,
            "created_at":   str(message.timestamp),
        })

        await self._notify_group_members(
            group_id    = group_id,
            company_id  = company_id,
            sender_id   = staff_id,
            sender_name = staff_name,
            title       = f"{staff_name} sent a file",
            message     = f"📎 {file.filename}",
        )

        return message

    # ==========================================================================
    # GET MESSAGES
    # ==========================================================================

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
                "message_id":    m.message_id,
                "group_id":      m.group_id,
                "company_id":    m.company_id,
                "sender_id":     m.sender_id,
                "sender_name":   m.sender.name if m.sender else None,
                "message_type":  m.message_type.value,
                "content":       m.content,
                "file_url":      m.file_url,
                "file_name":     m.file_name,
                "file_size":     m.file_size,
                "duration_secs": m.duration_secs,
                "media_thumbnail": m.media_thumbnail,
                "reply_to_id":   m.reply_to_id,
                "reply_to": {
                    "message_id":  m.reply_to.message_id,
                    "sender_id":   m.reply_to.sender_id,
                    "content":     m.reply_to.content,
                    "message_type": m.reply_to.message_type.value,
                } if m.reply_to else None,
                "is_deleted":    m.is_deleted,
                "is_read":       m.is_read,
                "created_at":    m.timestamp,
            }
            for m in messages
        ]

    # ==========================================================================
    # READ RECEIPTS
    # ==========================================================================

    async def mark_message_read(
        self, message_id: int, staff_id: int, company_id: int
    ) -> dict:
        message = await self.repo.get_message_by_id(message_id, company_id)
        if not message:
            raise HTTPException(404, f"Message id={message_id} not found.")

        await self.repo.mark_message_read(message)

        await self._publish(message.group_id, {
            "event":      "message_read",
            "message_id": message_id,
            "read_by":    staff_id,
            "group_id":   message.group_id,
        })

        return {"message": f"Message id={message_id} marked as read."}

    async def mark_all_read(
        self, group_id: int, staff_id: int, company_id: int
    ) -> dict:
        await self._verify_group(group_id, company_id)
        count = await self.repo.mark_all_read_in_group(group_id, company_id, staff_id)

        await self._publish(group_id, {
            "event":    "all_messages_read",
            "group_id": group_id,
            "read_by":  staff_id,
            "count":    count,
        })

        return {"message": f"{count} messages marked as read."}

    async def get_unread_count(
        self, group_id: int, staff_id: int, company_id: int
    ) -> dict:
        await self._verify_group(group_id, company_id)
        count = await self.repo.get_unread_count(group_id, company_id, staff_id)
        return {"group_id": group_id, "unread_count": count}

    # ==========================================================================
    # DELETE MESSAGE
    # ==========================================================================

    async def delete_message(
        self, message_id: int, staff_id: int, company_id: int
    ) -> dict:
        message = await self.repo.get_message_by_id(message_id, company_id)
        if not message:
            raise HTTPException(404, f"Message id={message_id} not found.")

        if message.sender_id != staff_id:
            raise HTTPException(403, "You can only delete your own messages.")

        # Delete Cloudinary asset if present
        await self._delete_cloudinary_asset(message)

        # Soft delete — keeps row for reply references
        await self.repo.soft_delete_message(message)

        await self._publish(message.group_id, {
            "event":      "message_deleted",
            "message_id": message_id,
            "group_id":   message.group_id,
        })

        return {"message": f"Message id={message_id} deleted."}


# ==============================================================================
# FACTORY
# ==============================================================================

async def get_chat_service(
    db:           AsyncSession = Depends(get_db),
    redis_client: redis.Redis  = Depends(get_redis_client),
) -> ChatService:
    return ChatService(db=db, redis_client=redis_client)