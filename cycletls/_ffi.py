"""Go shared library bindings for CycleTLS using CFFI."""

from __future__ import annotations

import asyncio
import base64
import os
import platform
import threading
import logging
from typing import Any, Dict, Iterator, Optional

import msgpack
from cffi import FFI

# Setup module logger
logger = logging.getLogger(__name__)


# Lazily initialized CFFI interface and shared library handle
_ffi = FFI()
_ffi.cdef(
    """
    char* getRequest(char* data);
    unsigned long submitRequestAsync(char* data);
    char* checkRequestAsync(unsigned long handle);
    void freeString(char* ptr);
    """
)

_lib = None
_lib_lock = threading.Lock()
# _send_lock removed: Go backend is thread-safe (singleton client with sync.RWMutex on pool)


def _get_library_filename() -> str:
    system = platform.system()

    if system == "Windows":
        return "cycletls.dll"
    if system == "Darwin":
        return "libcycletls.dylib"
    # Default to Unix-style shared library
    return "libcycletls.so"


def _iter_library_candidates() -> Iterator[str]:
    """Yield possible filesystem locations for the shared library."""
    env_override = os.environ.get("CYCLETLS_LIB_PATH")
    if env_override:
        yield env_override

    filename = _get_library_filename()
    package_dir = os.path.abspath(os.path.dirname(__file__))

    # Common locations inside the package
    yield os.path.join(package_dir, "dist", filename)
    yield os.path.join(package_dir, filename)

    # Project root during development
    project_root = os.path.abspath(os.path.join(package_dir, os.pardir))
    yield os.path.join(project_root, "dist", filename)


def _load_library():
    global _lib

    with _lib_lock:
        if _lib is not None:
            return _lib

        for candidate in _iter_library_candidates():
            if candidate and os.path.exists(candidate):
                logger.debug(f"Loading CycleTLS shared library from: {candidate}")
                _lib = _ffi.dlopen(candidate)
                logger.info(f"Successfully loaded CycleTLS shared library: {candidate}")
                return _lib

        error_msg = (
            "CycleTLS shared library not found. Set CYCLETLS_LIB_PATH or build the "
            "Go library using 'go build -buildmode=c-shared'."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def send_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a request against the Go runtime via the shared library (synchronous)."""
    lib = _load_library()

    # Use msgpack for binary serialization (3-5x faster than JSON)
    # Then base64 encode to avoid null bytes in C string transfer
    # use_bin_type=False to keep strings as strings for Go compatibility
    msgpack_data = msgpack.packb(payload, use_bin_type=False)
    b64_data = base64.b64encode(msgpack_data)
    buf = _ffi.new("char[]", b64_data)

    logger.debug("Calling Go shared library getRequest()")

    # No lock needed: Go backend is thread-safe
    response_ptr = lib.getRequest(buf)

    if response_ptr == _ffi.NULL:
        error_msg = "CycleTLS shared library returned NULL response"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    try:
        raw_b64 = _ffi.string(response_ptr)
        logger.debug(f"Received base64 response from Go (size: {len(raw_b64)} bytes)")
    finally:
        lib.freeString(response_ptr)

    # Decode base64 then unpack msgpack
    raw = base64.b64decode(raw_b64)
    return msgpack.unpackb(raw, raw=False)


def submit_request_async(payload: Dict[str, Any]) -> int:
    """Submit a request asynchronously and return a handle for polling.

    Args:
        payload: Request payload dictionary

    Returns:
        Handle ID (uintptr) for checking result later

    Raises:
        RuntimeError: If submission fails
    """
    lib = _load_library()

    # Serialize payload
    msgpack_data = msgpack.packb(payload, use_bin_type=False)
    b64_data = base64.b64encode(msgpack_data)
    buf = _ffi.new("char[]", b64_data)

    logger.debug("Submitting async request to Go worker pool")

    # Submit request (non-blocking, no lock needed)
    handle = lib.submitRequestAsync(buf)

    if handle == 0:
        error_msg = "Failed to submit async request (invalid payload)"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    logger.debug(f"Async request submitted with handle: {handle}")
    return handle


def check_request_async(handle: int) -> Optional[Dict[str, Any]]:
    """Check if an async request is complete and return result if ready.

    Args:
        handle: Handle ID returned by submit_request_async()

    Returns:
        Response dictionary if ready, None if still processing

    Raises:
        RuntimeError: If check fails
    """
    lib = _load_library()

    logger.debug(f"Checking async request handle: {handle}")

    # Non-blocking check
    response_ptr = lib.checkRequestAsync(handle)

    if response_ptr == _ffi.NULL:
        # Not ready yet
        logger.debug(f"Request {handle} still processing")
        return None

    # Result ready
    try:
        raw_b64 = _ffi.string(response_ptr)
        logger.debug(f"Request {handle} complete (size: {len(raw_b64)} bytes)")
    finally:
        lib.freeString(response_ptr)

    # Decode base64 then unpack msgpack
    raw = base64.b64decode(raw_b64)
    return msgpack.unpackb(raw, raw=False)


async def send_request_async(
    payload: Dict[str, Any],
    poll_interval: float = 0.0,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """Execute a request asynchronously with polling.

    Args:
        payload: Request payload dictionary
        poll_interval: Time between polls in seconds (default: 0 = tight loop with yield)
        timeout: Maximum wait time in seconds (default: 30s)

    Returns:
        Response dictionary

    Raises:
        RuntimeError: If request fails
        asyncio.TimeoutError: If timeout is exceeded
    """
    # Submit request
    handle = submit_request_async(payload)

    # Poll for completion with adaptive backoff
    start_time = asyncio.get_event_loop().time()
    check_count = 0

    while True:
        # Check if ready
        result = check_request_async(handle)
        if result is not None:
            return result

        # Check timeout
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed > timeout:
            logger.error(f"Async request {handle} timed out after {timeout}s")
            raise asyncio.TimeoutError(
                f"Request timed out after {timeout} seconds"
            )

        # Adaptive polling: tight loop for fast responses, backoff for slow ones
        check_count += 1
        if poll_interval == 0.0:
            # Tight loop with yield for fast local requests
            if check_count < 100:
                # First 100 checks: just yield to event loop (no sleep)
                await asyncio.sleep(0)
            elif check_count < 1000:
                # Next 900 checks: 100μs sleep (0.0001s)
                await asyncio.sleep(0.0001)
            else:
                # After 1000 checks: 1ms sleep
                await asyncio.sleep(0.001)
        else:
            # User-specified interval
            await asyncio.sleep(poll_interval)


async def send_requests_batch(
    payloads: list[Dict[str, Any]],
    poll_interval: float = 0.001,
    timeout: float = 30.0
) -> list[Dict[str, Any]]:
    """Execute multiple requests concurrently with async polling.

    Args:
        payloads: List of request payload dictionaries
        poll_interval: Time between polls in seconds (default: 1ms)
        timeout: Maximum wait time in seconds (default: 30s)

    Returns:
        List of response dictionaries in the same order as input

    Raises:
        RuntimeError: If any request fails
        asyncio.TimeoutError: If timeout is exceeded
    """
    return await asyncio.gather(*[
        send_request_async(payload, poll_interval, timeout)
        for payload in payloads
    ])


__all__ = [
    "send_request",
    "submit_request_async",
    "check_request_async",
    "send_request_async",
    "send_requests_batch",
]

