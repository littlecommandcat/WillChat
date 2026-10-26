from collections import defaultdict
import asyncio
import logging

logger = logging.getLogger(__name__)


class EventHandler:
    def __init__(self):
        self._listeners = defaultdict(list)
        self._tasks: set[asyncio.Task] = set()

    def remove_event(self, event) -> list:
        return self._listeners.pop(event, [])

    def add_event(self, event, func) -> None:
        self._listeners[event].append(func)

    async def _run_callback(self, callback, *args, **kwargs):
        try:
            result = callback(*args, **kwargs)

            if asyncio.iscoroutine(result):
                await result

        except asyncio.CancelledError:
            raise

        except Exception:
            logger.exception("Error in event callback: %s", callback)

    def dispatch(self, event, *args, **kwargs) -> None:
        for callback in tuple(self._listeners.get(event, [])):
            task = asyncio.create_task(self._run_callback(callback, *args, **kwargs))

            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

    async def wait_for_tasks(self):
        current = asyncio.current_task()

        tasks = [
            task for task in self._tasks
            if task is not current and not task.done()
        ]

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def clear_tasks(self):
        tasks = list(self._tasks)

        for task in tasks:
            task.cancel()

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        self._tasks.clear()