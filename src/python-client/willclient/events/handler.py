from collections import defaultdict
import asyncio

class EventHandler:
    def __init__(self):
        self._listeners = defaultdict(list)

    def remove_event(self, event) -> list:
        return self._listeners.pop(event, [])
    
    def add_event(self, event, func) -> None:
        self._listeners[event].append(func)

    async def dispatch(self, event, *args, **kwargs) -> None:
        for callback in self._listeners.get(event, []):
            result = callback(*args, **kwargs)

            if asyncio.iscoroutine(result):
                await result