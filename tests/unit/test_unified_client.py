"""
Unit tests for CycleTLS unified client refactoring (Phases 1-2).

Tests cover:
- Phase 1: _prepare_request() and _parse_response() extraction
- Phase 2: Async context manager and async methods on CycleTLS

These tests mock the FFI layer so they run without the Go shared library.
"""

from __future__ import annotations

import asyncio
import json
import warnings
from unittest.mock import AsyncMock, patch

import pytest

from cycletls.api import CycleTLS
from cycletls.exceptions import CycleTLSError
from cycletls.schema import Response

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_response_data(status: int = 200, body: str = "ok", url: str = "https://example.com") -> dict:
    """Build a minimal response dict matching Go backend format."""
    return {
        "RequestID": "req_1",
        "Status": status,
        "Body": body,
        "Headers": {"Content-Type": "text/plain"},
        "FinalUrl": url,
        "Cookies": [],
    }


# ===========================================================================
# Phase 1: _prepare_request / _parse_response
# ===========================================================================


class TestPrepareRequest:
    """Tests for CycleTLS._prepare_request()."""

    def test_method_exists(self):
        """_prepare_request should be a method on CycleTLS."""
        client = CycleTLS()
        assert hasattr(client, "_prepare_request")
        assert callable(client._prepare_request)

    def test_returns_dict(self):
        """_prepare_request should return a dict payload."""
        client = CycleTLS()
        result = client._prepare_request("GET", "https://example.com")
        assert isinstance(result, dict)

    def test_payload_has_request_id_and_options(self):
        """Returned dict must have requestId and options keys."""
        client = CycleTLS()
        payload = client._prepare_request("GET", "https://example.com")
        assert "requestId" in payload
        assert "options" in payload
        assert isinstance(payload["options"], dict)

    def test_payload_options_has_url_and_method(self):
        """Options dict should contain url and method."""
        client = CycleTLS()
        payload = client._prepare_request("POST", "https://example.com/api")
        options = payload["options"]
        assert options["url"] == "https://example.com/api"
        assert options["method"] == "POST"

    def test_params_merged_into_url(self):
        """Query params should be merged into the URL."""
        client = CycleTLS()
        payload = client._prepare_request(
            "GET", "https://example.com", params={"q": "hello"}
        )
        assert "q=hello" in payload["options"]["url"]

    def test_json_data_sets_body_and_content_type(self):
        """json_data should serialize to body and set Content-Type."""
        client = CycleTLS()
        payload = client._prepare_request(
            "POST", "https://example.com", json_data={"key": "value"}
        )
        options = payload["options"]
        # orjson produces compact JSON (no spaces), stdlib json adds spaces
        assert options["body"] == json.dumps({"key": "value"}, separators=(",", ":"))
        assert options["headers"]["Content-Type"] == "application/json"

    def test_form_data_urlencoded(self):
        """Dict data should be URL-encoded with proper Content-Type."""
        client = CycleTLS()
        payload = client._prepare_request(
            "POST", "https://example.com", data={"field": "val"}
        )
        options = payload["options"]
        assert "field=val" in options["body"]
        assert options["headers"]["Content-Type"] == "application/x-www-form-urlencoded"

    def test_bytes_data_sets_body_bytes(self):
        """bytes data should be set in bodyBytes."""
        client = CycleTLS()
        payload = client._prepare_request(
            "POST", "https://example.com", data=b"raw bytes"
        )
        options = payload["options"]
        assert options.get("bodyBytes") == b"raw bytes"

    def test_data_and_json_raises(self):
        """Passing both data and json_data should raise ValueError."""
        client = CycleTLS()
        with pytest.raises(ValueError, match="Cannot specify both"):
            client._prepare_request(
                "POST", "https://example.com",
                data={"a": "1"}, json_data={"b": "2"}
            )

    def test_fingerprint_string_applied(self):
        """String fingerprint should be resolved and applied to kwargs."""
        client = CycleTLS()
        # chrome_120 is a built-in fingerprint
        payload = client._prepare_request(
            "GET", "https://example.com", fingerprint="chrome_120"
        )
        options = payload["options"]
        # chrome_120 sets a specific ja3 and user_agent
        assert "Chrome" in options.get("userAgent", "")

    def test_user_agent_header_extraction(self):
        """User-Agent in headers dict should be moved to userAgent field."""
        client = CycleTLS()
        payload = client._prepare_request(
            "GET", "https://example.com",
            headers={"User-Agent": "CustomBot/1.0"}
        )
        options = payload["options"]
        assert options["userAgent"] == "CustomBot/1.0"

    def test_cookies_dict_converted(self):
        """Dict cookies should be converted to list of Cookie dicts."""
        client = CycleTLS()
        payload = client._prepare_request(
            "GET", "https://example.com",
            cookies={"session": "abc123"}
        )
        options = payload["options"]
        assert "cookies" in options
        cookie_list = options["cookies"]
        assert isinstance(cookie_list, list)
        assert any(c["name"] == "session" for c in cookie_list)

    def test_deprecated_body_param_warning(self):
        """Using 'body' kwarg should emit DeprecationWarning."""
        client = CycleTLS()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            client._prepare_request(
                "POST", "https://example.com", body="old style"
            )
            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)

    def test_does_not_call_ffi(self):
        """_prepare_request must NOT call any FFI function."""
        client = CycleTLS()
        with patch("cycletls.api.ffi_send_request") as mock_ffi:
            client._prepare_request("GET", "https://example.com")
            mock_ffi.assert_not_called()


