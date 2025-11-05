"""Core CycleTLS client implementation backed by the Go shared library."""

from __future__ import annotations

import io
import mimetypes
import os
import urllib.parse
import json
import warnings
import logging
import threading
from collections.abc import Mapping, Sequence
from typing import Any, BinaryIO, Dict, Iterable, Optional, Tuple, Union

from ._ffi import send_request as ffi_send_request
from .exceptions import CycleTLSError
from .schema import Request, Response, _dict_to_response

# Setup module logger
logger = logging.getLogger(__name__)

# Request ID counter (faster than UUID) - use thread-local for zero-lock overhead
_request_counter_local = threading.local()


def _next_request_id() -> str:
    """Generate next request ID using thread-local counter (no locks needed)."""
    if not hasattr(_request_counter_local, 'counter'):
        _request_counter_local.counter = 0
    _request_counter_local.counter += 1
    # Include thread ID for uniqueness across threads
    return f"req_{threading.current_thread().ident}_{_request_counter_local.counter}"


ParamValue = Union[str, int, float, bool, None]
ParamsType = Union[
    Mapping[str, Union[ParamValue, Sequence[ParamValue]]],
    Sequence[Tuple[str, Union[ParamValue, Sequence[ParamValue]]]],
]


def _merge_url_params(url: str, params: Optional[ParamsType]) -> str:
    """Attach query parameters to a URL, preserving existing values."""
    if not params:
        return url

    parsed = urllib.parse.urlsplit(url)
    existing = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)

    def iter_params() -> Iterable[Tuple[str, str]]:
        source: Iterable[Tuple[Any, Any]]
        if isinstance(params, Mapping):
            source = params.items()
        else:
            source = params

        for key, value in source:
            if value is None:
                continue

            if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
                for item in value:
                    if item is None:
                        continue
                    yield str(key), str(item)
            else:
                yield str(key), str(value)

    combined = existing + list(iter_params())
    query = urllib.parse.urlencode(combined, doseq=True)
    return urllib.parse.urlunsplit(parsed._replace(query=query))


def _encode_multipart_formdata(
    fields: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None
) -> Tuple[bytes, str]:
    """
    Encode data and files as multipart/form-data.

    Args:
        fields: Dictionary of form fields
        files: Dictionary of files to upload
            Format: {'field_name': file_object} or
                   {'field_name': ('filename', file_object)} or
                   {'field_name': ('filename', file_object, 'content_type')}

    Returns:
        Tuple of (body_bytes, content_type_header)
    """
    import uuid

    # Generate unique boundary
    boundary = f'----WebKitFormBoundary{uuid.uuid4().hex[:16]}'
    body = io.BytesIO()

    # Add form fields
    if fields:
        for field_name, field_value in fields.items():
            body.write(f'--{boundary}\r\n'.encode('utf-8'))
            body.write(f'Content-Disposition: form-data; name="{field_name}"\r\n\r\n'.encode('utf-8'))
            body.write(str(field_value).encode('utf-8'))
            body.write(b'\r\n')

    # Add files
    if files:
        for field_name, file_info in files.items():
            # Parse file_info
            if isinstance(file_info, tuple):
                if len(file_info) == 2:
                    filename, file_obj = file_info
                    content_type = None
                elif len(file_info) == 3:
                    filename, file_obj, content_type = file_info
                else:
                    raise ValueError(f"Invalid file info format for field '{field_name}'")
            else:
                # file_info is a file object
                file_obj = file_info
                filename = getattr(file_obj, 'name', field_name)
                content_type = None

            # Guess content type if not provided
            if content_type is None:
                content_type, _ = mimetypes.guess_type(filename)
                if content_type is None:
                    content_type = 'application/octet-stream'

            # Read file data
            if hasattr(file_obj, 'read'):
                file_data = file_obj.read()
                # Reset file pointer if possible
                if hasattr(file_obj, 'seek'):
                    try:
                        file_obj.seek(0)
                    except (OSError, io.UnsupportedOperation):
                        pass
            else:
                # file_obj is already bytes
                file_data = file_obj

            # Write file part
            body.write(f'--{boundary}\r\n'.encode('utf-8'))
            body.write(
                f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode('utf-8')
            )
            body.write(f'Content-Type: {content_type}\r\n\r\n'.encode('utf-8'))

            # Ensure file_data is bytes
            if isinstance(file_data, str):
                file_data = file_data.encode('utf-8')
            body.write(file_data)
            body.write(b'\r\n')

    # Write final boundary
    body.write(f'--{boundary}--\r\n'.encode('utf-8'))

    content_type_header = f'multipart/form-data; boundary={boundary}'
    return body.getvalue(), content_type_header


