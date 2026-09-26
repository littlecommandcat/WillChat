from typing import Any, Awaitable, Callable, TypeVar
import inspect

CallbackT = TypeVar("CallbackT", bound=Callable[..., Awaitable[Any]])


class Command:
    def __init__(
        self,
        callback: Callable[..., Awaitable[Any]],
        *,
        name: str | None = None,
    ):
        self.callback = callback
        self.name = name or callback.__name__

        parameters = inspect.signature(callback).parameters

        for parameter in parameters.values():
            if parameter.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                raise TypeError(
                    f"Command {self.name!r} does not support "
                    f"*args or **kwargs."
                )

        self.parameters = parameters

    async def __call__(self, *args: Any) -> Any:
        return await self.callback(*args)

    def __repr__(self) -> str:
        return f"<Command name={self.name!r} args={len(self.parameters)!r}>"