from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import Optional

from app.models.chat import ChatGroup, ChatGroupMember, ChatMessage
from app.models.chat.chat_group import  ChatType

class ChatRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    # -----------------------------------------------------------------------
    # GROUPS
    # -----------------------------------------------------------------------

    async def get_group_by_id(
        self, group_id: int, company_id: int
    ) -> ChatGroup | None:
        result = await self.db.execute(
            select(ChatGroup)
            .options(
                selectinload(ChatGroup.members),
                selectinload(ChatGroup.creator),
            )
            .where(
                ChatGroup.group_id   == group_id,
                ChatGroup.company_id == company_id,
                ChatGroup.is_active  == True,
            )
        )
        return result.scalar_one_or_none()
    
    # ============================================================


    async def get_my_groups(
        self, staff_id: int, company_id: int
    ) -> list[ChatGroup]:
        """Get all groups this staff member belongs to."""
        result = await self.db.execute(
            select(ChatGroup)
            .join(
                ChatGroupMember,
                and_(
                    ChatGroupMember.group_id   == ChatGroup.group_id,
                    ChatGroupMember.staff_id   == staff_id,
                    ChatGroupMember.company_id == company_id,
                )
            )
            .where(
                ChatGroup.company_id == company_id,
                ChatGroup.is_active  == True,
            )
            .order_by(ChatGroup.created_at.desc())
        )
        return result.scalars().all()

    async def get_all_groups(self, company_id: int) -> list[ChatGroup]:
        """Manager: get all groups in company."""
        result = await self.db.execute(
            select(ChatGroup)
            .where(
                ChatGroup.company_id == company_id,
                ChatGroup.is_active  == True,
            )
            .order_by(ChatGroup.created_at.desc())
        )
        return result.scalars().all()

    async def find_direct_chat(
        self, staff_id_1: int, staff_id_2: int, company_id: int
    ) -> ChatGroup | None:
        """Find existing DM between two staff members."""
        result = await self.db.execute(
            select(ChatGroup)
            .join(ChatGroupMember, ChatGroupMember.group_id == ChatGroup.group_id)
            .where(
                ChatGroup.company_id == company_id,
                ChatGroup.chat_type  == ChatType.direct,
                ChatGroup.is_active  == True,
                ChatGroupMember.staff_id.in_([staff_id_1, staff_id_2]),
            )
            .group_by(ChatGroup.group_id)
            .having(func.count(ChatGroupMember.staff_id) == 2)
        )
        return result.scalar_one_or_none()



    async def create_group(self, data: dict) -> ChatGroup:
        group = ChatGroup(**data)
        self.db.add(group)
        await self.db.flush()
        return group
    



    async def update_group(self, group: ChatGroup, data: dict) -> ChatGroup:
        for k, v in data.items():
            setattr(group, k, v)
        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def delete_group(self, group: ChatGroup) -> None:
        group.is_active = False
        await self.db.commit()

    # -----------------------------------------------------------------------
    # MEMBERS
    # -----------------------------------------------------------------------

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
    

    
    
    async def get_members(
        self, group_id: int, company_id: int
    ) -> list[ChatGroupMember]:
        result = await self.db.execute(
            select(ChatGroupMember)
            .options(selectinload(ChatGroupMember.staff))
            .where(
                ChatGroupMember.group_id   == group_id,
                ChatGroupMember.company_id == company_id,
            )
        )
        return result.scalars().all()


    async def add_member(self, data: dict) -> ChatGroupMember:
        member = ChatGroupMember(**data)
        self.db.add(member)
        await self.db.flush()
        return member

    async def remove_member(self, member: ChatGroupMember) -> None:
        await self.db.delete(member)
        await self.db.flush()




    # -----------------------------------------------------------------------
    # MESSAGES
    # -----------------------------------------------------------------------

    async def get_messages(
        self,
        group_id:   int,
        company_id: int,
        skip:       int = 0,
        limit:      int = 50,
    ) -> list[ChatMessage]:
        """Get messages — newest first, paginated."""
        result = await self.db.execute(
            select(ChatMessage)
            .options(selectinload(ChatMessage.sender))
            .where(
                ChatMessage.group_id   == group_id,
                ChatMessage.company_id == company_id,
                ChatMessage.is_deleted == False,
            )
            .order_by(ChatMessage.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_message_by_id(
        self, message_id: int, company_id: int
    ) -> ChatMessage | None:
        result = await self.db.execute(
            select(ChatMessage).where(
                ChatMessage.message_id == message_id,
                ChatMessage.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_message(self, data: dict) -> ChatMessage:
        message = ChatMessage(**data)
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def delete_message(self, message: ChatMessage) -> None:
        """Soft delete — keep record but hide content."""
        message.is_deleted = True
        message.content    = None
        message.file_url   = None
        await self.db.commit()



        

    async def commit(self) -> None:
        await self.db.commit()