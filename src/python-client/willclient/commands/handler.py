import inspect

from ..objects import Message, Group, _Missing, MISSING
from .core import Command
from .data import CommandData


class CommandHandler:
    def __init__(self, command_prefix: str | _Missing):
        self._commands: dict[str, Command] = {}
        self._command_prefix: str | _Missing = command_prefix

    def __validate_command(self, command: Command) -> None:
        parameters = list(command.parameters.values())

        if not parameters:
            raise TypeError(
                f"Command {command.name!r} must have "
                f"CommandData as its first parameter."
            )

        if parameters[0].annotation is not CommandData:
            raise TypeError(
                f"Command {command.name!r} must have "
                f"CommandData as its first parameter."
            )

        keyword_only = [
            p
            for p in parameters[1:]
            if p.kind == inspect.Parameter.KEYWORD_ONLY
        ]

        if len(keyword_only) > 1:
            raise TypeError(
                f"Command {command.name!r} can only have "
                f"one keyword-only parameter."
            )
            
    def _remove_command(self, command: Command) -> Command:
        if command.name not in self._commands:
            raise ValueError(
                f"Command {command.name!r} is not registered."
            )

        return self._commands.pop(command.name)

    def _add_command(self, command: Command) -> Command:
        if command.name in self._commands:
            raise ValueError(
                f"Command {command.name!r} is already registered."
            )

        self.__validate_command(command)

        self._commands[command.name] = command
        return command

    async def _process_command(self, message: Message, group: Group) -> None:
        content = message.content.strip()

        if self._command_prefix:
            if not content.startswith(self._command_prefix):
                return

            content = content[len(self._command_prefix):].strip()

        parts = content.split()

        if not parts:
            return

        command_name = parts[0]
        args = parts[1:]

        command = self._commands.get(command_name)

        if command is None:
            return

        parameters = list(command.parameters.values())

        # self.__validate_command(command)

        # command_data_parameter = parameters[0]

        # if command_data_parameter.annotation is not CommandData:
        #     raise TypeError(
        #         f"Command {command.name!r} must have "
        #         f"CommandData as its first parameter."
        #     )

        user_parameters = parameters[1:]

        positional = [
            p for p in user_parameters
            if p.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]

        keyword_only = [
            p for p in user_parameters
            if p.kind == inspect.Parameter.KEYWORD_ONLY
        ]

        required = sum(
            p.default is inspect.Parameter.empty
            for p in positional
        )

        if len(args) < required:
            return

        positional_count = len(positional)

        positional_args = args[:positional_count]
        remaining = args[positional_count:]

        kwargs = {}

        if keyword_only:
            last = keyword_only[-1]

            if remaining:
                kwargs[last.name] = " ".join(remaining)
            elif last.default is inspect.Parameter.empty:
                return

        # elif remaining:
        #     return

        command_data = CommandData(cmd=command, message=message, group=group)

        await command(command_data, *positional_args, **kwargs)