class CycleTLS:
    """CycleTLS client for making HTTP requests with advanced TLS fingerprinting."""

    def __init__(self, port: int = 9112) -> None:
        """
        Initialize CycleTLS client.

        Args:
            port: Retained for backward compatibility; no longer used.
        """
        self.port = port
        self._closed = False

    def __enter__(self) -> "CycleTLS":
        """Allow usage as a context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Cleanup resources when exiting a context manager block."""
        self.close()
        return False

    def __del__(self) -> None:  # pragma: no cover - best-effort cleanup
        try:
            self.close()
        except Exception:
            pass

    def close(self) -> None:
        """Close the client (no-op retained for API compatibility)."""
        self._closed = True

    def request(
        self,
        method: str,
        url: str,
        params: Optional[ParamsType] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Response:
        """
        Send an HTTP request with enhanced data handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Target URL
            params: Query parameters to append to URL
            data: Form data or raw body
            json_data: JSON data (auto-serialized)
            files: File uploads (not yet supported)
            **kwargs: Additional CycleTLS options (headers, cookies, proxy, etc.)

        Returns:
            Response: Response object with status, headers, body, cookies, etc.
        """
        if self._closed:
            raise CycleTLSError("CycleTLS client is closed")

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
                from .schema import Cookie

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
        logger.debug(f"Sending {method.upper()} request to {url}")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Request headers: {headers}")
            if 'proxy' in kwargs and kwargs['proxy']:
                logger.debug(f"Using proxy: {kwargs['proxy']}")

        try:
            response_data = ffi_send_request(payload)
        except Exception as exc:  # pragma: no cover - unexpected backend failure
            logger.error(f"Request to {url} failed: {exc}")
            raise CycleTLSError(f"Failed to execute CycleTLS request: {exc}") from exc

        if not isinstance(response_data, dict):
            logger.error("Invalid response payload received from CycleTLS backend")
            raise CycleTLSError("Invalid response payload received from CycleTLS backend")

        try:
            response = _dict_to_response(response_data)
            # Log response
            logger.debug(f"Received response: {response.status_code} {response.reason}")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Response headers: {dict(response.headers)}")
            return response
        except Exception as exc:  # pragma: no cover - validation error
            logger.error(f"Failed to parse response: {exc}")
            raise CycleTLSError(f"Failed to parse CycleTLS response: {exc}") from exc

    def get(self, url, params=None, **kwargs) -> Response:
        """Sends a GET request."""
        return self.request("get", url, params=params, **kwargs)

    def options(self, url, params=None, **kwargs) -> Response:
        """Sends an OPTIONS request."""
        return self.request("options", url, params=params, **kwargs)

    def head(self, url, params=None, **kwargs) -> Response:
        """Sends a HEAD request."""
        return self.request("head", url, params=params, **kwargs)

    def post(self, url, params=None, data=None, json_data=None, **kwargs) -> Response:
        """Sends a POST request."""
        return self.request("post", url, params=params, data=data, json_data=json_data, **kwargs)

    def put(self, url, params=None, data=None, json_data=None, **kwargs) -> Response:
        """Sends a PUT request."""
        return self.request("put", url, params=params, data=data, json_data=json_data, **kwargs)

    def patch(self, url, params=None, data=None, json_data=None, **kwargs) -> Response:
        """Sends a PATCH request."""
        return self.request("patch", url, params=params, data=data, json_data=json_data, **kwargs)

    def delete(self, url, params=None, **kwargs) -> Response:
        """Sends a DELETE request."""
        return self.request("delete", url, params=params, **kwargs)

