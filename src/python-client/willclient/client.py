import asyncio
import json
import urllib.parse

import websockets

from config import EMAIL, PASSWORD, BASE_URL
from .request import Requester
from .objects import Member, Message, Group, _Missing, MISSING
from .enums import EventType
from .commands import Command, CommandHandler
from .events import EventHandler
from .exceptions import *

class Client:
    def __init__(self, *, command_prefix: str | _Missing=MISSING):
        self._allowed_status = [200, 201, 202, 204]
        self._socket = None
        self._running = False
        self._requester = Requester()
        self._command_handler = CommandHandler(command_prefix)
        self._event_handler = EventHandler()

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

            self._command_handler._add_command(command)

            return command

        return decorator

    def listen(self, event):
        def decorator(func):
            self._event_handler._add_event(event, func)
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
        self._requester._init_session()
        self._running = True
        if email and password:
            data, token = await self._requester.login(email, password)
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

                    await self._event_handler._dispatch("ready")

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
                            payload_data["message"] = Message.from_payload(payload.get("message", {}))

                        if payload.get("group", {}):
                            payload_data["group"] = Group.from_payload(payload.get("group", {}))

                        try:
                            event_type = EventType(event_type)
                        except:
                            event_type = EventType.OTHER

                        if event_type == EventType.MESSAGE_SEND:
                            await self._command_handler._process_command(payload_data["message"], payload_data["group"])

                        await self._event_handler._dispatch("event", event_type, payload, payload_data)
                        # print("event", event_type, payload, **payload_data)
                        await self._event_handler._dispatch(event_type, **payload_data)

            except asyncio.CancelledError:
                raise

            except websockets.ConnectionClosed as error:
                await self._event_handler._dispatch("disconnect", error)

                if self._running:
                    await asyncio.sleep(3)

            except Exception as error:
                # traceback.print_exc()
                await self._event_handler._dispatch("error", error)

                if self._running:
                    await asyncio.sleep(3)

            finally:
                self._socket = None

    async def close(self):
        self._running = False

        if self._socket is not None:
            await self._socket.close()

        if not self._requester.closed:
            await self._requester.close()


    async def fetch_group(self, group_id: str) -> Group:
        resp, body = await self._requester.get(f"/api/groups/{group_id}", headers={"Authorization": f"{self._requester.token}"})
        if resp.status == 404:
            raise UnknownMember(f"Unknow group id: {group_id}")
        
        if resp.status not in self._allowed_status:
            raise UnexpectedStatus(f"Return unexcepted status code: {resp.status}")

        if not isinstance(body, dict):
            raise UnexpectedBody(f"Return unexcepted response body")

        try:
            group = Group.from_payload(body)
        except:
            raise UnexpectedBody(f"Return unexcepted response body")

        return group

    async def fetch_member(self, group_id: str, member_id: str) -> Member:
        resp, body = await self._requester.get(f"/api/groups/{group_id}/members/{member_id}", headers={"Authorization": f"{self._requester.token}"})
        if resp.status == 404:
            raise UnknownMember(f"Unknow group or member id: {group_id}/{member_id}")
        
        if resp.status not in self._allowed_status:
            raise UnexpectedStatus(f"Return unexcepted status code: {resp.status}")
    
        if not isinstance(body, dict):
            raise UnexpectedBody(f"Return unexcepted response body")
    
        try:
            member = Member.from_payload(body)
        except:
            raise UnexpectedBody(f"Return unexcepted response body")
    
        return member

    async def fetch_message(self, group_id: str, message_id: str) -> Message:
        resp, body = await self._requester.get(f"/api/groups/{group_id}/messages", headers={"Authorization": f"{self._requester.token}"}, params={"message_id": message_id})
        if resp.status == 404:
            raise UnknownMessage(f"Unknow group or message id: {group_id}/{message_id}")
        
        if resp.status not in self._allowed_status:
            raise UnexpectedStatus(f"Return unexcepted status code: {resp.status}")
    
        if not isinstance(body, dict):
            raise UnexpectedBody(f"Return unexcepted response body")
    
        try:
            message = Message.from_payload(body)
        except:
            raise UnexpectedBody(f"Return unexcepted response body")
    
        return message

    async def fetch_bulk_message(self, group_id: str, amount: int) -> list[Message]:
        resp, body = await self._requester.get(f"/api/groups/{group_id}/messages", headers={"Authorization": f"{self._requester.token}"}, params={"amount": amount})
        print(resp, body)
        if resp.status == 404:
            raise UnknownGroup(f"Unknow group id: {group_id}")
        
        if resp.status not in self._allowed_status:
            raise UnexpectedStatus(f"Return unexcepted status code: {resp.status}")
    
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