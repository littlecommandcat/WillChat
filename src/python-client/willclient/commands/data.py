from __future__ import annotations

from .core import Command
from ..models import Message, Group

class CommandData:
    def __init__(self, cmd: Command, message: Message, group: Group):
        self.cmd: Command = cmd
        self.message: Message = message
        self.group: Group = group