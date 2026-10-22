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
    def __init__(self, *, command_prefix: str=MISSING):
        self._allowed_status = [200, 201, 202, 204]
        self._socket = None
        self._running = False
        self.command_handler = CommandHandler(command_prefix)
        self.event_handler = EventHandler()

    def __enter__(self) -> None:
        raise TypeError("Use async with instead")
    
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    # def is_running(self) -> bool:
    #     return self._running

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

    async def start(self, email: str=None, password: str=None, *, token: str=None):
        _cache_base.init_session()
        self._running = True
        if email and password:
            data, token = await RequestManager.login(email, password)
            # print(data, token)

        if not token:
            self._running = False
            raise RuntimeError("Login failed")

        while self._running:
            try:
                async with websockets.connect(
                    self.websocket_url(token),
                    origin=BASE_URL,
                    ping_interval=None
                ) as socket:
                    self._socket = socket

                    await self.event_handler.dispatch("ready")

                    async for raw_event in socket:
                        try:
                            event = json.loads(raw_event)
                        except json.JSONDecodeError:
                            print("Invalid WebSocket event:", raw_event)
                            continue

                        # print(event)
                        event_type: str | None = event.get("event")
                        payload = event.get("payload")

                        if not event_type:
                            continue

                        # print(payload)

                        payload_data = {}
                        if payload.get("member", {}):
                            payload_data["member"] = Member.from_payload(payload.get("member", {}))
                            
                        if payload.get("message", {}):
                            payload_data["message"] = Message.from_payload(payload)

                        if payload.get("group", {}):
                            payload_data["group"] = Group.from_payload(payload.get("group", {}))

                        try:
                            event_type = EventType(event_type)
                        except:
                            event_type = EventType.OTHER

                        if event_type == EventType.MESSAGE_SEND:
                            await self.command_handler._process_command(payload_data["message"], payload_data["group"])

                        await self.event_handler.dispatch("event", event_type, payload, payload_data)
                        # print("event", event_type, payload, **payload_data)
                        await self.event_handler.dispatch(event_type, **payload_data)

            except asyncio.CancelledError:
                raise

            except websockets.ConnectionClosed as error:
                await self.event_handler.dispatch("disconnect", error)

                if self._running:
                    await asyncio.sleep(3)

            except Exception as error:
                # traceback.print_exc()
                await self.event_handler.dispatch("error", error)

                if self._running:
                    await asyncio.sleep(3)

            finally:
                self._socket = None

    async def close(self):
        self._running = False

        if self._socket is not None:
            await self._socket.close()

        if not RequestManager.closed:
            await RequestManager.close()


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