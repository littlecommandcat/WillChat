from ..objects import Message, Group
from .core import Command

class CommandData:
    def __init__(self, cmd: Command, message: Message, group: Group):
        self.cmd: Command = cmd
        self.message: Message = message
        self.group: Group = group