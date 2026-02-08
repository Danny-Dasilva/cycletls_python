"""WebSocket client for CycleTLS with TLS fingerprinting support.

This module provides a WebSocket client that uses the same TLS fingerprinting
capabilities as the HTTP client for establishing WebSocket connections.

Example:
    >>> from cycletls import CycleTLS
    >>> from cycletls.websocket import WebSocketConnection
    >>>
    >>> # Using context manager
    >>> with WebSocketConnection("wss://echo.websocket.org") as ws:
    ...     ws.send("Hello, World!")
    ...     message = ws.receive()
    ...     print(message.data)
    >>>
    >>> # Async iteration
    >>> async with WebSocketConnection("wss://stream.example.com") as ws:
    ...     async for message in ws:
    ...         print(message.data)
"""

from __future__ import annotations

import asyncio
import base64
import logging
import threading
from dataclasses import dataclass
from enum import IntEnum
from typing import AsyncIterator, Dict, Iterator, Optional, Union

import ormsgpack  # Drop-in replacement for msgpack, 10-30% faster

from ._ffi import _ffi, _load_library
from .exceptions import CycleTLSError

logger = logging.getLogger(__name__)


class MessageType(IntEnum):
    """WebSocket message types."""

    TEXT = 1
    BINARY = 2
    CLOSE = 8
    PING = 9
    PONG = 10


@dataclass
class WebSocketMessage:
    """A WebSocket message received from the server.

    Attributes:
        type: Message type (TEXT=1, BINARY=2, CLOSE=8, PING=9, PONG=10)
        data: Message data (str for text, bytes for binary)
    """

    type: MessageType
    data: Union[str, bytes]

    @property
    def is_text(self) -> bool:
        """Check if this is a text message."""
        return self.type == MessageType.TEXT

    @property
    def is_binary(self) -> bool:
        """Check if this is a binary message."""
        return self.type == MessageType.BINARY

    @property
    def is_close(self) -> bool:
        """Check if this is a close message."""
        return self.type == MessageType.CLOSE


class WebSocketError(CycleTLSError):
    """Raised when a WebSocket operation fails."""

    pass