class TestParseResponse:
    """Tests for CycleTLS._parse_response()."""

    def test_method_exists(self):
        """_parse_response should be a method on CycleTLS."""
        client = CycleTLS()
        assert hasattr(client, "_parse_response")
        assert callable(client._parse_response)

    def test_returns_response_object(self):
        """_parse_response should return a Response instance."""
        client = CycleTLS()
        data = _fake_response_data()
        result = client._parse_response(data, "https://example.com")
        assert isinstance(result, Response)

    def test_response_status_code(self):
        """Status code should be extracted correctly."""
        client = CycleTLS()
        data = _fake_response_data(status=404)
        result = client._parse_response(data, "https://example.com")
        assert result.status_code == 404

    def test_response_body(self):
        """Body should be extracted correctly."""
        client = CycleTLS()
        data = _fake_response_data(body="hello world")
        result = client._parse_response(data, "https://example.com")
        assert result.body == "hello world"

    def test_invalid_response_raises(self):
        """Non-dict response_data should raise CycleTLSError."""
        client = CycleTLS()
        with pytest.raises(CycleTLSError, match="Invalid response payload"):
            client._parse_response("not a dict", "https://example.com")

    def test_error_response_raises(self):
        """Error response (status 0) should raise appropriate exception."""
        client = CycleTLS()
        data = {"Status": 0, "Body": "Request failed: connection refused", "Headers": {}}
        with pytest.raises(CycleTLSError):
            client._parse_response(data, "https://example.com")


class TestRequestUsesHelpers:
    """Tests that request() delegates to _prepare_request and _parse_response."""

    @patch("cycletls.api.ffi_send_request")
    def test_request_uses_prepare_and_parse(self, mock_ffi):
        """request() should call _prepare_request then ffi then _parse_response."""
        mock_ffi.return_value = _fake_response_data()
        client = CycleTLS()

        with patch.object(client, "_prepare_request", wraps=client._prepare_request) as mock_prep, \
             patch.object(client, "_parse_response", wraps=client._parse_response) as mock_parse:
            response = client.request("GET", "https://example.com")

            mock_prep.assert_called_once()
            mock_parse.assert_called_once()
            assert isinstance(response, Response)

    @patch("cycletls.api.ffi_send_request")
    def test_request_closed_raises(self, mock_ffi):
        """request() on closed client should raise CycleTLSError."""
        client = CycleTLS()
        client.close()
        with pytest.raises(CycleTLSError, match="closed"):
            client.request("GET", "https://example.com")
        mock_ffi.assert_not_called()


