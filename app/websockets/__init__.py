from .base_handler import BaseWebSocketHandler
from .chat_handler import ChatWebSocketHandler, publish_chat_message, start_chat_pubsub_listener
from .notification_handler import NotificationWebSocketHandler, publish_notification, start_notification_pubsub_listener

# Global singletons — import these everywhere
chat_handler         = ChatWebSocketHandler()
notification_handler = NotificationWebSocketHandler()
__all__ = [
    "BaseWebSocketHandler",
    "ChatWebSocketHandler",
    "NotificationWebSocketHandler",
    "chat_handler",
    "notification_handler",
    "publish_chat_message",
    "publish_notification",
    "start_chat_pubsub_listener",
    "start_notification_pubsub_listener",
]