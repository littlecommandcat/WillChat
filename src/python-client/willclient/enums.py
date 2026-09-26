from enum import Enum


class MessageType(Enum):
    NORMAL = 0
    REFRENCE = 1
    DEV = 2
    OTHER = 3

class EventType(str, Enum):
    MESSAGE_SEND = "message_send"
    MESSAGE_DELETE = "message_delete"

    GROUP_CREATE = "group_create"
    GROUP_DELETE = "group_delete"
    GROUP_JOIN = "group_join"
    GROUP_LEAVE = "group_leave"

    EVENT = "event"
    ERROR = "error"
    OTHER = "other"