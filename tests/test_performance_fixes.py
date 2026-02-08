"""Tests for performance optimizations (hot-path serialization, error checking, imports)."""

from __future__ import annotations

import math

import pytest


class TestRaiseForErrorResponseShortCircuit:
    """Test that _raise_for_error_response short-circuits for successful status codes."""

    def test_200_does_not_raise(self):
        from cycletls.schema import _raise_for_error_response

        # Should return None without raising
        result = _raise_for_error_response({"Status": 200, "Body": ""})
        assert result is None

    def test_201_does_not_raise(self):
        from cycletls.schema import _raise_for_error_response

        result = _raise_for_error_response({"Status": 201, "Body": ""})
        assert result is None

    def test_301_does_not_raise(self):
        from cycletls.schema import _raise_for_error_response

        result = _raise_for_error_response({"Status": 301, "Body": ""})
        assert result is None

    def test_399_does_not_raise(self):
        from cycletls.schema import _raise_for_error_response

        result = _raise_for_error_response({"Status": 399, "Body": ""})
        assert result is None

    def test_4xx_still_raises(self):
        from cycletls.exceptions import CycleTLSError
        from cycletls.schema import _raise_for_error_response

        # status 0 with error body should raise
        with pytest.raises(CycleTLSError):
            _raise_for_error_response({"Status": 0, "Body": "Request failed: something"})

    def test_timeout_still_raises(self):
        from cycletls.exceptions import Timeout
        from cycletls.schema import _raise_for_error_response

        with pytest.raises(Timeout):
            _raise_for_error_response({"Status": 408, "Body": "timeout -> error"})

    def test_dns_error_still_raises(self):
        from cycletls.exceptions import ConnectionError
        from cycletls.schema import _raise_for_error_response

        with pytest.raises(ConnectionError):
            _raise_for_error_response({"Status": 421, "Body": "no such host -> error"})

    def test_500_with_error_body_does_not_raise_without_marker(self):
        """500 without error markers should not raise (it's a valid HTTP 500 response)."""
        from cycletls.schema import _raise_for_error_response

        # A plain 500 without Go error markers should pass through
        result = _raise_for_error_response({"Status": 500, "Body": "Internal Server Error"})
        assert result is None


class TestResponseJson:
    """Test that Response.json() works correctly."""

    def test_json_with_string_body(self):
        from cycletls.schema import Response

        resp = Response(
            request_id="test",
            status_code=200,
            body='{"key": "value", "num": 42}',
        )
        data = resp.json()
        assert data == {"key": "value", "num": 42}

    def test_json_with_unicode_body(self):
        from cycletls.schema import Response

        resp = Response(
            request_id="test",
            status_code=200,
            body='{"emoji": "\\u2764"}',
        )
        data = resp.json()
        assert data == {"emoji": "\u2764"}

    def test_json_with_empty_object(self):
        from cycletls.schema import Response

        resp = Response(
            request_id="test",
            status_code=200,
            body="{}",
        )
        assert resp.json() == {}

    def test_json_with_array(self):
        from cycletls.schema import Response

        resp = Response(
            request_id="test",
            status_code=200,
            body="[1, 2, 3]",
        )
        assert resp.json() == [1, 2, 3]


class TestRequestToDict:
    """Test that Request.to_dict() correctly rounds up timeout (math.ceil behavior)."""

    def test_float_timeout_rounds_up(self):
        from cycletls.schema import Request

        req = Request(url="https://example.com", method="GET", timeout=2.1)
        d = req.to_dict()
        assert d["timeout"] == 3  # math.ceil(2.1) == 3

    def test_integer_timeout_stays_same(self):
        from cycletls.schema import Request

        req = Request(url="https://example.com", method="GET", timeout=5)
        d = req.to_dict()
        assert d["timeout"] == 5

    def test_zero_timeout(self):
        from cycletls.schema import Request

        req = Request(url="https://example.com", method="GET", timeout=0)
        d = req.to_dict()
        assert d["timeout"] == 0

    def test_fractional_timeout_rounds_up(self):
        from cycletls.schema import Request

        req = Request(url="https://example.com", method="GET", timeout=0.5)
        d = req.to_dict()
        assert d["timeout"] == 1  # max(1, math.ceil(0.5))

    def test_minimum_timeout_is_1(self):
        from cycletls.schema import Request

        req = Request(url="https://example.com", method="GET", timeout=0.01)
        d = req.to_dict()
        assert d["timeout"] == 1


class TestJsonBodySerialization:
    """Test that JSON body serialization produces correct output via _json_dumps."""

    def test_orjson_dumps_available(self):
        from cycletls.api import _json_dumps

        # orjson should be available (it's a dependency)
        assert _json_dumps is not None

    def test_json_data_serialization(self):
        from cycletls.api import _json_dumps

        import json

        data = {"key": "value", "number": 42}
        result = _json_dumps(data).decode("utf-8")
        parsed = json.loads(result)
        assert parsed == data

    def test_json_data_with_nested_objects(self):
        from cycletls.api import _json_dumps

        import json

        data = {"nested": {"a": 1}, "list": [1, 2, 3]}
        result = _json_dumps(data).decode("utf-8")
        parsed = json.loads(result)
        assert parsed == data

    def test_json_data_with_special_characters(self):
        from cycletls.api import _json_dumps

        import json

        data = {"text": 'hello "world"', "unicode": "\u00e9"}
        result = _json_dumps(data).decode("utf-8")
        parsed = json.loads(result)
        assert parsed == data

    def test_batch_payload_json_serialization(self):
        """Test that _build_batch_payload uses orjson for json_data."""
        from cycletls.api import CycleTLS as _CycleTLS

        import json

        client = _CycleTLS()
        payload = client._build_batch_payload(
            {"url": "https://example.com", "method": "POST", "json_data": {"key": "value"}},
            request_id="test_1",
        )
        parsed = json.loads(payload["options"]["body"])
        assert parsed == {"key": "value"}
        assert payload["options"]["headers"]["Content-Type"] == "application/json"


class TestStatusPhrasesCache:
    """Test that _STATUS_PHRASES is a module-level constant."""

    def test_status_phrases_is_module_level(self):
        from cycletls import schema

        assert hasattr(schema, "_STATUS_PHRASES")
        assert isinstance(schema._STATUS_PHRASES, dict)
        assert schema._STATUS_PHRASES[200] == "OK"
        assert schema._STATUS_PHRASES[404] == "Not Found"

    def test_reason_property_uses_cached_phrases(self):
        from cycletls.schema import Response

        resp = Response(request_id="test", status_code=200)
        assert resp.reason == "OK"

        resp2 = Response(request_id="test", status_code=404)
        assert resp2.reason == "Not Found"

        resp3 = Response(request_id="test", status_code=999)
        assert resp3.reason == "Unknown"


class TestMathImportModuleLevel:
    """Test that math is imported at module level (not per-call)."""

    def test_math_in_schema_module(self):
        from cycletls import schema

        # math should be available at module level
        assert hasattr(schema, "math")
        assert schema.math is math
