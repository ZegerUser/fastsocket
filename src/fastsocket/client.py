import asyncio
import json
import logging
from typing import Dict, List, Callable, Any
import websockets

from .message import Message
from .utils import setup_logger

class Client:
    """
    A WebSocket client for handling asynchronous communication.

    This class provides methods to connect to a WebSocket server, send and receive messages,
    and register event handlers for different message codes.
    """

    def __init__(self, url: str, log_level=logging.INFO):
        """
        Initialize the Client.

        Args:
            url (str): The WebSocket server URL to connect to.
            log_level (int, optional): The logging level. Defaults to logging.INFO.
        """
        self._url = url
        self._registed_callbacks: Dict[str, List[Callable]] = {}
        self._logger, _ = setup_logger("Client", log_level)
        self._websocket = None
        self._response_futures: Dict[int, asyncio.Future] = {}

    def on_message(self, code: str, func: Callable):
        """
        A function for registering event handlers for specific message codes.

        Args:
            code (str): The message code to register the handler for.
            func (Callable): The function to run.
        """
        if code not in self._registed_callbacks:
            self._registed_callbacks[code] = []
        self._registed_callbacks[code].append(func)

    def on(self, code: str):
        """
        Decorator for registering event handlers for specific message codes.

        Args:
            code (str): The message code to register the handler for.

        Returns:
            Callable: The decorator function.
        """
        def decorator(func: Callable):
            if code not in self._registed_callbacks:
                self._registed_callbacks[code] = []
            self._registed_callbacks[code].append(func)
            return func
        return decorator

    async def connect(self):
        """
        Connect to the WebSocket server and start the message handler.
        """
        self._websocket = await websockets.connect(self._url)
        self._logger.info(f"Connected to server at {self._url}")
        asyncio.create_task(self._message_handler())

    async def disconnect(self):
        """
        Disconnect from the WebSocket server.
        """
        if self._websocket:
            await self._websocket.close()
            self._logger.info("Disconnected from server")

    async def _message_handler(self):
        """
        Handle incoming messages from the WebSocket server.
        """
        try:
            async for message in self._websocket:
                await self._process_message(message)
        except websockets.exceptions.ConnectionClosed:
            self._logger.info("Connection to server closed")

    async def _process_message(self, message: str):
        """
        Process an incoming message.

        Args:
            message (str): The raw message string received from the server.
        """
        try:
            msg = Message.from_json(message)
            await self._dispatch_message(msg)

            if msg.uuid in self._response_futures:
                self._response_futures[msg.uuid].set_result(msg)

        except Exception as e:
            self._logger.error(f"Error processing message ({message}): {e}")

    async def _dispatch_message(self, msg: Message):
        """
        Dispatch a message to registered event handlers.

        Args:
            msg (Message): The message to dispatch.
        """
        self._logger.debug(f"Dispatching msg: {msg.to_json()}")
        tasks = []
        
        for event_type in (msg.code, "ALL"):
            for func in self._events.get(event_type, []):
                if asyncio.iscoroutinefunction(func):
                    tasks.append(func(msg))
                else:
                    func(msg)
        
        if tasks:
            await asyncio.gather(*tasks)

    async def send_msg(self, msg: Message, blocking: bool = False, timeout: float = 30.0):
        """
        Send a message to the WebSocket server.

        Args:
            msg (Message): The message to send.

        Raises:
            RuntimeError: If not connected to the server.
        """
        if not self._websocket:
            self._logger.critical("Not connected to the server!")
        self._logger.debug(f"Sending msg: {msg.to_json()}")
        await self._websocket.send(msg.to_json())

        if blocking:
            future = asyncio.get_running_loop().create_future()
            self._response_futures[msg.uuid] = future
            try:
                response = await asyncio.wait_for(future, timeout)
                return response
            except asyncio.TimeoutError:
                self._logger.warning(f"Timeout waiting for response to message {msg.uuid}")
            finally:
                self._response_futures.pop(msg.uuid, None)
        
        return None

    async def __aenter__(self):
        """
        Async context manager entry point.

        Returns:
            Client: The connected client instance.
        """
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit point.
        """
        await self.disconnect()