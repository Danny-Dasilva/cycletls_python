"""Server-Sent Events (SSE) client for CycleTLS.

This module provides an SSE client that uses the same TLS fingerprinting
capabilities as the HTTP client for streaming event connections.

Example:
    >>> from cycletls.sse import SSEConnection
    >>>
    >>> # Using context manager
    >>> with SSEConnection("https://api.example.com/events") as sse:
    ...     for event in sse:
    ...         print(f"{event.event}: {event.data}")
    >>>
    >>> # Async iteration
    >>> async with SSEConnection("https://api.example.com/events") as sse:
    ...     async for event in sse:
    ...         print(f"{event.event}: {event.data}")
"""

from __future__ import annotations

import asyncio
import base64
import logging
import threading
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, Iterator, Optional

import ormsgpack  # Drop-in replacement for msgpack, 10-30% faster

from ._ffi import _ffi, _load_library

logger = logging.getLogger(__name__)


@dataclass
class SSEEvent:
    """A Server-Sent Event.

    Attributes:
        data: Event data
        event: Event type (defaults to "message")
        id: Optional event ID for reconnection
        retry: Optional retry time in milliseconds
    """

    data: str
    event: str = "message"
    id: Optional[str] = None
    retry: Optional[int] = None

    def __str__(self) -> str:
        """Return a string representation of the event."""
        return f"SSEEvent(event={self.event!r}, data={self.data[:50]!r}...)"


class SSEError(Exception):
    """Raised when an SSE operation fails."""

    pass


class SSEConnection:
    """A Server-Sent Events connection with TLS fingerprinting support.

    This class provides both synchronous and asynchronous APIs for SSE
    streams. It supports automatic reconnection and Last-Event-ID tracking.

    Args:
        url: SSE endpoint URL
        headers: Optional headers to include in the request
        ja3: Optional JA3 fingerprint for TLS
        user_agent: Optional User-Agent header
        proxy: Optional proxy URL
        timeout: Connection timeout in seconds
        last_event_id: Optional Last-Event-ID for reconnection

    Example:
        >>> # Synchronous iteration
        >>> with SSEConnection("https://api.example.com/events") as sse:
        ...     for event in sse:
        ...         if event.event == "update":
        ...             print(event.data)
        >>>
        >>> # Async iteration
        >>> async with SSEConnection("https://api.example.com/events") as sse:
        ...     async for event in sse:
        ...         print(f"[{event.event}] {event.data}")
    """

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        ja3: Optional[str] = None,
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None,
        timeout: int = 30,
        last_event_id: Optional[str] = None,
    ):
        self.url = url
        self.headers = headers or {}
        self.ja3 = ja3
        self.user_agent = user_agent
        self.proxy = proxy
        self.timeout = timeout
        self.last_event_id = last_event_id

        self._handle: Optional[int] = None
        self._connected = False
        self._lock = threading.Lock()
        self._retry_time = 3000  # Default retry time in ms

    @property
    def connected(self) -> bool:
        """Check if the SSE connection is active."""
        return self._connected

    @property
    def retry_time(self) -> int:
        """Get the current retry time in milliseconds."""
        return self._retry_time

    def connect(self) -> None:
        """Establish the SSE connection.

        Raises:
            SSEError: If connection fails
        """
        if self._connected:
            return

        lib = _load_library()

        # Check if sseConnect is available
        if not hasattr(lib, "sseConnect"):
            raise SSEError(
                "SSE support requires rebuilding the Go library with SSE exports. "
                "The current library does not have sseConnect exported."
            )

        # Build connection options
        headers_dict = {
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
            **self.headers,
        }
        if self.last_event_id:
            headers_dict["Last-Event-ID"] = self.last_event_id

        options: Dict[str, Any] = {
            "url": self.url,
            "headers": headers_dict,
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

        logger.debug(f"Connecting to SSE endpoint: {self.url}")
        handle = lib.sseConnect(buf)

        if handle == 0:
            raise SSEError(f"Failed to connect to SSE endpoint: {self.url}")

        self._handle = handle
        self._connected = True
        logger.info(f"SSE connected to {self.url}")

    def next_event(self) -> Optional[SSEEvent]:
        """Read the next event from the stream.

        Returns:
            SSEEvent if an event was received, None if stream ended

        Raises:
            SSEError: If not connected or read fails
        """
        if not self._connected or self._handle is None:
            raise SSEError("SSE connection is not active")

        lib = _load_library()

        if not hasattr(lib, "sseNextEvent"):
            raise SSEError("SSE next_event not supported in this library build")

        response_ptr = lib.sseNextEvent(self._handle)

        if response_ptr == _ffi.NULL:
            # Stream ended
            self._connected = False
            return None

        try:
            raw_b64 = _ffi.string(response_ptr)
        finally:
            lib.freeString(response_ptr)

        # Decode response
        raw = base64.b64decode(raw_b64)
        result = ormsgpack.unpackb(raw)

        # Check for end of stream
        if result.get("eof", False):
            self._connected = False
            return None

        # Check for error
        if "error" in result:
            raise SSEError(result["error"])

        # Build event
        event = SSEEvent(
            data=result.get("data", ""),
            event=result.get("event", "message"),
            id=result.get("id"),
            retry=result.get("retry"),
        )

        # Update tracking
        if event.id:
            self.last_event_id = event.id
        if event.retry:
            self._retry_time = event.retry

        logger.debug(f"Received SSE event: {event.event}")
        return event

    def close(self) -> None:
        """Close the SSE connection."""
        if not self._connected or self._handle is None:
            return

        lib = _load_library()

        if hasattr(lib, "sseClose"):
            logger.debug("Closing SSE connection")
            lib.sseClose(self._handle)

        self._handle = None
        self._connected = False
        logger.info("SSE connection closed")

    async def connect_async(self) -> None:
        """Async version of connect()."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.connect)

    async def next_event_async(self) -> Optional[SSEEvent]:
        """Async version of next_event()."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.next_event)

    async def close_async(self) -> None:
        """Async version of close()."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.close)

    def __enter__(self) -> "SSEConnection":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    async def __aenter__(self) -> "SSEConnection":
        """Async context manager entry."""
        await self.connect_async()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close_async()

    def __iter__(self) -> Iterator[SSEEvent]:
        """Iterate over events synchronously."""
        while self._connected:
            event = self.next_event()
            if event is None:
                break
            yield event

    async def __aiter__(self) -> AsyncIterator[SSEEvent]:
        """Iterate over events asynchronously."""
        while self._connected:
            event = await self.next_event_async()
            if event is None:
                break
            yield event


__all__ = [
    "SSEEvent",
    "SSEError",
    "SSEConnection",
]
