"""Tests for API UX improvements: json= alias, auth=, Session base_url, async cookies."""

import base64
from unittest.mock import patch

import pytest

from cycletls.api import CycleTLS
from cycletls.sessions import Session


# ---------------------------------------------------------------------------
# json= alias
# ---------------------------------------------------------------------------

class TestJsonAlias:
    """Test that json= works as an alias for json_data=."""

    @patch("cycletls.api.ffi_send_request")
    def test_json_alias_sends_json_body(self, mock_ffi):
        mock_ffi.return_value = {
            "RequestID": "1",
            "Status": 200,
            "Headers": {"Content-Type": "application/json"},
            "Body": '{"ok":true}',
        }
        client = CycleTLS()
        resp = client.post("https://example.com/api", json={"key": "value"})
        assert resp.status_code == 200

        # Verify the payload sent to FFI has JSON body
        call_args = mock_ffi.call_args[0][0]
        options = call_args["options"]
        assert '"key"' in options["body"]
        assert '"value"' in options["body"]

    @patch("cycletls.api.ffi_send_request")
    def test_json_alias_sets_content_type(self, mock_ffi):
        mock_ffi.return_value = {
            "RequestID": "1",
            "Status": 200,
            "Headers": {},
            "Body": "",
        }
        client = CycleTLS()
        client.post("https://example.com/api", json={"a": 1})

        call_args = mock_ffi.call_args[0][0]
        options = call_args["options"]
        assert options["headers"].get("Content-Type") == "application/json"

    def test_json_and_json_data_conflict_raises(self):
        client = CycleTLS()
        with pytest.raises(ValueError, match="Cannot specify both"):
            client.post("https://example.com", json={"a": 1}, json_data={"b": 2})


# ---------------------------------------------------------------------------
# auth= parameter
# ---------------------------------------------------------------------------

class TestAuthParameter:
    """Test HTTP Basic auth via auth= tuple."""

    @patch("cycletls.api.ffi_send_request")
    def test_auth_adds_basic_header(self, mock_ffi):
        mock_ffi.return_value = {
            "RequestID": "1",
            "Status": 200,
            "Headers": {},
            "Body": "",
        }
        client = CycleTLS()
        client.get("https://example.com/secure", auth=("user", "pass123"))

        call_args = mock_ffi.call_args[0][0]
        options = call_args["options"]
        auth_header = options["headers"]["Authorization"]
        expected = "Basic " + base64.b64encode(b"user:pass123").decode()
        assert auth_header == expected

    @patch("cycletls.api.ffi_send_request")
    def test_auth_works_on_post(self, mock_ffi):
        mock_ffi.return_value = {
            "RequestID": "1",
            "Status": 201,
            "Headers": {},
            "Body": "",
        }
        client = CycleTLS()
        resp = client.post(
            "https://example.com/api",
            json={"data": "test"},
            auth=("admin", "secret"),
        )
        assert resp.status_code == 201

        call_args = mock_ffi.call_args[0][0]
        options = call_args["options"]
        assert "Authorization" in options["headers"]
        assert options["headers"]["Authorization"].startswith("Basic ")


# ---------------------------------------------------------------------------
# Session base_url
# ---------------------------------------------------------------------------

class TestSessionBaseUrl:
    """Test Session with base_url for relative URLs."""

    @patch("cycletls.api.ffi_send_request")
    def test_base_url_prepended_to_relative(self, mock_ffi):
        mock_ffi.return_value = {
            "RequestID": "1",
            "Status": 200,
            "Headers": {},
            "Body": "",
        }
        session = Session(base_url="https://api.example.com")
        session.get("/users")

        call_args = mock_ffi.call_args[0][0]
        options = call_args["options"]
        assert options["url"] == "https://api.example.com/users"

    @patch("cycletls.api.ffi_send_request")
    def test_base_url_not_prepended_to_absolute(self, mock_ffi):
        mock_ffi.return_value = {
            "RequestID": "1",
            "Status": 200,
            "Headers": {},
            "Body": "",
        }
        session = Session(base_url="https://api.example.com")
        session.get("https://other.example.com/data")

        call_args = mock_ffi.call_args[0][0]
        options = call_args["options"]
        assert options["url"] == "https://other.example.com/data"

    @patch("cycletls.api.ffi_send_request")
    def test_base_url_trailing_slash_handled(self, mock_ffi):
        mock_ffi.return_value = {
            "RequestID": "1",
            "Status": 200,
            "Headers": {},
            "Body": "",
        }
        session = Session(base_url="https://api.example.com/")
        session.get("users/1")

        call_args = mock_ffi.call_args[0][0]
        options = call_args["options"]
        assert options["url"] == "https://api.example.com/users/1"


