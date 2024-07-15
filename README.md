# Fastsocket

An experimental, asynchronous WebSocket library for Python.

⚠️ **WARNING**: This library is highly experimental and provided as-is. No support or help will be given for issues. Use at your own risk.

## Features

- Asynchronous WebSocket server and client
- Event-based message handling
- Support for blocking and non-blocking message sending

## Installation

```bash
pip install git+https://github.com/ZegerUser/fastsocket.git
```
## Usage Examples

### Server
```python
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
```
### Client
```python
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
```

## License
This project is licensed under the MIT License.

## This library is experimental and not intended for production use. It is provided as-is, without any warranty or support.