from fastsocket import Server, Message
import asyncio
import logging

async def handle_ping(msg: Message, ws):
    response = Message(msg.uuid, "PONG", {"data": "Hello from server!"})
    await ws.send(response.to_json())

async def main():
    server = Server("localhost", 8765, log_level=logging.INFO)
    server.on_message("PING", handle_ping)
    
    async with server:
        await asyncio.Future()  # Run forever

asyncio.run(main())