# ---------------------------------------------------------------------------
# Session.auth default
# ---------------------------------------------------------------------------

class TestSessionAuth:
    """Test session-level auth that applies to all requests."""

    @patch("cycletls.api.ffi_send_request")
    def test_session_auth_applied_to_all_requests(self, mock_ffi):
        mock_ffi.return_value = {
            "RequestID": "1",
            "Status": 200,
            "Headers": {},
            "Body": "",
        }
        session = Session(auth=("user", "pass"))
        session.get("https://example.com/a")
        session.get("https://example.com/b")

        # Both calls should have auth header
        for call in mock_ffi.call_args_list:
            options = call[0][0]["options"]
            assert "Authorization" in options["headers"]
            expected = "Basic " + base64.b64encode(b"user:pass").decode()
            assert options["headers"]["Authorization"] == expected

    @patch("cycletls.api.ffi_send_request")
    def test_request_auth_overrides_session_auth(self, mock_ffi):
        mock_ffi.return_value = {
            "RequestID": "1",
            "Status": 200,
            "Headers": {},
            "Body": "",
        }
        session = Session(auth=("default_user", "default_pass"))
        session.get("https://example.com", auth=("override_user", "override_pass"))

        call_args = mock_ffi.call_args[0][0]
        options = call_args["options"]
        expected = "Basic " + base64.b64encode(b"override_user:override_pass").decode()
        assert options["headers"]["Authorization"] == expected


# ---------------------------------------------------------------------------
# Session.arequest() async with cookie persistence
# ---------------------------------------------------------------------------

class TestSessionAsyncCookies:
    """Test that Session.arequest() persists cookies like sync request()."""

    @pytest.mark.asyncio
    @patch("cycletls.api.ffi_send_request_async")
    async def test_arequest_persists_cookies(self, mock_async_ffi):
        mock_async_ffi.return_value = {
            "RequestID": "1",
            "Status": 200,
            "Headers": {},
            "Body": "ok",
            "Cookies": [
                {"name": "session_id", "value": "abc123", "secure": False, "httpOnly": False},
            ],
        }
        session = Session()
        resp = await session.arequest("get", "https://example.com/login")
        assert resp.status_code == 200

        # Session should now have the cookie
        assert "session_id" in session.cookies
        assert session.cookies["session_id"] == "abc123"

    @pytest.mark.asyncio
    @patch("cycletls.api.ffi_send_request_async")
    async def test_arequest_sends_session_cookies(self, mock_async_ffi):
        mock_async_ffi.return_value = {
            "RequestID": "1",
            "Status": 200,
            "Headers": {},
            "Body": "ok",
        }
        session = Session()
        session.cookies.set("token", "xyz")
        await session.arequest("get", "https://example.com/data")

        # Verify cookies were included in the request payload
        call_args = mock_async_ffi.call_args[0][0]
        options = call_args["options"]
        cookies = options.get("cookies", [])
        cookie_names = [c["name"] for c in cookies]
        assert "token" in cookie_names

    @pytest.mark.asyncio
    @patch("cycletls.api.ffi_send_request_async")
    async def test_arequest_uses_base_url(self, mock_async_ffi):
        mock_async_ffi.return_value = {
            "RequestID": "1",
            "Status": 200,
            "Headers": {},
            "Body": "",
        }
        session = Session(base_url="https://api.example.com")
        await session.arequest("get", "/users")

        call_args = mock_async_ffi.call_args[0][0]
        options = call_args["options"]
        assert options["url"] == "https://api.example.com/users"
