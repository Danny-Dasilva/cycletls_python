"""Core CycleTLS client implementation backed by the Go shared library."""

from __future__ import annotations

import io
import json
import logging
import mimetypes
import threading
import urllib.parse
import warnings
from collections.abc import Mapping, Sequence
from types import TracebackType
from typing import Any, Dict, Iterable, Literal, Optional, Tuple, Union

from ._ffi import _has_callback_support
from ._ffi import send_batch_request as ffi_send_batch_request
from ._ffi import send_request as ffi_send_request
from ._ffi import send_request_async as ffi_send_request_async
from ._ffi import send_request_async_callback as ffi_send_request_async_callback
from ._ffi import send_requests_batch as ffi_send_requests_batch
from .exceptions import CycleTLSError
from .fingerprints import FingerprintRegistry, TLSFingerprint
from .schema import Request, Response, _dict_to_response

# Setup module logger
logger = logging.getLogger(__name__)

# Request ID counter (faster than UUID) - use thread-local for zero-lock overhead
_request_counter_local = threading.local()


def _next_request_id() -> str:
    """Generate next request ID using thread-local counter (no locks needed)."""
    if not hasattr(_request_counter_local, "counter"):
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
    fields: Optional[Dict[str, Any]] = None, files: Optional[Dict[str, Any]] = None
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
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex[:16]}"
    body = io.BytesIO()

    # Add form fields
    if fields:
        for field_name, field_value in fields.items():
            body.write(f"--{boundary}\r\n".encode("utf-8"))
            body.write(
                f'Content-Disposition: form-data; name="{field_name}"\r\n\r\n'.encode("utf-8")
            )
            body.write(str(field_value).encode("utf-8"))
            body.write(b"\r\n")

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
                filename = getattr(file_obj, "name", field_name)
                content_type = None

            # Guess content type if not provided
            if content_type is None:
                content_type, _ = mimetypes.guess_type(filename)
                if content_type is None:
                    content_type = "application/octet-stream"

            # Read file data
            if hasattr(file_obj, "read"):
                file_data = file_obj.read()
                # Reset file pointer if possible
                if hasattr(file_obj, "seek"):
                    try:
                        file_obj.seek(0)
                    except (OSError, io.UnsupportedOperation):
                        pass
            else:
                # file_obj is already bytes
                file_data = file_obj

            # Write file part
            body.write(f"--{boundary}\r\n".encode("utf-8"))
            body.write(
                f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode(
                    "utf-8"
                )
            )
            body.write(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))

            # Ensure file_data is bytes
            if isinstance(file_data, str):
                file_data = file_data.encode("utf-8")
            body.write(file_data)
            body.write(b"\r\n")

    # Write final boundary
    body.write(f"--{boundary}--\r\n".encode("utf-8"))

    content_type_header = f"multipart/form-data; boundary={boundary}"
    return body.getvalue(), content_type_header