class TestBatchUsesParseResponse:
    """Tests that batch() uses _parse_response for consistency."""

    @patch("cycletls.api.ffi_send_batch_request")
    def test_batch_uses_parse_response(self, mock_ffi):
        """batch() should call _parse_response for each result."""
        mock_ffi.return_value = [
            _fake_response_data(status=200, body="first"),
            _fake_response_data(status=201, body="second"),
        ]
        client = CycleTLS()

        with patch.object(client, "_parse_response", wraps=client._parse_response) as mock_parse:
            responses = client.batch([
                {"url": "https://example.com/1", "method": "GET"},
                {"url": "https://example.com/2", "method": "POST"},
            ])

            assert mock_parse.call_count == 2
            assert len(responses) == 2
            assert responses[0].body == "first"
            assert responses[1].body == "second"


# ===========================================================================
# Phase 2: Async context manager and async methods
# ===========================================================================


class TestAsyncContextManager:
    """Tests for CycleTLS async context manager (__aenter__/__aexit__)."""

    @pytest.mark.asyncio
    async def test_aenter_returns_self(self):
        """__aenter__ should return the CycleTLS instance."""
        client = CycleTLS()
        result = await client.__aenter__()
        assert result is client

    @pytest.mark.asyncio
    async def test_aexit_closes_client(self):
        """__aexit__ should close the client."""
        client = CycleTLS()
        await client.__aenter__()
        await client.__aexit__(None, None, None)
        assert client._closed is True

    @pytest.mark.asyncio
    async def test_async_with_statement(self):
        """CycleTLS should work with 'async with' statement."""
        async with CycleTLS() as client:
            assert isinstance(client, CycleTLS)
            assert client._closed is False
        assert client._closed is True


class TestARequest:
    """Tests for CycleTLS.arequest() async method."""

    def test_arequest_method_exists(self):
        """arequest should be a coroutine method on CycleTLS."""
        client = CycleTLS()
        assert hasattr(client, "arequest")
        assert asyncio.iscoroutinefunction(client.arequest)

    @pytest.mark.asyncio
    async def test_arequest_basic(self):
        """arequest should return a Response via async FFI."""
        client = CycleTLS()
        fake_data = _fake_response_data()

        with patch("cycletls.api.ffi_send_request_async", new_callable=AsyncMock) as mock_ffi:
            mock_ffi.return_value = fake_data
            response = await client.arequest("GET", "https://example.com")

            assert isinstance(response, Response)
            assert response.status_code == 200
            mock_ffi.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_arequest_passes_poll_interval_and_timeout(self):
        """arequest should pass poll_interval and timeout to FFI."""
        client = CycleTLS()
        fake_data = _fake_response_data()

        with patch("cycletls.api.ffi_send_request_async", new_callable=AsyncMock) as mock_ffi:
            mock_ffi.return_value = fake_data
            await client.arequest(
                "GET", "https://example.com",
                poll_interval=0.01, timeout=5.0
            )

            args, kwargs = mock_ffi.call_args
            # poll_interval and timeout should be passed to the FFI function
            assert 0.01 in args or kwargs.get("poll_interval") == 0.01 or args[1] == 0.01
            assert 5.0 in args or kwargs.get("timeout") == 5.0 or args[2] == 5.0

    @pytest.mark.asyncio
    async def test_arequest_uses_prepare_request(self):
        """arequest should use _prepare_request for payload construction."""
        client = CycleTLS()
        fake_data = _fake_response_data()

        with patch("cycletls.api.ffi_send_request_async", new_callable=AsyncMock) as mock_ffi, \
             patch.object(client, "_prepare_request", wraps=client._prepare_request) as mock_prep:
            mock_ffi.return_value = fake_data
            await client.arequest("POST", "https://example.com", json_data={"x": 1})

            mock_prep.assert_called_once()

    @pytest.mark.asyncio
    async def test_arequest_uses_parse_response(self):
        """arequest should use _parse_response for response construction."""
        client = CycleTLS()
        fake_data = _fake_response_data()

        with patch("cycletls.api.ffi_send_request_async", new_callable=AsyncMock) as mock_ffi, \
             patch.object(client, "_parse_response", wraps=client._parse_response) as mock_parse:
            mock_ffi.return_value = fake_data
            await client.arequest("GET", "https://example.com")

            mock_parse.assert_called_once()

    @pytest.mark.asyncio
    async def test_arequest_closed_raises(self):
        """arequest on closed client should raise CycleTLSError."""
        client = CycleTLS()
        client.close()
        with pytest.raises(CycleTLSError, match="closed"):
            await client.arequest("GET", "https://example.com")

    @pytest.mark.asyncio
    async def test_arequest_with_fingerprint(self):
        """arequest should accept and apply fingerprint parameter."""
        client = CycleTLS()
        fake_data = _fake_response_data()

        with patch("cycletls.api.ffi_send_request_async", new_callable=AsyncMock) as mock_ffi:
            mock_ffi.return_value = fake_data
            response = await client.arequest(
                "GET", "https://example.com", fingerprint="chrome_120"
            )
            assert isinstance(response, Response)


