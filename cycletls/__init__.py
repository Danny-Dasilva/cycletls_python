"""
CycleTLS - Advanced TLS Fingerprinting HTTP Client

Usage:
    Basic request (auto-setup, auto-cleanup):
        >>> import cycletls
        >>> response = cycletls.get('https://example.com')
        >>> print(response.status_code)
        200

    Configure defaults:
        >>> cycletls.set_default(
        ...     proxy='socks5://127.0.0.1:9050',
        ...     timeout=10,
        ...     ja3='771,4865-4866...'
        ... )
        >>> response = cycletls.get('https://example.com')  # Uses defaults

    Per-request overrides:
        >>> response = cycletls.get(
        ...     'https://example.com',
        ...     timeout=5  # Override default
        ... )

    Manual session management:
        >>> with cycletls.CycleTLS() as client:
        ...     response = client.get('https://example.com')
"""

from typing import Any, Dict, Optional

__version__ = "0.0.2"

# Import core classes
from .api import CycleTLS
from .async_api import AsyncCycleTLS, async_delete, async_get, async_post, async_put
from .exceptions import (
    ConnectionError,
    ConnectTimeout,
    CycleTLSError,
    HTTPError,
    InvalidHeader,
    InvalidURL,
    ProxyError,
    ReadTimeout,
    RequestException,
    Timeout,
    TLSError,
    TooManyRedirects,
)

# Import fingerprint plugin system
from .fingerprints import (
    CHROME_120,
    CHROME_121,
    CHROME_ANDROID,
    EDGE_120,
    FIREFOX_121,
    SAFARI_17,
    SAFARI_IOS,
    FingerprintRegistry,
    TLSFingerprint,
)
from .plugins import (
    create_fingerprint_template,
    load_fingerprint_from_file,
    load_fingerprints_from_dir,
    load_fingerprints_from_env,
)
from .schema import *  # noqa: F403
from .sessions import Session
from .sse import (
    SSEConnection,
    SSEError,
)
from .sse import (
    SSEEvent as SSEEvent,  # type: ignore[misc,assignment]  # override schema.py version
)
from .structures import CaseInsensitiveDict, CookieJar

# Import WebSocket and SSE support
from .websocket import (
    MessageType,
    WebSocketConnection,
    WebSocketError,
)
from .websocket import (
    WebSocketMessage as WebSocketMessage,  # type: ignore[misc,assignment]  # override schema.py version
)

# Import configuration and global session management
from ._config import (  # noqa: E402
    _CONFIGURABLE_ATTRS,
    _config,
    _merge_defaults,
    get_default,
    reset_defaults,
    set_default,
)
from ._global import (  # noqa: E402
    close_global_session,
    get_global_session,
)

# Initialize default configuration on package import
set_default(enable_connection_reuse=True)


# Module-level convenience functions
def request(method: str, url: str, **kwargs) -> "Response":
    """
    Make an HTTP request using the global session with defaults.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Target URL
        **kwargs: Additional request options

    Returns:
        Response object

    Example:
        >>> import cycletls
        >>> response = cycletls.request('GET', 'https://example.com')
    """
    session = get_global_session()
    merged_kwargs = _merge_defaults(kwargs)
    return session.request(method, url, **merged_kwargs)


def get(url: str, **kwargs) -> "Response":
    """
    Make a GET request using the global session with defaults.

    Args:
        url: Target URL
        **kwargs: Additional request options (headers, params, etc.)

    Returns:
        Response object

    Example:
        >>> import cycletls
        >>> response = cycletls.get('https://example.com')
        >>> print(response.status_code)
    """
    session = get_global_session()
    merged_kwargs = _merge_defaults(kwargs)
    return session.get(url, **merged_kwargs)


def post(
    url: str, data: Optional[Any] = None, json_data: Optional[Dict] = None, **kwargs
) -> "Response":
    """
    Make a POST request using the global session with defaults.

    Args:
        url: Target URL
        data: Form data or raw body
        json_data: JSON payload
        **kwargs: Additional options

    Returns:
        Response object

    Example:
        >>> import cycletls
        >>> response = cycletls.post('https://api.example.com', json_data={'key': 'value'})
    """
    session = get_global_session()
    merged_kwargs = _merge_defaults(kwargs)
    return session.post(url, data=data, json_data=json_data, **merged_kwargs)


def put(
    url: str, data: Optional[Any] = None, json_data: Optional[Dict] = None, **kwargs
) -> "Response":
    """
    Make a PUT request using the global session with defaults.

    Args:
        url: Target URL
        data: Form data or raw body
        json_data: JSON payload
        **kwargs: Additional options

    Returns:
        Response object
    """
    session = get_global_session()
    merged_kwargs = _merge_defaults(kwargs)
    return session.put(url, data=data, json_data=json_data, **merged_kwargs)


def patch(
    url: str, data: Optional[Any] = None, json_data: Optional[Dict] = None, **kwargs
) -> "Response":
    """
    Make a PATCH request using the global session with defaults.

    Args:
        url: Target URL
        data: Form data or raw body
        json_data: JSON payload
        **kwargs: Additional options

    Returns:
        Response object
    """
    session = get_global_session()
    merged_kwargs = _merge_defaults(kwargs)
    return session.patch(url, data=data, json_data=json_data, **merged_kwargs)


def delete(url: str, **kwargs) -> "Response":
    """
    Make a DELETE request using the global session with defaults.

    Args:
        url: Target URL
        **kwargs: Additional options

    Returns:
        Response object
    """
    session = get_global_session()
    merged_kwargs = _merge_defaults(kwargs)
    return session.delete(url, **merged_kwargs)


