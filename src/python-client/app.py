import asyncio

from config import EMAIL, PASSWORD
import willclient
from willclient import Message, Group, Member, EventType, commands

client = willclient.Client(command_prefix="!")


@client.listen("ready")
async def on_ready():
    print("WebSocket connected")
    print("Waiting for events; press Ctrl+C to stop")

@client.listen("event")
async def on_event(event: EventType, *args):
    print(f"On event [{event}] -> {args}")

@client.listen("message_send")
async def on_message_send(message: Message, group: Group):
    print("MESSAGE:", message.content, group.name)

@client.listen("message_delete")
async def on_message_delete(message: Message, group: Group):
    print("DELETE:", message.content, group.name)

@client.listen("group_ceate")
async def on_group_join(group: Group, member: Member):
    print("CREATE GROUP:", group, member)

@client.listen("group_delete")
async def on_group_leave(group: Group, member: Member):
    print("DELETE GROUP:", group, member)

@client.listen("group_join")
async def on_group_join(group: Group, member: Member):
    print("JOIN GROUP:", group, member)

@client.listen("group_leave")
async def on_group_leave(group: Group, member: Member):
    print("LEAVE GROUP:", group, member)


@client.listen("error")
async def on_error(error):
    print("WebSocket error:", error)

@client.listen("disconnect")
async def on_disconnect(error):
    print("WebSocket disconnect:", error)

@client.command(name="echo")
async def echo_command(cda: commands.CommandData, msg_data: str):
    try:
        print("=" * 40)
        print(f"""Command '{cda.cmd.name}' from {cda.group.name}({cda.group.id}) attaches <{msg_data}>
Command authorid: {cda.message.authorid}""")
        print("=" * 40)
    except Exception as e:
        print(f"Error: {e}")

async def main():
    async with client:
        await client.start(EMAIL, PASSWORD)


try:
    asyncio.run(main())
except KeyboardInterrupt:
    # asyncio.run(client.close())
    print("WebSocket listener stopped")