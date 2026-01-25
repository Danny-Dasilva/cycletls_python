"""Go shared library bindings for CycleTLS using CFFI.

This module provides two FFI modes:
1. Zero-copy mode (default): Uses raw bytes with explicit length (faster)
2. Base64 mode (fallback): Uses base64 encoding for compatibility

Zero-copy mode eliminates the ~33% size overhead and CPU cycles of base64.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import platform
import threading
from typing import Any, Dict, Iterator, Optional

import ormsgpack  # Drop-in replacement for msgpack, 10-30% faster (Rust-based)
from cffi import FFI

# Setup module logger
logger = logging.getLogger(__name__)


# Lazily initialized CFFI interface and shared library handle
_ffi = FFI()
_ffi.cdef(
    """
    // HTTP request functions (base64-encoded API)
    char* getRequest(char* data);
    unsigned long submitRequestAsync(char* data);
    char* checkRequestAsync(unsigned long handle);
    char* sendBatchRequest(char* data);
    void freeString(char* ptr);

    // Zero-copy API (raw bytes with explicit length)
    // Returns: pointer to result buffer, sets *outLen to result length
    char* getRequestZeroCopy(char* data, int dataLen, int* outLen);
    char* sendBatchRequestZeroCopy(char* data, int dataLen, int* outLen);

    // WebSocket functions
    unsigned long wsConnect(char* data);
    int wsSend(unsigned long handle, int msgType, char* data, int dataLen);
    char* wsReceive(unsigned long handle);
    void wsClose(unsigned long handle);

    // SSE (Server-Sent Events) functions
    unsigned long sseConnect(char* data);
    char* sseNextEvent(unsigned long handle);
    void sseClose(unsigned long handle);

    // Callback-based async API (pipe notification instead of polling)
    // Returns handle, writes 1 byte to notifyFD when complete
    uintptr_t submitRequestAsyncWithNotify(char* data, int dataLen, int notifyFD);
    // Retrieves result after notification (guaranteed ready)
    char* getAsyncResult(uintptr_t handle, int* outLen);
    """
)

_lib = None
_lib_lock = threading.Lock()
_use_zerocopy = None  # None = auto-detect, True/False = forced


def _get_library_filenames() -> list[str]:
    """Get list of library filenames to try, in priority order.

    Returns platform-specific names first, then falls back to generic names
    for backward compatibility.
    """
    system = platform.system()
    machine = platform.machine().lower()

    # Normalize architecture names to match build script output
    if machine in ("x86_64", "amd64"):
        arch = "x64"
    elif machine in ("aarch64", "arm64"):
        arch = "arm64"
    else:
        arch = machine

    filenames = []

    if system == "Windows":
        # Try platform-specific first, then generic
        filenames.append(f"cycletls-win-{arch}.dll")
        filenames.append("cycletls.dll")
    elif system == "Darwin":
        filenames.append(f"libcycletls-darwin-{arch}.dylib")
        filenames.append("libcycletls.dylib")
    else:
        # Default to Unix-style shared library (Linux, etc.)
        filenames.append(f"libcycletls-linux-{arch}.so")
        filenames.append("libcycletls.so")

    return filenames


def _iter_library_candidates() -> Iterator[str]:
    """Yield possible filesystem locations for the shared library."""
    env_override = os.environ.get("CYCLETLS_LIB_PATH")
    if env_override:
        yield env_override

    filenames = _get_library_filenames()
    package_dir = os.path.abspath(os.path.dirname(__file__))

    # Try each filename in each location
    for filename in filenames:
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


def _has_zerocopy_support() -> bool:
    """Check if the loaded library supports zero-copy API."""
    global _use_zerocopy
    if _use_zerocopy is not None:
        return _use_zerocopy

    lib = _load_library()
    try:
        # Check if getRequestZeroCopy exists
        _ = lib.getRequestZeroCopy
        _use_zerocopy = True
        logger.debug("Zero-copy FFI mode enabled")
    except AttributeError:
        _use_zerocopy = False
        logger.debug("Zero-copy FFI not available, using base64 mode")
    return _use_zerocopy


def _send_request_zerocopy(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute request using zero-copy mode (no base64 encoding)."""
    lib = _load_library()

    # Serialize payload to msgpack (raw bytes)
    msgpack_data = ormsgpack.packb(payload)

    # Create buffer from raw bytes - CFFI's from_buffer creates a view, not a copy
    buf = _ffi.from_buffer(msgpack_data)

    # Prepare output length pointer
    out_len = _ffi.new("int*")

    logger.debug(f"Calling getRequestZeroCopy (input: {len(msgpack_data)} bytes)")

    # Call zero-copy function
    response_ptr = lib.getRequestZeroCopy(buf, len(msgpack_data), out_len)

    if response_ptr == _ffi.NULL:
        error_msg = "CycleTLS shared library returned NULL response"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    try:
        # Read exact number of bytes (no null termination issues)
        response_len = out_len[0]
        raw_response = _ffi.buffer(response_ptr, response_len)[:]
        logger.debug(f"Received zero-copy response ({response_len} bytes)")
    finally:
        lib.freeString(response_ptr)

    # Unpack msgpack directly (no base64 decode needed)
    return ormsgpack.unpackb(raw_response)


