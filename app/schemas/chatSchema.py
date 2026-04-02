from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.chat.chat_group import ChatType
from app.models.chat.chat_message import  MessageType





# ===========================================================================
# GROUP SCHEMAS
# ===========================================================================

class ChatGroupCreate(BaseModel):
    group_name:       str       = Field(..., min_length=1, max_length=150)
    chat_type:  ChatType  = ChatType.group
    member_ids: List[int] = Field(..., min_length=1, description="List of staff_ids to add")

    class Config:
        json_schema_extra = {
            "example": {
                "group_name":       "Engineering Team",
                "chat_type":  "group",
                "member_ids": [1, 2, 3]
            }
        }


class DirectMessageCreate(BaseModel):
    """Create a direct message chat between two staff members."""
    staff_id: int = Field(..., description="staff_id to start DM with")

    class Config:
        json_schema_extra = {"example": {"staff_id": 2}}







class ChatGroupResponse(BaseModel):
    group_id:   int
    company_id: int
    group_name:       str
    chat_type:  str
    created_by: int
    is_active:  bool
    created_at: datetime
    member_count: Optional[int] = None

    class Config:
        from_attributes = True


class AddMemberRequest(BaseModel):
    staff_ids: List[int] = Field(..., min_length=1)


class RemoveMemberRequest(BaseModel):
    staff_id: int


# ===========================================================================
# MESSAGE SCHEMAS
# ===========================================================================

class SendMessageRequest(BaseModel):
    content:      Optional[str] = None
    message_type: MessageType   = MessageType.text

    class Config:
        json_schema_extra = {
            "example": {
                "content":      "Hello team!",
                "message_type": "text"
            }
        }


class ChatMessageResponse(BaseModel):
    message_id:   int
    group_id:     int
    company_id:   int
    sender_id:    int
    sender_name:  Optional[str] = None
    message_type: str
    content:      Optional[str] = None
    file_url:     Optional[str] = None
    file_name:    Optional[str] = None
    file_size:    Optional[int] = None
    is_deleted:   bool
    created_at:   datetime

    class Config:
        from_attributes = True


class ChatMemberResponse(BaseModel):
    member_id:  int
    group_id:   int
    staff_id:   int
    company_id: int
    joined_at:  datetime
    is_admin:   bool
    staff_name: Optional[str] = None

    class Config:
        from_attributes = True