class TestAsyncConvenienceMethods:
    """Tests for async convenience methods (aget, apost, etc.)."""

    @pytest.mark.asyncio
    async def test_aget_exists_and_calls_arequest(self):
        """aget should exist and delegate to arequest."""
        client = CycleTLS()

        with patch.object(client, "arequest", new_callable=AsyncMock) as mock_areq:
            mock_areq.return_value = Response(
                request_id="1", status_code=200, body="ok"
            )
            await client.aget("https://example.com", params={"q": "test"})
            mock_areq.assert_awaited_once()
            call_args = mock_areq.call_args
            assert call_args[0][0] == "get"
            assert call_args[0][1] == "https://example.com"

    @pytest.mark.asyncio
    async def test_apost_exists_and_calls_arequest(self):
        """apost should exist and delegate to arequest."""
        client = CycleTLS()
        with patch.object(client, "arequest", new_callable=AsyncMock) as mock_areq:
            mock_areq.return_value = Response(
                request_id="1", status_code=200, body="ok"
            )
            await client.apost("https://example.com", data={"k": "v"})
            mock_areq.assert_awaited_once()
            assert mock_areq.call_args[0][0] == "post"

    @pytest.mark.asyncio
    async def test_aput_exists_and_calls_arequest(self):
        """aput should exist and delegate to arequest."""
        client = CycleTLS()
        with patch.object(client, "arequest", new_callable=AsyncMock) as mock_areq:
            mock_areq.return_value = Response(
                request_id="1", status_code=200, body="ok"
            )
            await client.aput("https://example.com", json_data={"x": 1})
            mock_areq.assert_awaited_once()
            assert mock_areq.call_args[0][0] == "put"

    @pytest.mark.asyncio
    async def test_apatch_exists_and_calls_arequest(self):
        """apatch should exist and delegate to arequest."""
        client = CycleTLS()
        with patch.object(client, "arequest", new_callable=AsyncMock) as mock_areq:
            mock_areq.return_value = Response(
                request_id="1", status_code=200, body="ok"
            )
            await client.apatch("https://example.com")
            mock_areq.assert_awaited_once()
            assert mock_areq.call_args[0][0] == "patch"

    @pytest.mark.asyncio
    async def test_adelete_exists_and_calls_arequest(self):
        """adelete should exist and delegate to arequest."""
        client = CycleTLS()
        with patch.object(client, "arequest", new_callable=AsyncMock) as mock_areq:
            mock_areq.return_value = Response(
                request_id="1", status_code=200, body="ok"
            )
            await client.adelete("https://example.com")
            mock_areq.assert_awaited_once()
            assert mock_areq.call_args[0][0] == "delete"

    @pytest.mark.asyncio
    async def test_ahead_exists_and_calls_arequest(self):
        """ahead should exist and delegate to arequest."""
        client = CycleTLS()
        with patch.object(client, "arequest", new_callable=AsyncMock) as mock_areq:
            mock_areq.return_value = Response(
                request_id="1", status_code=200, body="ok"
            )
            await client.ahead("https://example.com")
            mock_areq.assert_awaited_once()
            assert mock_areq.call_args[0][0] == "head"

    @pytest.mark.asyncio
    async def test_aoptions_exists_and_calls_arequest(self):
        """aoptions should exist and delegate to arequest."""
        client = CycleTLS()
        with patch.object(client, "arequest", new_callable=AsyncMock) as mock_areq:
            mock_areq.return_value = Response(
                request_id="1", status_code=200, body="ok"
            )
            await client.aoptions("https://example.com")
            mock_areq.assert_awaited_once()
            assert mock_areq.call_args[0][0] == "options"


