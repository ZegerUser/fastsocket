import asyncio
import json
import logging
from typing import Dict, List, Callable, Any
import websockets
import inspect

import websockets.legacy
import websockets.legacy.client

from .message import Message
from .utils import setup_logger

class Server:
    """
    A WebSocket server for handling asynchronous communication.

    This class provides methods to start a WebSocket server, handle client connections,
    process incoming messages, and send messages to connected clients.
    """

    def __init__(self, host: str, port: int, log_level:logging.INFO) -> None:
        """
        Initialize the Server.

        Args:
            host (str): The host address to bind the server to.
            port (int): The port number to listen on.
            log_level (int): The logging level.
        """
        self._host = host
        self._port = port
        self._logger, _ = setup_logger("WS Server", level=log_level)

        self._registed_callbacks: Dict[str, List[Callable]] = {}
        self._connections: Dict[str, Any] = {}
    
    async def _handle_connection(self, ws, path):
        """
        Handle a new WebSocket connection.

        Args:
            ws: The WebSocket connection object.
            path: The path of the connection.
        """
        self._logger.info(f"Got new connection from: {ws.remote_address}, {path}")
        self._connections[path[1:]] = ws

        try:
            async for message in ws:
                await self._process_message(ws, message)
        
        finally:
            self._logger.info(f"Connection disconnected: {ws.remote_address}, {path}")
            del self._connections[path[1:]]
    
    async def _process_message(self, ws, message):
        """
        Process an incoming message.

        Args:
            ws: The WebSocket connection object.
            message: The raw message received from the client.
        """
        self._logger.debug(f"Processing message: {message}")
        try:
            msg = Message.from_json(message)
            await self._dispatch_message(msg, ws)

        except Exception as e:
            self._logger.error(f"Error processing message ({message}): {e}")
    
    async def _dispatch_message(self, msg: Message, ws):
        """
        Dispatch a message to registered callbacks.

        Args:
            msg (Message): The message to dispatch.
        """
        self._logger.debug(f"Dispatching msg: {msg.to_json()}")
        tasks = []
        
        for message_code in (msg.code, "ALL"):
            for func in self._registed_callbacks.get(message_code, []):
                tasks.append(func(msg, ws))
        
        if tasks:
            await asyncio.gather(*tasks)
    
    async def send_msg(self, msg: Message, path: str = None):
        """
        Send a message to connected clients.

        Args:
            msg (Message): The message to send.
            path (str, optional): The specific path to send the message to. If None, send to all connections.
        """
        self._logger.debug(f"Sending msg: {msg.to_json()}")
        if path is None:
            await asyncio.gather(*[ws.send(msg.to_json()) for ws in self._connections.values()])

        elif path in self._connections:
            await self._connections[path].send(msg.to_json())

        else:
            self._logger.warning(f"Attempted to send message to non-existent path: {path}")
    
    async def start(self):
        """
        Start the WebSocket server.

        Returns:
            Server: The started server instance.
        """
        self._server = await websockets.serve(self._handle_connection, self._host, self._port)
        self._logger.info(f"Server started and listening on ws://{self._host}:{self._port}")
        return self
    
    async def stop(self):
        """
        Stop the WebSocket server.
        """
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._logger.info("Server stopped")
    
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
        Decorator for registering callbacks for specific message codes.

        Args:
            code (str): The message code to register the callback for.

        Returns:
            Callable: The decorator function.
        """
        def decorator(func: Callable):
            if code not in self._registed_callbacks:
                self._registed_callbacks[code] = []
            self._registed_callbacks[code].append(func)
            return func
        return decorator

    async def __aenter__(self):
        """
        Async context manager entry point.

        Returns:
            Server: The started server instance.
        """
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit point.
        """
        await self.stop()