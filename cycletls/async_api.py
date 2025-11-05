"""Async API for CycleTLS - async/await interface matching the sync API."""

from __future__ import annotations

import json
import logging
import urllib.parse
import warnings
from typing import Any, Dict, Optional, Union

from .api import (
    _encode_multipart_formdata,
    _merge_url_params,
    _next_request_id,
    _dict_to_response,
    ParamsType,
)
from .exceptions import CycleTLSError
from .schema import Request, Cookie, Response
from . import _ffi

logger = logging.getLogger(__name__)


class AsyncCycleTLS:
    """
    Async HTTP client powered by CycleTLS with async/await support.

    Provides the same API as CycleTLS but with async methods for concurrent requests.

    Example:
        >>> async with AsyncCycleTLS() as client:
        ...     response = await client.get("https://api.example.com/data")
        ...     print(response.json())
    """

    def __init__(self):
        """Initialize an async CycleTLS client."""
        self._closed = False

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Async context manager exit."""
        await self.close()
        return False

    async def close(self) -> None:
        """Close the client (no-op retained for API compatibility)."""
        self._closed = True

    async def request(
        self,
        method: str,
        url: str,
        params: Optional[ParamsType] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        poll_interval: float = 0.0,
        timeout: float = 30.0,
        **kwargs: Any
    ) -> Response:
        """
        Send an async HTTP request with enhanced data handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Target URL
            params: Query parameters to append to URL
            data: Form data or raw body
            json_data: JSON data (auto-serialized)
            files: File uploads (multipart form data)
            poll_interval: Time between completion checks (default: 0s = tight loop)
            timeout: Maximum wait time for request completion (default: 30s)
            **kwargs: Additional CycleTLS options (headers, cookies, proxy, etc.)

        Returns:
            Response: Response object with status, headers, body, cookies, etc.
        """
        if self._closed:
            raise CycleTLSError("AsyncCycleTLS client is closed")

        # Handle deprecated body/body_bytes parameters
        if 'body' in kwargs:
            warnings.warn(
                "The 'body' parameter is deprecated. Use 'data' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            if data is None:
                data = kwargs.pop('body')

        if 'body_bytes' in kwargs:
            warnings.warn(
                "The 'body_bytes' parameter is deprecated. Use 'data' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            if data is None:
                data = kwargs.pop('body_bytes')

        headers = kwargs.get('headers') or {}
        if headers is None:
            headers = {}

        # Attach params to URL before building the request
        url = _merge_url_params(url, params)

        body_value: Optional[str] = None
        body_bytes_value: Optional[bytes] = None

        if json_data is not None:
            if data is not None:
                raise ValueError("Cannot specify both 'data' and 'json_data' parameters")
            body_value = json.dumps(json_data)
            headers['Content-Type'] = 'application/json'
        elif data is not None:
            if isinstance(data, dict):
                body_value = urllib.parse.urlencode(data)
                if 'Content-Type' not in headers:
                    headers['Content-Type'] = 'application/x-www-form-urlencoded'
            elif isinstance(data, bytes):
                body_bytes_value = data
            else:
                body_value = str(data)

        # Handle multipart form data with files
        if files is not None:
            # Extract form fields from data if it's a dict
            form_fields = None
            if isinstance(data, dict):
                form_fields = data
                data = None  # Clear data since it's now part of multipart

            # Encode multipart form data
            body_bytes_value, content_type = _encode_multipart_formdata(
                fields=form_fields,
                files=files
            )
            headers['Content-Type'] = content_type

        if body_value is not None:
            kwargs['body'] = body_value
        if body_bytes_value is not None:
            kwargs['body_bytes'] = body_bytes_value

        if headers:
            kwargs['headers'] = headers

        # Simplify cookie input - handle dict or CookieJar
        if 'cookies' in kwargs and kwargs['cookies'] is not None:
            cookies = kwargs['cookies']
            if isinstance(cookies, dict):
                kwargs['cookies'] = [Cookie(name=str(k), value=str(v)) for k, v in cookies.items()]
            elif hasattr(cookies, '_cookies'):
                kwargs['cookies'] = list(cookies._cookies.values())

        request_model = Request(method=method, url=url, **kwargs)
        request_payload = request_model.to_dict()

        payload = {
            "requestId": _next_request_id(),
            "options": request_payload,
        }

        # Log outgoing request
        logger.debug(f"Sending async {method.upper()} request to {url}")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Request headers: {headers}")
            if 'proxy' in kwargs and kwargs['proxy']:
                logger.debug(f"Using proxy: {kwargs['proxy']}")

        try:
            response_data = await _ffi.send_request_async(payload, poll_interval, timeout)
        except Exception as exc:  # pragma: no cover - unexpected backend failure
            logger.error(f"Async request to {url} failed: {exc}")
            raise CycleTLSError(f"Failed to execute async CycleTLS request: {exc}") from exc

        if not isinstance(response_data, dict):
            logger.error("Invalid response payload received from CycleTLS backend")
            raise CycleTLSError("Invalid response payload received from CycleTLS backend")

        try:
            response = _dict_to_response(response_data)
            # Log response
            logger.debug(f"Received async response: {response.status_code} {response.reason}")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Response headers: {dict(response.headers)}")
            return response
        except Exception as exc:  # pragma: no cover - validation error
            logger.error(f"Failed to parse async response: {exc}")
            raise CycleTLSError(f"Failed to parse async CycleTLS response: {exc}") from exc

    async def get(self, url, params=None, **kwargs) -> Response:
        """Sends an async GET request."""
        return await self.request("get", url, params=params, **kwargs)

    async def options(self, url, params=None, **kwargs) -> Response:
        """Sends an async OPTIONS request."""
        return await self.request("options", url, params=params, **kwargs)

    async def head(self, url, params=None, **kwargs) -> Response:
        """Sends an async HEAD request."""
        return await self.request("head", url, params=params, **kwargs)

    async def post(self, url, params=None, data=None, json_data=None, **kwargs) -> Response:
        """Sends an async POST request."""
        return await self.request("post", url, params=params, data=data, json_data=json_data, **kwargs)

    async def put(self, url, params=None, data=None, json_data=None, **kwargs) -> Response:
        """Sends an async PUT request."""
        return await self.request("put", url, params=params, data=data, json_data=json_data, **kwargs)

    async def patch(self, url, params=None, data=None, json_data=None, **kwargs) -> Response:
        """Sends an async PATCH request."""
        return await self.request("patch", url, params=params, data=data, json_data=json_data, **kwargs)

    async def delete(self, url, params=None, **kwargs) -> Response:
        """Sends an async DELETE request."""
        return await self.request("delete", url, params=params, **kwargs)


# Convenience functions for quick requests
async def async_get(url, params=None, **kwargs) -> Response:
    """Send an async GET request (convenience function)."""
    async with AsyncCycleTLS() as client:
        return await client.get(url, params=params, **kwargs)


async def async_post(url, params=None, data=None, json_data=None, **kwargs) -> Response:
    """Send an async POST request (convenience function)."""
    async with AsyncCycleTLS() as client:
        return await client.post(url, params=params, data=data, json_data=json_data, **kwargs)


async def async_put(url, params=None, data=None, json_data=None, **kwargs) -> Response:
    """Send an async PUT request (convenience function)."""
    async with AsyncCycleTLS() as client:
        return await client.put(url, params=params, data=data, json_data=json_data, **kwargs)


async def async_delete(url, params=None, **kwargs) -> Response:
    """Send an async DELETE request (convenience function)."""
    async with AsyncCycleTLS() as client:
        return await client.delete(url, params=params, **kwargs)


__all__ = [
    "AsyncCycleTLS",
    "async_get",
    "async_post",
    "async_put",
    "async_delete",
]