class TestAsyncConvenienceMethodsHaveFingerprint:
    """All async convenience methods should include fingerprint parameter."""

    @pytest.mark.asyncio
    async def test_aget_has_fingerprint(self):
        """aget should accept fingerprint parameter."""
        client = CycleTLS()
        with patch.object(client, "arequest", new_callable=AsyncMock) as mock_areq:
            mock_areq.return_value = Response(
                request_id="1", status_code=200, body="ok"
            )
            await client.aget("https://example.com", fingerprint="chrome_120")
            call_kwargs = mock_areq.call_args[1]
            assert call_kwargs.get("fingerprint") == "chrome_120"

    @pytest.mark.asyncio
    async def test_apost_has_fingerprint(self):
        """apost should accept fingerprint parameter."""
        client = CycleTLS()
        with patch.object(client, "arequest", new_callable=AsyncMock) as mock_areq:
            mock_areq.return_value = Response(
                request_id="1", status_code=200, body="ok"
            )
            await client.apost("https://example.com", fingerprint="firefox_121")
            call_kwargs = mock_areq.call_args[1]
            assert call_kwargs.get("fingerprint") == "firefox_121"

    @pytest.mark.asyncio
    async def test_aput_has_fingerprint(self):
        """aput should accept fingerprint parameter."""
        client = CycleTLS()
        with patch.object(client, "arequest", new_callable=AsyncMock) as mock_areq:
            mock_areq.return_value = Response(
                request_id="1", status_code=200, body="ok"
            )
            await client.aput("https://example.com", fingerprint="chrome_120")
            call_kwargs = mock_areq.call_args[1]
            assert call_kwargs.get("fingerprint") == "chrome_120"

    @pytest.mark.asyncio
    async def test_apatch_has_fingerprint(self):
        """apatch should accept fingerprint parameter."""
        client = CycleTLS()
        with patch.object(client, "arequest", new_callable=AsyncMock) as mock_areq:
            mock_areq.return_value = Response(
                request_id="1", status_code=200, body="ok"
            )
            await client.apatch("https://example.com", fingerprint="chrome_120")
            call_kwargs = mock_areq.call_args[1]
            assert call_kwargs.get("fingerprint") == "chrome_120"

    @pytest.mark.asyncio
    async def test_adelete_has_fingerprint(self):
        """adelete should accept fingerprint parameter."""
        client = CycleTLS()
        with patch.object(client, "arequest", new_callable=AsyncMock) as mock_areq:
            mock_areq.return_value = Response(
                request_id="1", status_code=200, body="ok"
            )
            await client.adelete("https://example.com", fingerprint="chrome_120")
            call_kwargs = mock_areq.call_args[1]
            assert call_kwargs.get("fingerprint") == "chrome_120"

    @pytest.mark.asyncio
    async def test_ahead_has_fingerprint(self):
        """ahead should accept fingerprint parameter."""
        client = CycleTLS()
        with patch.object(client, "arequest", new_callable=AsyncMock) as mock_areq:
            mock_areq.return_value = Response(
                request_id="1", status_code=200, body="ok"
            )
            await client.ahead("https://example.com", fingerprint="chrome_120")
            call_kwargs = mock_areq.call_args[1]
            assert call_kwargs.get("fingerprint") == "chrome_120"

    @pytest.mark.asyncio
    async def test_aoptions_has_fingerprint(self):
        """aoptions should accept fingerprint parameter."""
        client = CycleTLS()
        with patch.object(client, "arequest", new_callable=AsyncMock) as mock_areq:
            mock_areq.return_value = Response(
                request_id="1", status_code=200, body="ok"
            )
            await client.aoptions("https://example.com", fingerprint="chrome_120")
            call_kwargs = mock_areq.call_args[1]
            assert call_kwargs.get("fingerprint") == "chrome_120"


