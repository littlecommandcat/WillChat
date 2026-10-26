from __future__ import annotations

import asyncio
import json
import urllib.parse

import websockets

from config import EMAIL, PASSWORD, BASE_URL
from .request import RequestManager
from .models import Member, Message, Group, ErrorType
from .commands import Command, CommandHandler
from .events import EventHandler, EventType
from .cache import _cache_base
from .utils import MISSING, is_not_allowed_code, raise_code_error
from .exceptions import *

class Client:
    def __init__(self, *, command_prefix: str = MISSING):
        self._allowed_status = [200, 201, 202, 204]
        self._socket = None
        self._running = False
        self._ready = asyncio.Event()
        self._closed = asyncio.Event()
        self._closed.set()
        self._start_task: asyncio.Task | None = None
        self.command_handler = CommandHandler(command_prefix)
        self.event_handler = EventHandler()
        self._member: Member | None = None

    def __enter__(self) -> None:
        raise TypeError("Use async with instead")
    
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    def _clear_ready(self):
        if self._ready.is_set():
            self._ready.clear()

    @property
    def member(self) -> Member:
        if self._member is None:
            raise UnknownClient("Client is not ready")

        return self._member
    
    def is_running(self) -> bool:
        return self._running

    def is_ready(self) -> bool:
        return self._ready.is_set()

    def command(self, name: str | None = None):
        def decorator(func):
            command_name = name or func.__name__

            command = Command(
                func,
                name=command_name,
            )

            self.command_handler.add_command(command)

            return command

        return decorator

    def listen(self, event):
        def decorator(func):
            self.event_handler.add_event(event, func)
            return func

        return decorator

    def websocket_url(self, token):
        base = (
            BASE_URL
            .replace("http://", "ws://")
            .replace("https://", "wss://")
        )

        query = urllib.parse.urlencode({
            "token": token
        })

        return f"{base}/ws?{query}"

    async def start(self, email: str | None = None, password: str | None = None, *, token: str | None = None):
        if self._running:
            raise RuntimeError("Client is already running")

        self._running = True
        self._closed.clear()
        self._ready.clear()
        self._start_task = asyncio.current_task()
        try:
            _cache_base.init_session()
            if email and password:
                data, token = await RequestManager.login(email, password)
                self._member = Member.from_payload(data)

            if not token:
                raise WillClientUnauthorized("Login failed")

            while self._running:
                try:
                    async with websockets.connect(
                        self.websocket_url(token),
                        origin=BASE_URL,
                        ping_interval=None
                    ) as socket:
                        self._socket = socket

                        async for raw_event in socket:
                            if not self._running:
                                break

                            try:
                                event = json.loads(raw_event)

                                if not isinstance(event, dict):
                                    continue

                            except json.JSONDecodeError:
                                print("Invalid WebSocket event:", raw_event)
                                continue

                            event_type = event.get("event")
                            payload = event.get("payload")

                            if not event_type:
                                continue

                            try:
                                event_type = EventType(event_type)
                            except ValueError:
                                event_type = EventType.OTHER

                            # READY
                            if event_type == EventType.READY:
                                if not self._ready.is_set():
                                    self._member = Member.from_payload(payload)
                                    self._ready.set()

                            # Not READY
                            elif not self._ready.is_set():
                                continue

                            if not isinstance(payload, dict):
                                payload = {}

                            payload_data = {}

                            if payload.get("member"):
                                payload_data["member"] = Member.from_payload(payload["member"])

                            if payload.get("message"):
                                payload_data["message"] = Message.from_payload(payload["message"])

                            if payload.get("group"):
                                payload_data["group"] = Group.from_payload(payload["group"])

                            # COMMAND
                            if event_type == EventType.MESSAGE_SEND:
                                message: Message = payload_data.get("message")
                                group: Group = payload_data.get("group")

                                if message is not None and group is not None and message.authorid != self._member.id:
                                    self.command_handler._process_command(message, group)

                            # EVENTS
                            self.event_handler.dispatch(
                                EventType.EVENT,
                                event_type,
                                payload,
                                payload_data
                            )

                            self.event_handler.dispatch(event_type, **payload_data)

                except asyncio.CancelledError:
                    raise

                except websockets.ConnectionClosed as error:
                    self.event_handler.dispatch(EventType.DISCONNECT, error)

                except Exception as error:
                    self.event_handler.dispatch(EventType.ERROR, error)

                finally:
                    self._ready.clear()
                    self._socket = None
                    self._member = None

                if self._running:
                    await asyncio.sleep(3)

        finally:
            self._running = False
            self._ready.clear()
            self._socket = None
            self._member = None
            self._closed.set()
            self._start_task = None
            await self.event_handler.clear_tasks()
            self.event_handler.dispatch(EventType.CLOSE)
            await self.event_handler.wait_for_tasks()
            if not RequestManager.closed:
                await RequestManager.close()

    async def close(self):
        self._running = False
        self._ready.clear()
        self._closed.set()

        if self._socket is not None:
            await self._socket.close()

        task = self._start_task

        if task is not None and task is not asyncio.current_task():
            task.cancel()

            await asyncio.gather(task, return_exceptions=True)

        if not RequestManager.closed:
            await RequestManager.close()

    # Refer to discord.py
    async def wait_until_ready(self):
        if self.is_ready():
            return

        if not self._running:
            raise UnknownClient("Client is not running")

        while not self._ready.is_set():
            if self._closed.is_set():
                raise UnknownClient("Client has been closed")
            ready_task = asyncio.create_task(self._ready.wait())
            closed_task = asyncio.create_task(self._closed.wait())
            try:
                done, pending = await asyncio.wait(
                    [ready_task, closed_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
            finally:
                for task in (ready_task, closed_task):
                    if not task.done():
                        task.cancel()

                await asyncio.gather(
                    ready_task,
                    closed_task,
                    return_exceptions=True
                )

            if self._closed.is_set():
                raise UnknownClient("Client closed before becoming ready")

            if self._ready.is_set():
                return

    async def fetch_group(self, group_id: str) -> Group:
        resp, body = await RequestManager.get(f"/api/groups/{group_id}", headers={"Authorization": f"{RequestManager.token}"})
        if is_not_allowed_code(resp.status):
            raise_code_error(resp.status, ErrorType.GROUP)

        if not isinstance(body, dict):
            raise UnexpectedBody(f"Return unexcepted response body")

        try:
            group = Group.from_payload(body)
        except:
            raise UnexpectedBody(f"Return unexcepted response body")

        return group

    async def fetch_member(self, group_id: str, member_id: str) -> Member:
        resp, body = await RequestManager.get(f"/api/groups/{group_id}/members/{member_id}", headers={"Authorization": f"{RequestManager.token}"})
        if is_not_allowed_code(resp.status):
            raise_code_error(resp.status, ErrorType.MEMBER)
    
        if not isinstance(body, dict):
            raise UnexpectedBody(f"Return unexcepted response body")
    
        try:
            member = Member.from_payload(body)
        except:
            raise UnexpectedBody(f"Return unexcepted response body")
    
        return member

    async def fetch_message(self, group_id: str, message_id: str) -> Message:
        resp, body = await RequestManager.get(f"/api/groups/{group_id}/messages", headers={"Authorization": f"{RequestManager.token}"}, params={"message_id": message_id})
        if is_not_allowed_code(resp.status):
            raise_code_error(resp.status, ErrorType.MESSAGE)
    
        if not isinstance(body, dict):
            raise UnexpectedBody(f"Return unexcepted response body")
    
        try:
            message = Message.from_payload(body)
        except:
            raise UnexpectedBody(f"Return unexcepted response body")
    
        return message

    async def fetch_bulk_message(self, group_id: str, amount: int) -> list[Message]:
        resp, body = await RequestManager.get(f"/api/groups/{group_id}/messages", headers={"Authorization": f"{RequestManager.token}"}, params={"amount": amount})
        if is_not_allowed_code(resp.status):
            raise_code_error(resp.status, ErrorType.GROUP)
    
        if not isinstance(body, dict):
            raise UnexpectedBody(f"Return unexcepted response body")

        message_list: list[Message] = []
        try:
            messages_body = body.get("data", {}).get("messages", [])
            for mbody in messages_body:
                message_list.append(Message.from_payload(mbody))
        except:
            raise UnexpectedBody(f"Return unexcepted response body")
    
        return message_list