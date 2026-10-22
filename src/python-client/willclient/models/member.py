from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from .group import Group

@dataclass
class Member:
    name: str
    id: str = id
    groups: list["Group"]
    block: list
    read: dict[str, str]

    @classmethod
    def from_payload(cls, payload: dict) -> "Member":
        member_payload = payload["payload"]["member"] if "payload" in payload else payload

        groups = [
            Group(
                name=group.get("name", ""),
                group_id=group.get("group_id", ""),
                owner_id=group.get("owner_id", ""),
                created_at=group.get("created_at", ""),
            )
            for group in member_payload.get("groups", [])
        ]

        return cls(
            name=member_payload.get("name", ""),
            id=member_payload.get("id", ""),
            groups=groups,
            block=member_payload.get("block", []),
            read=member_payload.get("read", {}),
        )