class TestABatch:
    """Tests for CycleTLS.abatch() async batch method."""

    def test_abatch_method_exists(self):
        """abatch should be a coroutine method on CycleTLS."""
        client = CycleTLS()
        assert hasattr(client, "abatch")
        assert asyncio.iscoroutinefunction(client.abatch)

    @pytest.mark.asyncio
    async def test_abatch_returns_list_of_responses(self):
        """abatch should return a list of Response objects."""
        client = CycleTLS()
        fake_responses = [
            _fake_response_data(status=200, body="first"),
            _fake_response_data(status=201, body="second"),
        ]

        with patch("cycletls.api.ffi_send_requests_batch", new_callable=AsyncMock) as mock_ffi:
            mock_ffi.return_value = fake_responses
            responses = await client.abatch([
                {"url": "https://example.com/1", "method": "GET"},
                {"url": "https://example.com/2", "method": "POST"},
            ])

            assert len(responses) == 2
            assert all(isinstance(r, Response) for r in responses)
            assert responses[0].status_code == 200
            assert responses[1].status_code == 201

    @pytest.mark.asyncio
    async def test_abatch_empty_list(self):
        """abatch with empty list should return empty list."""
        client = CycleTLS()
        responses = await client.abatch([])
        assert responses == []

    @pytest.mark.asyncio
    async def test_abatch_closed_raises(self):
        """abatch on closed client should raise CycleTLSError."""
        client = CycleTLS()
        client.close()
        with pytest.raises(CycleTLSError, match="closed"):
            await client.abatch([{"url": "https://example.com", "method": "GET"}])


class TestSyncMethodsUnchanged:
    """Verify that existing sync methods still work identically."""

    @patch("cycletls.api.ffi_send_request")
    def test_get_still_works(self, mock_ffi):
        """Sync get() should still work after refactoring."""
        mock_ffi.return_value = _fake_response_data()
        client = CycleTLS()
        response = client.get("https://example.com")
        assert isinstance(response, Response)
        assert response.status_code == 200

    @patch("cycletls.api.ffi_send_request")
    def test_post_still_works(self, mock_ffi):
        """Sync post() should still work after refactoring."""
        mock_ffi.return_value = _fake_response_data()
        client = CycleTLS()
        response = client.post("https://example.com", json_data={"k": "v"})
        assert isinstance(response, Response)

    @patch("cycletls.api.ffi_send_request")
    def test_put_still_works(self, mock_ffi):
        """Sync put() should still work after refactoring."""
        mock_ffi.return_value = _fake_response_data()
        client = CycleTLS()
        response = client.put("https://example.com", data={"k": "v"})
        assert isinstance(response, Response)

    @patch("cycletls.api.ffi_send_request")
    def test_patch_still_works(self, mock_ffi):
        """Sync patch() should still work after refactoring."""
        mock_ffi.return_value = _fake_response_data()
        client = CycleTLS()
        response = client.patch("https://example.com")
        assert isinstance(response, Response)

    @patch("cycletls.api.ffi_send_request")
    def test_delete_still_works(self, mock_ffi):
        """Sync delete() should still work after refactoring."""
        mock_ffi.return_value = _fake_response_data()
        client = CycleTLS()
        response = client.delete("https://example.com")
        assert isinstance(response, Response)

    @patch("cycletls.api.ffi_send_request")
    def test_head_still_works(self, mock_ffi):
        """Sync head() should still work after refactoring."""
        mock_ffi.return_value = _fake_response_data()
        client = CycleTLS()
        response = client.head("https://example.com")
        assert isinstance(response, Response)

    @patch("cycletls.api.ffi_send_request")
    def test_options_still_works(self, mock_ffi):
        """Sync options() should still work after refactoring."""
        mock_ffi.return_value = _fake_response_data()
        client = CycleTLS()
        response = client.options("https://example.com")
        assert isinstance(response, Response)

    def test_sync_context_manager_still_works(self):
        """Sync context manager should still work."""
        with CycleTLS() as client:
            assert isinstance(client, CycleTLS)
            assert client._closed is False
        assert client._closed is True

    @patch("cycletls.api.ffi_send_request")
    def test_request_signature_unchanged(self, mock_ffi):
        """request() signature should be identical - Session subclass depends on it."""
        mock_ffi.return_value = _fake_response_data()
        client = CycleTLS()
        # Call with all positional args that Session.request uses
        response = client.request(
            "GET",  # method
            "https://example.com",  # url
            None,  # params
            None,  # data
            None,  # json_data
            None,  # files
            None,  # fingerprint
        )
        assert isinstance(response, Response)
