from fastapi import APIRouter
from .chat_router import chat_router         
from .notification_router import notification_router 

router_communication = APIRouter()
router_communication.include_router(chat_router)
router_communication.include_router(notification_router)