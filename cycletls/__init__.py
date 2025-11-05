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

from typing import Optional, Dict, Any

# Import core classes
from .api import CycleTLS
from .async_api import AsyncCycleTLS, async_get, async_post, async_put, async_delete
from .sessions import Session
from .schema import *
from .exceptions import (
    CycleTLSError,
    RequestException,
    HTTPError,
    ConnectionError,
    Timeout,
    TooManyRedirects,
    InvalidURL,
    TLSError,
    ProxyError,
    InvalidHeader,
    ConnectTimeout,
    ReadTimeout,
)
from .structures import CaseInsensitiveDict, CookieJar

# Import global session management
from ._global import (
    get_global_session,
    close_global_session,
)

# Import configuration management
from ._config import (
    _config,
    _CONFIGURABLE_ATTRS,
    _merge_defaults,
    set_default,
    reset_defaults,
    get_default,
)


# Initialize default configuration on package import
set_default(enable_connection_reuse=True)


# Module-level convenience functions
def request(method: str, url: str, **kwargs) -> 'Response':
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


def get(url: str, **kwargs) -> 'Response':
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


def post(url: str, data: Optional[Any] = None, json_data: Optional[Dict] = None, **kwargs) -> 'Response':
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


def put(url: str, data: Optional[Any] = None, json_data: Optional[Dict] = None, **kwargs) -> 'Response':
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


def patch(url: str, data: Optional[Any] = None, json_data: Optional[Dict] = None, **kwargs) -> 'Response':
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


def delete(url: str, **kwargs) -> 'Response':
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


def head(url: str, **kwargs) -> 'Response':
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


def options(url: str, **kwargs) -> 'Response':
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

async def async_request(method: str, url: str, **kwargs) -> 'Response':
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
    async with AsyncCycleTLS() as client:
        merged_kwargs = _merge_defaults(kwargs)
        return await client.request(method, url, **merged_kwargs)


async def aget(url: str, **kwargs) -> 'Response':
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
    async with AsyncCycleTLS() as client:
        merged_kwargs = _merge_defaults(kwargs)
        return await client.get(url, **merged_kwargs)


async def apost(url: str, data: Optional[Any] = None, json_data: Optional[Dict] = None, **kwargs) -> 'Response':
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
    async with AsyncCycleTLS() as client:
        merged_kwargs = _merge_defaults(kwargs)
        return await client.post(url, data=data, json_data=json_data, **merged_kwargs)


async def aput(url: str, data: Optional[Any] = None, json_data: Optional[Dict] = None, **kwargs) -> 'Response':
    """Make an async PUT request."""
    async with AsyncCycleTLS() as client:
        merged_kwargs = _merge_defaults(kwargs)
        return await client.put(url, data=data, json_data=json_data, **merged_kwargs)


async def apatch(url: str, data: Optional[Any] = None, json_data: Optional[Dict] = None, **kwargs) -> 'Response':
    """Make an async PATCH request."""
    async with AsyncCycleTLS() as client:
        merged_kwargs = _merge_defaults(kwargs)
        return await client.patch(url, data=data, json_data=json_data, **merged_kwargs)


async def adelete(url: str, **kwargs) -> 'Response':
    """Make an async DELETE request."""
    async with AsyncCycleTLS() as client:
        merged_kwargs = _merge_defaults(kwargs)
        return await client.delete(url, **merged_kwargs)


async def ahead(url: str, **kwargs) -> 'Response':
    """Make an async HEAD request."""
    async with AsyncCycleTLS() as client:
        merged_kwargs = _merge_defaults(kwargs)
        return await client.head(url, **merged_kwargs)


async def aoptions(url: str, **kwargs) -> 'Response':
    """Make an async OPTIONS request."""
    async with AsyncCycleTLS() as client:
        merged_kwargs = _merge_defaults(kwargs)
        return await client.options(url, **merged_kwargs)


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
    # Core classes
    'CycleTLS',
    'AsyncCycleTLS',
    'Session',
    # Convenience functions (sync)
    'request',
    'get',
    'post',
    'put',
    'patch',
    'delete',
    'head',
    'options',
    # Convenience functions (async)
    'aget',
    'apost',
    'aput',
    'apatch',
    'adelete',
    'ahead',
    'aoptions',
    'async_request',
    # Configuration
    'set_default',
    'reset_defaults',
    'get_default',
    'close_global_session',
    # Structures
    'CaseInsensitiveDict',
    'CookieJar',
    # Exceptions
    'CycleTLSError',
    'RequestException',
    'HTTPError',
    'ConnectionError',
    'Timeout',
    'TooManyRedirects',
    'InvalidURL',
    'TLSError',
    'ProxyError',
    'InvalidHeader',
    'ConnectTimeout',
    'ReadTimeout',
]