class CycleTLS:
    """CycleTLS client for making HTTP requests with advanced TLS fingerprinting."""

    def __init__(self) -> None:
        """Initialize CycleTLS client."""
        self._closed = False

    def __enter__(self) -> "CycleTLS":
        """Allow usage as a context manager."""
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Literal[False]:
        """Cleanup resources when exiting a context manager block."""
        self.close()
        return False

    async def __aenter__(self) -> "CycleTLS":
        """Allow usage as an async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Literal[False]:
        """Cleanup resources when exiting an async context manager block."""
        await self.aclose()
        return False

    def __del__(self) -> None:  # pragma: no cover - best-effort cleanup
        # Directly set _closed to avoid issues with subclasses that override
        # close() as a coroutine (e.g. AsyncCycleTLS).
        try:
            self._closed = True
        except Exception:
            pass

    def close(self) -> None:
        """Close the client (no-op retained for API compatibility)."""
        self._closed = True

    async def aclose(self) -> None:
        """Async close for httpx-compatible async cleanup.

        This is the async counterpart of :meth:`close`. It allows usage with
        async cleanup patterns like ``await client.aclose()``.

        Directly sets ``_closed`` rather than calling :meth:`close` so that
        subclasses that override ``close()`` as a coroutine (e.g.
        ``AsyncCycleTLS``) work without needing to be awaited separately.
        """
        self._closed = True

    # ------------------------------------------------------------------
    # Shared request preparation (used by both sync and async paths)
    # ------------------------------------------------------------------

    def _prepare_request(
        self,
        method: str,
        url: str,
        params: Optional[ParamsType] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        fingerprint: Optional[Union[str, TLSFingerprint]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Prepare a request payload dict without sending it.

        This method handles all parameter normalisation (fingerprints, deprecated
        body params, header extraction, cookie conversion, multipart encoding,
        etc.) and returns the payload ready for the FFI layer.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Target URL
            params: Query parameters to append to URL
            data: Form data or raw body
            json_data: JSON data (auto-serialized)
            files: File uploads (multipart form data)
            fingerprint: TLS fingerprint profile name or TLSFingerprint instance.
            **kwargs: Additional CycleTLS options (headers, cookies, proxy, etc.)

        Returns:
            Payload dictionary suitable for ``ffi_send_request`` /
            ``ffi_send_request_async``.
        """
        if self._closed:
            raise CycleTLSError("CycleTLS client is closed")

        # Apply fingerprint profile if provided
        if fingerprint is not None:
            if isinstance(fingerprint, str):
                fingerprint = FingerprintRegistry.get(fingerprint)
            kwargs = fingerprint.apply_to_kwargs(kwargs)

        # Handle deprecated body/body_bytes parameters
        if "body" in kwargs:
            warnings.warn(
                "The 'body' parameter is deprecated. Use 'data' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            if data is None:
                data = kwargs.pop("body")

        if "body_bytes" in kwargs:
            warnings.warn(
                "The 'body_bytes' parameter is deprecated. Use 'data' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            if data is None:
                data = kwargs.pop("body_bytes")

        headers = kwargs.get("headers") or {}

        # If User-Agent is in headers dict, it should override the user_agent parameter
        # Check case-insensitively
        for key, value in list(headers.items()):
            if key.lower() == "user-agent":
                kwargs["user_agent"] = value
                # Remove from headers since it's handled separately by the Go library
                del headers[key]
                break

        # Attach params to URL before building the request
        url = _merge_url_params(url, params)

        body_value: Optional[str] = None
        body_bytes_value: Optional[bytes] = None

        if json_data is not None:
            if data is not None:
                raise ValueError("Cannot specify both 'data' and 'json_data' parameters")
            body_value = json.dumps(json_data)
            headers["Content-Type"] = "application/json"
        elif data is not None:
            if isinstance(data, dict):
                body_value = urllib.parse.urlencode(data)
                if "Content-Type" not in headers:
                    headers["Content-Type"] = "application/x-www-form-urlencoded"
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
                fields=form_fields, files=files
            )
            headers["Content-Type"] = content_type

        if body_value is not None:
            kwargs["body"] = body_value
        if body_bytes_value is not None:
            kwargs["body_bytes"] = body_bytes_value

        if headers:
            kwargs["headers"] = headers

        # Simplify cookie input - handle dict, list of dicts, or CookieJar
        if "cookies" in kwargs and kwargs["cookies"] is not None:
            cookies = kwargs["cookies"]
            if isinstance(cookies, dict):
                from .schema import Cookie

                kwargs["cookies"] = [Cookie(name=str(k), value=str(v)) for k, v in cookies.items()]
            elif isinstance(cookies, list):
                from .schema import Cookie

                # Convert list of dicts to list of Cookie objects
                converted = []
                for c in cookies:
                    if isinstance(c, dict):
                        # Handle dict format: {"name": "...", "value": "...", ...}
                        converted.append(
                            Cookie(
                                name=c.get("name", ""),
                                value=c.get("value", ""),
                                path=c.get("path"),
                                domain=c.get("domain"),
                                expires=None,  # Would need datetime parsing if provided
                                max_age=c.get("max_age") or c.get("maxAge"),
                                secure=c.get("secure", False),
                                http_only=c.get("http_only") or c.get("httpOnly", False),
                                same_site=c.get("same_site") or c.get("sameSite"),
                            )
                        )
                    else:
                        # Already a Cookie object
                        converted.append(c)
                kwargs["cookies"] = converted
            elif hasattr(cookies, "_cookies"):
                kwargs["cookies"] = list(cookies._cookies.values())

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
            if "proxy" in kwargs and kwargs["proxy"]:
                logger.debug(f"Using proxy: {kwargs['proxy']}")

        return payload

    @staticmethod
    def _parse_response(response_data: Dict[str, Any], url: str = "") -> Response:
        """Convert raw FFI response data into a Response object.

        Args:
            response_data: Raw dict from the FFI layer.
            url: Original request URL (for error messages).

        Returns:
            Parsed Response object.
        """
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
        except CycleTLSError:
            # Re-raise our custom exceptions (includes exceptions from schema.py error handling)
            raise
        except Exception as exc:  # pragma: no cover - validation error
            logger.error(f"Failed to parse response: {exc}")
            raise CycleTLSError(f"Failed to parse CycleTLS response: {exc}") from exc

    # ------------------------------------------------------------------
    # Synchronous request methods
    # ------------------------------------------------------------------

    def request(
        self,
        method: str,
        url: str,
        params: Optional[ParamsType] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        fingerprint: Optional[Union[str, TLSFingerprint]] = None,
        **kwargs: Any,
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
            fingerprint: TLS fingerprint profile name or TLSFingerprint instance.
                        If a string, looks up the profile in FingerprintRegistry.
                        Applies the profile's ja3, user_agent, header_order, etc.
            **kwargs: Additional CycleTLS options (headers, cookies, proxy, etc.)

        Returns:
            Response: Response object with status, headers, body, cookies, etc.

        Example:
            >>> # Use a built-in fingerprint profile
            >>> response = client.get("https://example.com", fingerprint="chrome_120")
            >>>
            >>> # Or use a custom TLSFingerprint instance
            >>> from cycletls.fingerprints import TLSFingerprint
            >>> custom = TLSFingerprint(name="custom", ja3="...", user_agent="Custom/1.0")
            >>> response = client.get("https://example.com", fingerprint=custom)
        """
        payload = self._prepare_request(
            method, url, params=params, data=data, json_data=json_data,
            files=files, fingerprint=fingerprint, **kwargs,
        )

        try:
            response_data = ffi_send_request(payload)
        except Exception as exc:  # pragma: no cover - unexpected backend failure
            logger.error(f"Request to {url} failed: {exc}")
            raise CycleTLSError(f"Failed to execute CycleTLS request: {exc}") from exc

        return self._parse_response(response_data, url)

    def get(self, url, params=None, fingerprint=None, **kwargs) -> Response:
        """Sends a GET request."""
        return self.request("get", url, params=params, fingerprint=fingerprint, **kwargs)

    def options(self, url, params=None, fingerprint=None, **kwargs) -> Response:
        """Sends an OPTIONS request."""
        return self.request("options", url, params=params, fingerprint=fingerprint, **kwargs)

    def head(self, url, params=None, fingerprint=None, **kwargs) -> Response:
        """Sends a HEAD request."""
        return self.request("head", url, params=params, fingerprint=fingerprint, **kwargs)

    def post(
        self, url, params=None, data=None, json_data=None, fingerprint=None, **kwargs
    ) -> Response:
        """Sends a POST request."""
        return self.request(
            "post",
            url,
            params=params,
            data=data,
            json_data=json_data,
            fingerprint=fingerprint,
            **kwargs,
        )

    def put(
        self, url, params=None, data=None, json_data=None, fingerprint=None, **kwargs
    ) -> Response:
        """Sends a PUT request."""
        return self.request(
            "put",
            url,
            params=params,
            data=data,
            json_data=json_data,
            fingerprint=fingerprint,
            **kwargs,
        )

    def patch(
        self, url, params=None, data=None, json_data=None, fingerprint=None, **kwargs
    ) -> Response:
        """Sends a PATCH request."""
        return self.request(
            "patch",
            url,
            params=params,
            data=data,
            json_data=json_data,
            fingerprint=fingerprint,
            **kwargs,
        )

    def delete(self, url, params=None, fingerprint=None, **kwargs) -> Response:
        """Sends a DELETE request."""
        return self.request("delete", url, params=params, fingerprint=fingerprint, **kwargs)

    def batch(self, requests: list[dict]) -> list[Response]:
        """Send multiple requests in a single batch.

        This is more efficient than individual requests for high-throughput scenarios
        because it amortizes FFI call overhead across all requests. Requests are
        executed in parallel on the Go side.

        Args:
            requests: List of request dictionaries. Each dict should contain:
                - url (required): Target URL
                - method (required): HTTP method (GET, POST, etc.)
                - params (optional): Query parameters
                - data (optional): Form data or raw body
                - json_data (optional): JSON data (auto-serialized)
                - headers (optional): Custom headers
                - And any other CycleTLS options (ja3, proxy, timeout, etc.)

        Returns:
            List of Response objects in the same order as input requests.

        Raises:
            CycleTLSError: If the client is closed or batch request fails.

        Example:
            >>> with CycleTLS() as client:
            ...     responses = client.batch([
            ...         {"url": "https://api.example.com/users", "method": "GET"},
            ...         {"url": "https://api.example.com/posts", "method": "GET"},
            ...         {"url": "https://api.example.com/data", "method": "POST", "json_data": {"key": "value"}},
            ...     ])
            ...     for resp in responses:
            ...         print(resp.status_code)
        """
        if self._closed:
            raise CycleTLSError("CycleTLS client is closed")

        if not requests:
            return []

        # Build payloads for each request
        payloads = []
        for i, req in enumerate(requests):
            payload = self._build_batch_payload(req, request_id=f"batch_{i}")
            payloads.append(payload)

        logger.debug(f"Sending batch of {len(payloads)} requests")

        try:
            response_data_list = ffi_send_batch_request(payloads)
        except Exception as exc:  # pragma: no cover - unexpected backend failure
            logger.error(f"Batch request failed: {exc}")
            raise CycleTLSError(f"Failed to execute batch request: {exc}") from exc

        return [self._parse_response(rd) for rd in response_data_list]

    def _build_batch_payload(self, req: dict, request_id: str) -> dict:
        """Build a payload dict for a batch request item.

        Args:
            req: Request dictionary with url, method, and optional parameters.
            request_id: Unique ID for this request in the batch.

        Returns:
            Payload dictionary ready for FFI serialization.
        """
        url = req.get("url", "")
        method = req.get("method", "GET")
        params = req.get("params")
        data = req.get("data")
        json_data = req.get("json_data")
        headers = dict(req.get("headers") or {})

        # Attach params to URL
        url = _merge_url_params(url, params)

        body_value: Optional[str] = None
        body_bytes_value: Optional[bytes] = None

        if json_data is not None:
            if data is not None:
                raise ValueError("Cannot specify both 'data' and 'json_data' in batch request")
            body_value = json.dumps(json_data)
            headers["Content-Type"] = "application/json"
        elif data is not None:
            if isinstance(data, dict):
                body_value = urllib.parse.urlencode(data)
                if "Content-Type" not in headers:
                    headers["Content-Type"] = "application/x-www-form-urlencoded"
            elif isinstance(data, bytes):
                body_bytes_value = data
            else:
                body_value = str(data)

        # Build options dict - extract known CycleTLS options from req
        options = {
            "url": url,
            "method": method,
            "headers": headers,
            "body": body_value or "",
            "ja3": req.get(
                "ja3",
                (
                    "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-"
                    "49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,"
                    "29-23-24-25-256-257,0"
                ),
            ),
            "userAgent": req.get(
                "user_agent",
                "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0",
            ),
            "timeout": req.get("timeout", 30),
            "proxy": req.get("proxy", ""),
            "disableRedirect": req.get("disable_redirect", False),
            "insecureSkipVerify": req.get("insecure_skip_verify", False),
        }

        if body_bytes_value is not None:
            options["bodyBytes"] = body_bytes_value

        return {
            "requestId": request_id,
            "options": options,
        }

    # ------------------------------------------------------------------
    # Asynchronous request methods
    # ------------------------------------------------------------------

    async def arequest(
        self,
        method: str,
        url: str,
        params: Optional[ParamsType] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        fingerprint: Optional[Union[str, TLSFingerprint]] = None,
        poll_interval: float = 0.0,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> Response:
        """Send an async HTTP request with enhanced data handling.

        This is the async counterpart of :meth:`request`. It shares the same
        request preparation logic and adds async-specific polling parameters.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Target URL
            params: Query parameters to append to URL
            data: Form data or raw body
            json_data: JSON data (auto-serialized)
            files: File uploads (multipart form data)
            fingerprint: TLS fingerprint profile name or TLSFingerprint instance.
            poll_interval: Time between completion checks (default: 0s = adaptive)
            timeout: Maximum wait time for request completion (default: 30s)
            **kwargs: Additional CycleTLS options (headers, cookies, proxy, etc.)

        Returns:
            Response: Response object with status, headers, body, cookies, etc.
        """
        payload = self._prepare_request(
            method, url, params=params, data=data, json_data=json_data,
            files=files, fingerprint=fingerprint, **kwargs,
        )

        try:
            # Use callback-based async (zero-copy, pipe notification) when available,
            # fall back to polling-based async otherwise
            if _has_callback_support():
                try:
                    response_data = await ffi_send_request_async_callback(payload, timeout)
                except RuntimeError:
                    # Callback path can fail under heavy concurrent load (Go-side
                    # race with HTTP/2 stream cancellation). Fall back to polling.
                    logger.debug("Callback async failed, falling back to polling")
                    response_data = await ffi_send_request_async(payload, poll_interval, timeout)
            else:
                response_data = await ffi_send_request_async(payload, poll_interval, timeout)
        except Exception as exc:  # pragma: no cover - unexpected backend failure
            logger.error(f"Async request to {url} failed: {exc}")
            raise CycleTLSError(f"Failed to execute async CycleTLS request: {exc}") from exc

        return self._parse_response(response_data, url)

    async def aget(self, url, params=None, fingerprint=None, **kwargs) -> Response:
        """Sends an async GET request."""
        return await self.arequest("get", url, params=params, fingerprint=fingerprint, **kwargs)

    async def aoptions(self, url, params=None, fingerprint=None, **kwargs) -> Response:
        """Sends an async OPTIONS request."""
        return await self.arequest("options", url, params=params, fingerprint=fingerprint, **kwargs)

    async def ahead(self, url, params=None, fingerprint=None, **kwargs) -> Response:
        """Sends an async HEAD request."""
        return await self.arequest("head", url, params=params, fingerprint=fingerprint, **kwargs)

    async def apost(
        self, url, params=None, data=None, json_data=None, fingerprint=None, **kwargs
    ) -> Response:
        """Sends an async POST request."""
        return await self.arequest(
            "post", url, params=params, data=data, json_data=json_data,
            fingerprint=fingerprint, **kwargs,
        )

    async def aput(
        self, url, params=None, data=None, json_data=None, fingerprint=None, **kwargs
    ) -> Response:
        """Sends an async PUT request."""
        return await self.arequest(
            "put", url, params=params, data=data, json_data=json_data,
            fingerprint=fingerprint, **kwargs,
        )

    async def apatch(
        self, url, params=None, data=None, json_data=None, fingerprint=None, **kwargs
    ) -> Response:
        """Sends an async PATCH request."""
        return await self.arequest(
            "patch", url, params=params, data=data, json_data=json_data,
            fingerprint=fingerprint, **kwargs,
        )

    async def adelete(self, url, params=None, fingerprint=None, **kwargs) -> Response:
        """Sends an async DELETE request."""
        return await self.arequest("delete", url, params=params, fingerprint=fingerprint, **kwargs)

    async def abatch(self, requests: list[dict]) -> list[Response]:
        """Send multiple requests concurrently as an async batch.

        Each request is submitted asynchronously and all run in parallel.

        Args:
            requests: List of request dictionaries (same format as :meth:`batch`).

        Returns:
            List of Response objects in the same order as input requests.

        Raises:
            CycleTLSError: If the client is closed or any request fails.
        """
        if self._closed:
            raise CycleTLSError("CycleTLS client is closed")

        if not requests:
            return []

        # Build payloads for each request
        payloads = []
        for i, req in enumerate(requests):
            payload = self._build_batch_payload(req, request_id=f"batch_{i}")
            payloads.append(payload)

        logger.debug(f"Sending async batch of {len(payloads)} requests")

        try:
            response_data_list = await ffi_send_requests_batch(payloads)
        except Exception as exc:  # pragma: no cover - unexpected backend failure
            logger.error(f"Async batch request failed: {exc}")
            raise CycleTLSError(f"Failed to execute async batch request: {exc}") from exc

        return [self._parse_response(rd) for rd in response_data_list]