def _send_request_base64(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute request using base64 mode (compatibility fallback)."""
    lib = _load_library()

    # Use msgpack for binary serialization (3-5x faster than JSON)
    # Then base64 encode to avoid null bytes in C string transfer
    # use_bin_type=False to keep strings as strings for Go compatibility
    msgpack_data = ormsgpack.packb(payload)
    b64_data = base64.b64encode(msgpack_data)
    buf = _ffi.new("char[]", b64_data)

    logger.debug("Calling Go shared library getRequest() [base64 mode]")

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
    return ormsgpack.unpackb(raw)


def send_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a request against the Go runtime via the shared library (synchronous).

    Automatically uses zero-copy mode if available, falls back to base64.
    """
    if _has_zerocopy_support():
        return _send_request_zerocopy(payload)
    return _send_request_base64(payload)


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
    msgpack_data = ormsgpack.packb(payload)
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
    return ormsgpack.unpackb(raw)


async def send_request_async(
    payload: Dict[str, Any], poll_interval: float = 0.0, timeout: float = 30.0
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
            raise asyncio.TimeoutError(f"Request timed out after {timeout} seconds")

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
    payloads: list[Dict[str, Any]], poll_interval: float = 0.001, timeout: float = 30.0
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
    return await asyncio.gather(
        *[send_request_async(payload, poll_interval, timeout) for payload in payloads]
    )


# ============================================================================
# Callback-Based Async (Zero Polling)
# ============================================================================
# Uses pipe notification instead of polling, reducing FFI calls from 10-200
# per request to exactly 2 (submit + get result).


async def send_request_async_callback(
    payload: Dict[str, Any], timeout: float = 30.0
) -> Dict[str, Any]:
    """Execute a request asynchronously using pipe notification (no polling).

    This is more efficient than send_request_async() because it uses OS-level
    pipe notification instead of polling. FFI calls are reduced from 10-200
    per request to exactly 2 (submit + get result).

    Args:
        payload: Request payload dictionary with requestId and options
        timeout: Maximum wait time in seconds (default: 30s)

    Returns:
        Response dictionary with Status, Body, Headers, FinalUrl, Cookies

    Raises:
        RuntimeError: If request submission or retrieval fails
        asyncio.TimeoutError: If timeout is exceeded
    """
    lib = _load_library()

    # Create pipe for notification
    read_fd, write_fd = os.pipe()

    try:
        # Serialize payload to msgpack (zero-copy style)
        msgpack_data = ormsgpack.packb(payload)

        # Create buffer from raw bytes
        buf = _ffi.from_buffer(msgpack_data)

        logger.debug(f"Submitting async request with callback notification (fd={write_fd})")

        # Submit request with notification FD
        handle = lib.submitRequestAsyncWithNotify(buf, len(msgpack_data), write_fd)

        if handle == 0:
            error_msg = "Failed to submit async request (invalid payload or null handle)"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        logger.debug(f"Async request submitted with handle: {handle}")

        # Wait for notification (Go will write 1 byte when complete)
        loop = asyncio.get_event_loop()
        try:
            await asyncio.wait_for(loop.run_in_executor(None, os.read, read_fd, 1), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"Async request {handle} timed out after {timeout}s")
            raise asyncio.TimeoutError(f"Request timed out after {timeout} seconds")

        logger.debug(f"Received notification for handle: {handle}")

        # Get result (guaranteed ready since pipe was written)
        out_len = _ffi.new("int*")
        result_ptr = lib.getAsyncResult(handle, out_len)

        if result_ptr == _ffi.NULL:
            error_msg = "Failed to get async result (null pointer returned)"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            # Read exact number of bytes
            response_len = out_len[0]
            raw_response = _ffi.buffer(result_ptr, response_len)[:]
            logger.debug(f"Received async result ({response_len} bytes)")
        finally:
            lib.freeString(result_ptr)

        # Unpack msgpack response
        return ormsgpack.unpackb(raw_response)

    finally:
        # Clean up pipe file descriptors
        os.close(read_fd)
        os.close(write_fd)


def _send_batch_request_zerocopy(payloads: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Send batch request using zero-copy mode."""
    lib = _load_library()

    # Wrap payloads in batch structure
    batch_data = {"requests": payloads}
    msgpack_data = ormsgpack.packb(batch_data)

    # Create buffer from raw bytes
    buf = _ffi.from_buffer(msgpack_data)

    # Prepare output length pointer
    out_len = _ffi.new("int*")

    logger.debug(
        f"Sending batch request [zero-copy] ({len(payloads)} payloads, {len(msgpack_data)} bytes)"
    )

    response_ptr = lib.sendBatchRequestZeroCopy(buf, len(msgpack_data), out_len)

    if response_ptr == _ffi.NULL:
        error_msg = "CycleTLS batch request returned NULL response"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    try:
        response_len = out_len[0]
        raw_response = _ffi.buffer(response_ptr, response_len)[:]
        logger.debug(f"Received batch response ({response_len} bytes)")
    finally:
        lib.freeString(response_ptr)

    result = ormsgpack.unpackb(raw_response)
    return result.get("responses", [])


def _send_batch_request_base64(payloads: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Send batch request using base64 mode."""
    lib = _load_library()

    # Wrap payloads in batch structure
    batch_data = {"requests": payloads}
    msgpack_data = ormsgpack.packb(batch_data)
    b64_data = base64.b64encode(msgpack_data)
    buf = _ffi.new("char[]", b64_data)

    logger.debug(f"Sending batch request [base64] ({len(payloads)} payloads)")

    response_ptr = lib.sendBatchRequest(buf)

    if response_ptr == _ffi.NULL:
        error_msg = "CycleTLS batch request returned NULL response"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    try:
        raw_b64 = _ffi.string(response_ptr)
        logger.debug(f"Received batch response (size: {len(raw_b64)} bytes)")
    finally:
        lib.freeString(response_ptr)

    # Decode base64 then unpack msgpack
    raw = base64.b64decode(raw_b64)
    result = ormsgpack.unpackb(raw)
    return result.get("responses", [])


def send_batch_request(payloads: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Send multiple requests in a single FFI call.

    This is more efficient than individual requests because it amortizes
    FFI call overhead across all requests. Requests are executed in parallel
    on the Go side using goroutines.

    Automatically uses zero-copy mode if available, falls back to base64.

    Args:
        payloads: List of request payload dictionaries. Each payload should have:
            - requestId: Unique identifier for the request
            - options: Request options dict with url, method, headers, body, etc.

    Returns:
        List of response dictionaries in the same order as input payloads.
        Each response contains: RequestID, Status, Body, Headers, FinalUrl, Cookies

    Raises:
        RuntimeError: If the batch request fails
    """
    # Handle empty batch case on Python side (avoid FFI call)
    if not payloads:
        return []

    if _has_zerocopy_support():
        return _send_batch_request_zerocopy(payloads)
    return _send_batch_request_base64(payloads)


__all__ = [
    "send_request",
    "submit_request_async",
    "check_request_async",
    "send_request_async",
    "send_request_async_callback",
    "send_requests_batch",
    "send_batch_request",
]
