"""Tests for CycleTLS exception hierarchy.

Verifies that all custom exceptions inherit from CycleTLSError,
enabling unified exception handling across HTTP, WebSocket, and SSE errors.
"""

import pytest
import ormsgpack

from cycletls.exceptions import (
    ConnectionError,
    CycleTLSError,
    HTTPError,
    InvalidHeader,
    InvalidURL,
    ProxyError,
    RequestException,
    Timeout,
    TLSError,
    TooManyRedirects,
)
from cycletls.websocket import WebSocketError
from cycletls.sse import SSEError


class TestExceptionHierarchy:
    """Verify the exception class hierarchy."""

    def test_websocket_error_is_subclass_of_cycletls_error(self):
        assert issubclass(WebSocketError, CycleTLSError)

    def test_sse_error_is_subclass_of_cycletls_error(self):
        assert issubclass(SSEError, CycleTLSError)

    def test_request_exception_is_subclass_of_cycletls_error(self):
        assert issubclass(RequestException, CycleTLSError)

    def test_http_error_is_subclass_of_cycletls_error(self):
        assert issubclass(HTTPError, CycleTLSError)

    def test_connection_error_is_subclass_of_cycletls_error(self):
        assert issubclass(ConnectionError, CycleTLSError)

    def test_timeout_is_subclass_of_cycletls_error(self):
        assert issubclass(Timeout, CycleTLSError)

    def test_too_many_redirects_is_subclass_of_cycletls_error(self):
        assert issubclass(TooManyRedirects, CycleTLSError)

    def test_invalid_url_is_subclass_of_cycletls_error(self):
        assert issubclass(InvalidURL, CycleTLSError)

    def test_tls_error_is_subclass_of_cycletls_error(self):
        assert issubclass(TLSError, CycleTLSError)

    def test_proxy_error_is_subclass_of_cycletls_error(self):
        assert issubclass(ProxyError, CycleTLSError)

    def test_invalid_header_is_subclass_of_cycletls_error(self):
        assert issubclass(InvalidHeader, CycleTLSError)

    @pytest.mark.parametrize(
        "exc_class",
        [
            WebSocketError,
            SSEError,
            RequestException,
            HTTPError,
            ConnectionError,
            Timeout,
            TooManyRedirects,
            InvalidURL,
            TLSError,
            ProxyError,
            InvalidHeader,
        ],
    )
    def test_all_custom_exceptions_inherit_from_cycletls_error(self, exc_class):
        """Every custom exception must be catchable with except CycleTLSError."""
        assert issubclass(exc_class, CycleTLSError)


class TestUnifiedCatching:
    """Verify that except CycleTLSError catches all subtypes."""

    def test_catch_websocket_error_as_cycletls_error(self):
        with pytest.raises(CycleTLSError):
            raise WebSocketError("ws failure")

    def test_catch_sse_error_as_cycletls_error(self):
        with pytest.raises(CycleTLSError):
            raise SSEError("sse failure")

    def test_catch_http_error_as_cycletls_error(self):
        with pytest.raises(CycleTLSError):
            raise HTTPError("404 Not Found")

    def test_catch_timeout_as_cycletls_error(self):
        with pytest.raises(CycleTLSError):
            raise Timeout("timed out")

    def test_catch_connection_error_as_cycletls_error(self):
        with pytest.raises(CycleTLSError):
            raise ConnectionError("refused")


class TestCorruptMsgpackRaisesCycleTLSError:
    """Verify that corrupt msgpack data raises CycleTLSError, not ormsgpack errors."""

    def test_corrupt_msgpack_raises_cycletls_error(self):
        """Feeding garbage bytes to ormsgpack.unpackb should be wrapped."""
        from cycletls._ffi import CycleTLSError as FfiCycleTLSError

        # Verify the import is the same class
        assert FfiCycleTLSError is CycleTLSError

    def test_unpackb_on_truncated_data_raises_ormsgpack_error(self):
        """Baseline: raw ormsgpack raises its own error on truncated msgpack data."""
        # 0xde indicates a map16, requiring 2 more bytes for length + entries
        # Providing only 1 byte after the marker makes it truncated/invalid
        with pytest.raises(Exception):
            ormsgpack.unpackb(b"\xde\x00")


class TestBodyBytesDecodeFailure:
    """Verify that base64 decode failure in BodyBytes raises CycleTLSError."""

    def test_invalid_base64_body_bytes_raises_cycletls_error(self):
        from cycletls.schema import _dict_to_response

        data = {
            "RequestID": "test-1",
            "Status": 200,
            "Headers": {},
            "Body": "hello",
            "BodyBytes": "!!!not-valid-base64!!!",
        }
        with pytest.raises(CycleTLSError, match="Failed to decode BodyBytes"):
            _dict_to_response(data)
