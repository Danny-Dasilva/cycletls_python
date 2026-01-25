"""
Cookie tests against tlsfingerprint.com.

Tests sending and receiving cookies.

Mirrors TypeScript tests in tests/tlsfingerprint/cookies.test.ts
"""

import re
import pytest
from .conftest import (
    TEST_SERVER_URL,
    get_default_options,
    assert_tls_fields_present,
    is_service_available,
)


# Check service availability at module level
pytestmark = pytest.mark.skipif(
    not is_service_available(),
    reason="tlsfingerprint.com is unavailable (received 521 or timeout)"
)


class TestTLSFingerprintCookiesReading:
    """Cookie Reading tests."""

    def test_should_send_cookies_and_have_them_echoed_back(self, cycle_client):
        """Should send cookies and have them echoed back."""
        options = get_default_options()
        response = cycle_client.get(
            f"{TEST_SERVER_URL}/cookies",
            headers={"Cookie": "test=value1; session=abc123"},
            **options,
        )

        assert response.status_code == 200

        body = response.json()

        assert_tls_fields_present(body)

        # Verify cookies are echoed back
        assert "cookies" in body
        assert body["cookies"] is not None

        cookies = body["cookies"]
        assert cookies.get("test") == "value1"
        assert cookies.get("session") == "abc123"

    def test_should_send_single_cookie(self, cycle_client):
        """Should send single cookie."""
        options = get_default_options()
        response = cycle_client.get(
            f"{TEST_SERVER_URL}/cookies",
            headers={"Cookie": "single_cookie=single_value"},
            **options,
        )

        assert response.status_code == 200

        body = response.json()

        assert_tls_fields_present(body)

        assert "cookies" in body
        cookies = body["cookies"]
        assert cookies.get("single_cookie") == "single_value"

    def test_should_handle_cookies_with_special_characters(self, cycle_client):
        """Should handle cookies with special characters."""
        options = get_default_options()
        response = cycle_client.get(
            f"{TEST_SERVER_URL}/cookies",
            headers={"Cookie": "encoded=hello%20world"},
            **options,
        )

        assert response.status_code == 200

        body = response.json()

        assert_tls_fields_present(body)
        assert "cookies" in body

    def test_should_handle_multiple_cookies(self, cycle_client):
        """Should handle multiple cookies."""
        options = get_default_options()
        response = cycle_client.get(
            f"{TEST_SERVER_URL}/cookies",
            headers={"Cookie": "cookie1=value1; cookie2=value2; cookie3=value3"},
            **options,
        )

        assert response.status_code == 200

        body = response.json()

        assert_tls_fields_present(body)

        assert "cookies" in body
        cookies = body["cookies"]
        assert cookies.get("cookie1") == "value1"
        assert cookies.get("cookie2") == "value2"
        assert cookies.get("cookie3") == "value3"


class TestTLSFingerprintCookiesSetting:
    """Cookie Setting tests."""

    def test_should_receive_cookies_set_via_cookies_set(self, cycle_client):
        """Should receive cookies set via /cookies/set."""
        options = get_default_options()
        response = cycle_client.get(
            f"{TEST_SERVER_URL}/cookies/set?name=value&foo=bar",
            **options,
        )

        assert response.status_code == 200

        body = response.json()

        assert_tls_fields_present(body)

        # Verify the cookies were set and echoed back
        assert "cookies" in body
        cookies = body["cookies"]
        assert cookies.get("name") == "value"
        assert cookies.get("foo") == "bar"

    def test_should_receive_single_cookie_set_via_query_param(self, cycle_client):
        """Should receive single cookie set via query param."""
        options = get_default_options()
        response = cycle_client.get(
            f"{TEST_SERVER_URL}/cookies/set?session_id=xyz789",
            **options,
        )

        assert response.status_code == 200

        body = response.json()

        assert_tls_fields_present(body)

        assert "cookies" in body
        cookies = body["cookies"]
        assert cookies.get("session_id") == "xyz789"


class TestTLSFingerprintCookiesDelete:
    """Cookie Delete tests."""

    def test_should_handle_cookie_deletion_endpoint(self, cycle_client):
        """Should handle cookie deletion endpoint."""
        options = get_default_options()

        # First set a cookie
        cycle_client.get(
            f"{TEST_SERVER_URL}/cookies/set?deleteme=value",
            **options,
        )

        # Then request deletion (this endpoint may redirect to /cookies)
        delete_response = cycle_client.get(
            f"{TEST_SERVER_URL}/cookies/delete?deleteme",
            **options,
        )

        assert delete_response.status_code == 200

        body = delete_response.json()

        assert_tls_fields_present(body)


class TestTLSFingerprintCookiesWithTLSFingerprint:
    """Cookies with TLS Fingerprint tests."""

    def test_should_have_valid_tls_fingerprint_when_sending_cookies(self, cycle_client):
        """Should have valid TLS fingerprint when sending cookies."""
        options = get_default_options()
        response = cycle_client.get(
            f"{TEST_SERVER_URL}/cookies",
            headers={"Cookie": "auth=token123"},
            **options,
        )

        assert response.status_code == 200

        body = response.json()

        # Verify all required TLS fields
        assert_tls_fields_present(body)

        # JA3 should be present and valid
        assert "ja3" in body
        assert len(body["ja3"]) > 50

        # JA3 hash should be MD5 format
        assert re.match(r"^[a-f0-9]{32}$", body["ja3_hash"])

        # JA4 should be present
        assert "ja4" in body
        assert len(body["ja4"]) > 0

        # Peetprint should be present
        assert "peetprint" in body
        assert "peetprint_hash" in body


class TestTLSFingerprintNoCookies:
    """No Cookies tests."""

    def test_should_return_empty_cookies_when_none_sent(self, cycle_client):
        """Should return empty cookies when none sent."""
        options = get_default_options()
        response = cycle_client.get(f"{TEST_SERVER_URL}/cookies", **options)

        assert response.status_code == 200

        body = response.json()

        assert_tls_fields_present(body)

        # Cookies object should exist but be empty
        assert "cookies" in body
        assert len(body.get("cookies", {})) == 0