def head(url: str, **kwargs) -> "Response":
    """
    Make a HEAD request using the global session with defaults.

    Args:
        url: Target URL
        **kwargs: Additional options

    Returns:
        Response object
    """
    session = get_global_session()
    merged_kwargs = _merge_defaults(kwargs)
    return session.head(url, **merged_kwargs)


def options(url: str, **kwargs) -> "Response":
    """
    Make an OPTIONS request using the global session with defaults.

    Args:
        url: Target URL
        **kwargs: Additional options

    Returns:
        Response object
    """
    session = get_global_session()
    merged_kwargs = _merge_defaults(kwargs)
    return session.options(url, **merged_kwargs)


# Async module-level convenience functions
# These work exactly like sync versions but with async/await


async def async_request(method: str, url: str, **kwargs) -> "Response":
    """
    Make an async HTTP request.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Target URL
        **kwargs: Additional request options

    Returns:
        Response object

    Example:
        >>> import cycletls
        >>> response = await cycletls.async_request('GET', 'https://example.com')
    """
    async with CycleTLS() as client:
        merged_kwargs = _merge_defaults(kwargs)
        return await client.arequest(method, url, **merged_kwargs)


async def aget(url: str, **kwargs) -> "Response":
    """
    Make an async GET request (use 'aget' or just 'get' with await).

    Args:
        url: Target URL
        **kwargs: Additional request options

    Returns:
        Response object

    Example:
        >>> import cycletls
        >>> response = await cycletls.aget('https://example.com')
        >>> # Or use the original function with await:
        >>> response = await cycletls.get(url)  # Will auto-detect async context
    """
    async with CycleTLS() as client:
        merged_kwargs = _merge_defaults(kwargs)
        return await client.aget(url, **merged_kwargs)


async def apost(
    url: str, data: Optional[Any] = None, json_data: Optional[Dict] = None, **kwargs
) -> "Response":
    """
    Make an async POST request.

    Args:
        url: Target URL
        data: Form data or raw body
        json_data: JSON payload
        **kwargs: Additional options

    Returns:
        Response object

    Example:
        >>> import cycletls
        >>> response = await cycletls.apost('https://api.example.com', json_data={'key': 'value'})
    """
    async with CycleTLS() as client:
        merged_kwargs = _merge_defaults(kwargs)
        return await client.apost(url, data=data, json_data=json_data, **merged_kwargs)


async def aput(
    url: str, data: Optional[Any] = None, json_data: Optional[Dict] = None, **kwargs
) -> "Response":
    """Make an async PUT request."""
    async with CycleTLS() as client:
        merged_kwargs = _merge_defaults(kwargs)
        return await client.aput(url, data=data, json_data=json_data, **merged_kwargs)


async def apatch(
    url: str, data: Optional[Any] = None, json_data: Optional[Dict] = None, **kwargs
) -> "Response":
    """Make an async PATCH request."""
    async with CycleTLS() as client:
        merged_kwargs = _merge_defaults(kwargs)
        return await client.apatch(url, data=data, json_data=json_data, **merged_kwargs)


async def adelete(url: str, **kwargs) -> "Response":
    """Make an async DELETE request."""
    async with CycleTLS() as client:
        merged_kwargs = _merge_defaults(kwargs)
        return await client.adelete(url, **merged_kwargs)


async def ahead(url: str, **kwargs) -> "Response":
    """Make an async HEAD request."""
    async with CycleTLS() as client:
        merged_kwargs = _merge_defaults(kwargs)
        return await client.ahead(url, **merged_kwargs)


async def aoptions(url: str, **kwargs) -> "Response":
    """Make an async OPTIONS request."""
    async with CycleTLS() as client:
        merged_kwargs = _merge_defaults(kwargs)
        return await client.aoptions(url, **merged_kwargs)


# Module-level __getattr__ for configuration access (Python 3.7+)
def __getattr__(name: str):
    """
    Dynamic attribute access for configuration.

    Supports reading default_* configuration attributes.
    """
    if name in _CONFIGURABLE_ATTRS:
        return _config.get(name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Export public API
__all__ = [
    # Version
    "__version__",
    # Core classes
    "CycleTLS",
    "AsyncCycleTLS",
    "Session",
    # Fingerprint plugin system
    "TLSFingerprint",
    "FingerprintRegistry",
    "CHROME_120",
    "CHROME_121",
    "FIREFOX_121",
    "SAFARI_17",
    "EDGE_120",
    "CHROME_ANDROID",
    "SAFARI_IOS",
    "load_fingerprints_from_dir",
    "load_fingerprints_from_env",
    "load_fingerprint_from_file",
    "create_fingerprint_template",
    # WebSocket support
    "MessageType",
    "WebSocketMessage",
    "WebSocketError",
    "WebSocketConnection",
    # SSE (Server-Sent Events) support
    "SSEEvent",
    "SSEError",
    "SSEConnection",
    # Convenience functions (sync)
    "request",
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "head",
    "options",
    # Convenience functions (async)
    "aget",
    "apost",
    "aput",
    "apatch",
    "adelete",
    "ahead",
    "aoptions",
    "async_request",
    "async_get",
    "async_post",
    "async_put",
    "async_delete",
    # Configuration
    "set_default",
    "reset_defaults",
    "get_default",
    "close_global_session",
    # Structures
    "CaseInsensitiveDict",
    "CookieJar",
    # Exceptions
    "CycleTLSError",
    "RequestException",
    "HTTPError",
    "ConnectionError",
    "Timeout",
    "TooManyRedirects",
    "InvalidURL",
    "TLSError",
    "ProxyError",
    "InvalidHeader",
    "ConnectTimeout",
    "ReadTimeout",
]
