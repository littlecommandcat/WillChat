from collections import defaultdict
import asyncio

class EventHandler:
    def __init__(self):
        self._listeners = defaultdict(list)

    async def _dispatch(self, event, *args, **kwargs):
        for callback in self._listeners.get(event, []):
            result = callback(*args, **kwargs)

            if asyncio.iscoroutine(result):
                await result