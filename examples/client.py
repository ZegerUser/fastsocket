from fastsocket import Client, Message
import asyncio
import logging

async def main():
    async with Client("ws://localhost:8765") as client:
        # Non-blocking send
        await client.send_msg(Message(1, "PING", {"data": "Hello"}))
        
        # Blocking send with timeout
        response = await client.send_msg(Message(2, "PING", {"data": "Hello"}), blocking=True, timeout=5.0)
        if response:
            print(f"Received response: {response.data}")
        else:
            print("No response received within the timeout period")

        # Using event handler
        @client.on("PONG")
        def handle_pong(msg):
            print(f"Received PONG: {msg.data}")

        await asyncio.sleep(10)  # Keep connection open for a while

asyncio.run(main())