class WebSocketConnection:
    """A WebSocket connection with TLS fingerprinting support.

    This class provides both synchronous and asynchronous APIs for WebSocket
    communication. It supports context managers for automatic cleanup.

    Args:
        url: WebSocket URL (ws:// or wss://)
        headers: Optional headers to include in the handshake
        ja3: Optional JA3 fingerprint for TLS
        user_agent: Optional User-Agent header
        proxy: Optional proxy URL
        timeout: Connection timeout in seconds

    Example:
        >>> # Synchronous usage
        >>> ws = WebSocketConnection("wss://echo.websocket.org")
        >>> ws.connect()
        >>> ws.send("Hello")
        >>> msg = ws.receive()
        >>> ws.close()
        >>>
        >>> # Context manager
        >>> with WebSocketConnection("wss://echo.websocket.org") as ws:
        ...     ws.send("Hello")
        ...     msg = ws.receive()
        >>>
        >>> # Async context manager
        >>> async with WebSocketConnection("wss://stream.example.com") as ws:
        ...     await ws.send_async("Hello")
        ...     msg = await ws.receive_async()
    """

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        ja3: Optional[str] = None,
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None,
        timeout: int = 30,
    ):
        self.url = url
        self.headers = headers or {}
        self.ja3 = ja3
        self.user_agent = user_agent
        self.proxy = proxy
        self.timeout = timeout

        self._handle: Optional[int] = None
        self._connected = False
        self._lock = threading.Lock()

    @property
    def connected(self) -> bool:
        """Check if the WebSocket is currently connected."""
        return self._connected

    def connect(self) -> None:
        """Establish the WebSocket connection.

        Raises:
            WebSocketError: If connection fails
        """
        if self._connected:
            return

        lib = _load_library()

        # Check if wsConnect is available
        if not hasattr(lib, "wsConnect"):
            raise WebSocketError(
                "WebSocket support requires rebuilding the Go library with WebSocket exports. "
                "The current library does not have wsConnect exported."
            )

        # Build connection options
        options = {
            "url": self.url,
            "headers": self.headers,
            "timeout": self.timeout,
        }
        if self.ja3:
            options["ja3"] = self.ja3
        if self.user_agent:
            options["userAgent"] = self.user_agent
        if self.proxy:
            options["proxy"] = self.proxy

        # Serialize and send
        msgpack_data = ormsgpack.packb(options)
        b64_data = base64.b64encode(msgpack_data)
        buf = _ffi.new("char[]", b64_data)

        logger.debug(f"Connecting to WebSocket: {self.url}")
        handle = lib.wsConnect(buf)

        if handle == 0:
            raise WebSocketError(f"Failed to connect to {self.url}")

        self._handle = handle
        self._connected = True
        logger.info(f"WebSocket connected to {self.url}")

    def send(self, data: Union[str, bytes], binary: bool = False) -> None:
        """Send a message over the WebSocket.

        Args:
            data: Message data to send
            binary: If True, send as binary message; otherwise send as text

        Raises:
            WebSocketError: If not connected or send fails
        """
        if not self._connected or self._handle is None:
            raise WebSocketError("WebSocket is not connected")

        lib = _load_library()

        if not hasattr(lib, "wsSend"):
            raise WebSocketError("WebSocket send not supported in this library build")

        # Determine message type
        msg_type = MessageType.BINARY if binary else MessageType.TEXT

        # Encode data
        if isinstance(data, str):
            data_bytes = data.encode("utf-8")
        else:
            data_bytes = data

        b64_data = base64.b64encode(data_bytes)
        buf = _ffi.new("char[]", b64_data)
        data_len = len(data_bytes)

        logger.debug(f"Sending WebSocket message: type={msg_type}, len={data_len}")
        result = lib.wsSend(self._handle, int(msg_type), buf, data_len)

        if result != 0:
            raise WebSocketError(f"Failed to send WebSocket message: error code {result}")

    def receive(self, timeout: Optional[float] = None) -> WebSocketMessage:
        """Receive a message from the WebSocket.

        Args:
            timeout: Optional timeout in seconds (uses connection timeout if not specified)

        Returns:
            WebSocketMessage with the received data

        Raises:
            WebSocketError: If not connected or receive fails
        """
        if not self._connected or self._handle is None:
            raise WebSocketError("WebSocket is not connected")

        lib = _load_library()

        if not hasattr(lib, "wsReceive"):
            raise WebSocketError("WebSocket receive not supported in this library build")

        logger.debug("Waiting for WebSocket message...")
        response_ptr = lib.wsReceive(self._handle)

        if response_ptr == _ffi.NULL:
            raise WebSocketError("Failed to receive WebSocket message")

        try:
            raw_b64 = _ffi.string(response_ptr)
        finally:
            lib.freeString(response_ptr)

        # Decode response
        raw = base64.b64decode(raw_b64)
        result = ormsgpack.unpackb(raw)

        msg_type = MessageType(result.get("type", MessageType.TEXT))
        data = result.get("data", "")

        # Decode base64 data if binary
        if msg_type == MessageType.BINARY and isinstance(data, str):
            data = base64.b64decode(data)

        logger.debug(f"Received WebSocket message: type={msg_type}")
        return WebSocketMessage(type=msg_type, data=data)

    def close(self, code: int = 1000, reason: str = "") -> None:
        """Close the WebSocket connection.

        Args:
            code: WebSocket close code (default 1000 = normal closure)
            reason: Optional close reason
        """
        if not self._connected or self._handle is None:
            return

        lib = _load_library()

        if hasattr(lib, "wsClose"):
            logger.debug(f"Closing WebSocket connection: code={code}")
            lib.wsClose(self._handle)

        self._handle = None
        self._connected = False
        logger.info("WebSocket connection closed")

    async def connect_async(self) -> None:
        """Async version of connect()."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.connect)

    async def send_async(self, data: Union[str, bytes], binary: bool = False) -> None:
        """Async version of send()."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.send, data, binary)

    async def receive_async(self, timeout: Optional[float] = None) -> WebSocketMessage:
        """Async version of receive()."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.receive, timeout)

    async def close_async(self, code: int = 1000, reason: str = "") -> None:
        """Async version of close()."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.close, code, reason)

    def __enter__(self) -> "WebSocketConnection":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    async def __aenter__(self) -> "WebSocketConnection":
        """Async context manager entry."""
        await self.connect_async()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close_async()

    def __iter__(self) -> Iterator[WebSocketMessage]:
        """Iterate over incoming messages synchronously."""
        while self._connected:
            try:
                yield self.receive()
            except WebSocketError:
                break

    async def __aiter__(self) -> AsyncIterator[WebSocketMessage]:
        """Iterate over incoming messages asynchronously."""
        while self._connected:
            try:
                yield await self.receive_async()
            except WebSocketError:
                break


__all__ = [
    "MessageType",
    "WebSocketMessage",
    "WebSocketError",
    "WebSocketConnection",
]
