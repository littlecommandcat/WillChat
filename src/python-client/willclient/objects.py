from typing import Any
from dataclasses import dataclass

from .enums import MessageType


@dataclass
class Group:
    name: str
    id: str
    owner_id: str
    created_at: int

    @classmethod
    def from_payload(cls, payload: dict) -> "Group":
        data = payload["data"]["group"] if "data" in payload else payload

        return cls(
            name=data["name"],
            id=data["group_id"],
            owner_id=data["owner_id"],
            created_at=data["created_at"],
        )


@dataclass
class Member:
    name: str
    id: str
    groups: list[Group]
    block: list
    read: dict[str, str]

    @classmethod
    def from_payload(cls, payload: dict) -> "Member":
        data = payload["data"]["member"] if "data" in payload else payload

        groups = [
            Group(
                name=group.get("name", ""),
                group_id=group.get("group_id", ""),
                owner_id=group.get("owner_id", ""),
                created_at=group.get("created_at", ""),
            )
            for group in data.get("groups", [])
        ]

        return cls(
            name=data["name"],
            id=data["id"],
            groups=groups,
            block=data.get("block", []),
            read=data.get("read", {}),
        )


@dataclass
class Message:
    authorid: str
    content: str
    timestamp: int
    type: MessageType

    @classmethod
    def from_payload(cls, payload: dict) -> "Message":
        data =  payload["data"]["message"] if "data" in payload else payload
        try:
            message_type = MessageType(data["type"])
        except:
            message_type = MessageType.OTHER

        return cls(
            authorid=data["authorid"],
            content=data["content"],
            timestamp=data["timestamp"],
            type=message_type,
        )

class _Missing:
    __slots__ = ()

    def __eq__(self, other) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __hash__(self) -> int:
        return 0

    def __repr__(self):
        return '...'

MISSING: Any = _Missing()