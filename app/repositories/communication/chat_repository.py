from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload

from app.models.chat.chat_message import ChatMessage
from app.models.chat.chat_group import ChatGroup, ChatType
from app.models.chat.chat_group_member import ChatGroupMember


class ChatRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==========================================================================
    # COMMIT
    # ==========================================================================

    async def commit(self):
        await self.db.commit()

    # ==========================================================================
    # GROUPS
    # ==========================================================================

    async def create_group(self, payload: dict) -> ChatGroup:
        obj = ChatGroup(**payload)
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def get_group_by_id(self, group_id: int, company_id: int) -> ChatGroup | None:
        result = await self.db.execute(
            select(ChatGroup).where(
                ChatGroup.group_id   == group_id,
                ChatGroup.company_id == company_id,
                ChatGroup.is_active  == True,
            )
        )
        return result.scalar_one_or_none()
    


    async def get_all_groups(self, company_id: int) -> list[ChatGroup]:
        result = await self.db.execute(
            select(ChatGroup).where(
                ChatGroup.company_id == company_id,
                ChatGroup.is_active  == True,
            ).order_by(ChatGroup.group_id.desc())
        )
        return result.scalars().all()
    



    async def get_my_groups(self, staff_id: int, company_id: int) -> list[ChatGroup]:
        result = await self.db.execute(
            select(ChatGroup)
            .join(ChatGroupMember, ChatGroupMember.group_id == ChatGroup.group_id)
            .where(
                ChatGroupMember.staff_id   == staff_id,
                ChatGroupMember.company_id == company_id,
                ChatGroup.is_active   == True,
            )
            .order_by(ChatGroup.group_id.desc())
        )
        return result.scalars().all()

    async def find_direct_chat(
        self, staff_id_a: int, staff_id_b: int, company_id: int
    ) -> ChatGroup | None:
        """Find existing 1-to-1 DM group between two staff members."""
        subq_a = (
            select(ChatGroupMember.group_id)
            .where(ChatGroupMember.staff_id == staff_id_a, ChatGroupMember.company_id == company_id)
            .scalar_subquery()
        )
        subq_b = (
            select(ChatGroupMember.group_id)
            .where(ChatGroupMember.staff_id == staff_id_b, ChatGroupMember.company_id == company_id)
            .scalar_subquery()
        )
        result = await self.db.execute(
            select(ChatGroup).where(
                ChatGroup.chat_type   == ChatType.direct,
                ChatGroup.company_id  == company_id,
                ChatGroup.group_id.in_(subq_a),
                ChatGroup.group_id.in_(subq_b),
            )
        )
        return result.scalar_one_or_none()

    async def delete_group(self, group: ChatGroup) -> None:
        await self.db.delete(group)
        await self.db.commit()

    # ==========================================================================
    # MEMBERS
    # ==========================================================================

    async def add_member(self, payload: dict) -> ChatGroupMember:
        obj = ChatGroupMember(**payload)
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def get_member(
        self, group_id: int, staff_id: int, company_id: int
    ) -> ChatGroupMember | None:
        result = await self.db.execute(
            select(ChatGroupMember).where(
                ChatGroupMember.group_id   == group_id,
                ChatGroupMember.staff_id   == staff_id,
                ChatGroupMember.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_members(self, group_id: int, company_id: int) -> list[ChatGroupMember]:
        result = await self.db.execute(
            select(ChatGroupMember)
            .options(selectinload(ChatGroupMember.staff))
            .where(
                ChatGroupMember.group_id   == group_id,
                ChatGroupMember.company_id == company_id,
            )
        )
        return result.scalars().all()

    async def remove_member(self, member: ChatGroupMember) -> None:
        await self.db.delete(member)

    # ==========================================================================
    # MESSAGES
    # ==========================================================================

    async def create_message(self, payload: dict) -> ChatMessage:
        obj = ChatMessage(**payload)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_message_by_id(
        self, message_id: int, company_id: int
    ) -> ChatMessage | None:
        result = await self.db.execute(
            select(ChatMessage)
            .options(selectinload(ChatMessage.sender))
            .where(
                ChatMessage.message_id == message_id,
                ChatMessage.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_messages(
        self,
        group_id:   int,
        company_id: int,
        skip:       int = 0,
        limit:      int = 50,
    ) -> list[ChatMessage]:
        result = await self.db.execute(
            select(ChatMessage)
            .options(
                selectinload(ChatMessage.sender),
                selectinload(ChatMessage.reply_to),   # load replied message
            )
            .where(
                ChatMessage.group_id   == group_id,
                ChatMessage.company_id == company_id,
            )
            .order_by(ChatMessage.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_all_file_messages(
        self, group_id: int, company_id: int
    ) -> list[ChatMessage]:
        """Used when deleting a group — fetch all messages with Cloudinary assets."""
        result = await self.db.execute(
            select(ChatMessage).where(
                ChatMessage.group_id   == group_id,
                ChatMessage.company_id == company_id,
                ChatMessage.publice    != None,   # noqa: E711 — SQLAlchemy IS NOT NULL
            )
        )
        return result.scalars().all()

    async def soft_delete_message(self, message: ChatMessage) -> ChatMessage:
        """Mark as deleted — content hidden but row stays for reply references."""
        message.is_deleted = True
        message.content    = None
        message.file_url   = None
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def delete_message(self, message: ChatMessage) -> None:
        """Hard delete — use only when no replies reference this message."""
        await self.db.delete(message)
        await self.db.commit()

    # ==========================================================================
    # READ RECEIPTS
    # ==========================================================================

    async def mark_message_read(self, message: ChatMessage) -> ChatMessage:
        message.is_read = True
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def mark_all_read_in_group(
        self, group_id: int, company_id: int, sender_id: int
    ) -> int:
        """Mark all unread messages in a group as read (excluding own messages)."""
        result = await self.db.execute(
            update(ChatMessage)
            .where(
                ChatMessage.group_id   == group_id,
                ChatMessage.company_id == company_id,
                ChatMessage.sender_id  != sender_id,
                ChatMessage.is_read    == False,
                ChatMessage.is_deleted == False,
            )
            .values(is_read=True)
        )
        await self.db.commit()
        return result.rowcount

    async def get_unread_count(
        self, group_id: int, company_id: int, sender_id: int
    ) -> int:
        result = await self.db.execute(
            select(func.count()).where(
                ChatMessage.group_id   == group_id,
                ChatMessage.company_id == company_id,
                ChatMessage.sender_id  != sender_id,
                ChatMessage.is_read    == False,
                ChatMessage.is_deleted == False,
            )
        )
        return result.scalar_one()