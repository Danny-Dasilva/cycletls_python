"""
Cookie handling tests for CycleTLS Python client.
Tests cookie sending, receiving, attributes, and expiration.
"""

import pytest
from datetime import datetime, timedelta
from cycletls import Cookie


class TestCookies:
    """Test suite for cookie handling in CycleTLS"""

    def test_send_cookies_with_request(self, cycletls_client, httpbin_url):
        """Test sending cookies with a request"""
        cookies = [
            Cookie(name="session_id", value="abc123"),
            Cookie(name="user_token", value="xyz789"),
        ]

        response = cycletls_client.get(
            f"{httpbin_url}/cookies",
            cookies=cookies
        )

        assert response.status_code == 200
        data = response.json()
        assert "cookies" in data
        assert data["cookies"]["session_id"] == "abc123"
        assert data["cookies"]["user_token"] == "xyz789"

    def test_send_single_cookie(self, cycletls_client, httpbin_url):
        """Test sending a single cookie"""
        cookies = [Cookie(name="test_cookie", value="test_value")]

        response = cycletls_client.get(
            f"{httpbin_url}/cookies",
            cookies=cookies
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cookies"]["test_cookie"] == "test_value"

    def test_receive_cookies_from_response(self, cycletls_client, httpbin_url):
        """Test receiving cookies set by the server"""
        response = cycletls_client.get(
            f"{httpbin_url}/cookies/set?test_cookie=test_value&another=value2"
        )

        assert response.status_code == 200
        assert response.cookies is not None

        # Check that cookies were set
        cookie_names = [cookie.name for cookie in response.cookies]
        assert "test_cookie" in cookie_names or "another" in cookie_names

    def test_cookie_with_domain_attribute(self, cycletls_client, httpbin_url):
        """Test sending cookie with domain attribute"""
        cookies = [
            Cookie(
                name="domain_cookie",
                value="domain_value",
                domain=".httpbin.org"
            )
        ]

        response = cycletls_client.get(
            f"{httpbin_url}/cookies",
            cookies=cookies
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cookies"]["domain_cookie"] == "domain_value"

    def test_cookie_with_path_attribute(self, cycletls_client, httpbin_url):
        """Test sending cookie with path attribute"""
        cookies = [
            Cookie(
                name="path_cookie",
                value="path_value",
                path="/cookies"
            )
        ]

        response = cycletls_client.get(
            f"{httpbin_url}/cookies",
            cookies=cookies
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cookies"]["path_cookie"] == "path_value"

    def test_cookie_with_secure_flag(self, cycletls_client, httpbin_url):
        """Test sending cookie with secure flag"""
        cookies = [
            Cookie(
                name="secure_cookie",
                value="secure_value",
                secure=True
            )
        ]

        response = cycletls_client.get(
            f"{httpbin_url}/cookies",
            cookies=cookies
        )

        assert response.status_code == 200
        data = response.json()
        # Secure cookies should still be sent over HTTPS
        assert data["cookies"]["secure_cookie"] == "secure_value"

    def test_cookie_with_httponly_flag(self, cycletls_client, httpbin_url):
        """Test sending cookie with httpOnly flag"""
        cookies = [
            Cookie(
                name="httponly_cookie",
                value="httponly_value",
                http_only=True
            )
        ]

        response = cycletls_client.get(
            f"{httpbin_url}/cookies",
            cookies=cookies
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cookies"]["httponly_cookie"] == "httponly_value"

    def test_cookie_with_all_attributes(self, cycletls_client, httpbin_url):
        """Test sending cookie with all attributes"""
        future_date = datetime.now() + timedelta(days=1)

        cookies = [
            Cookie(
                name="full_cookie",
                value="full_value",
                domain=".httpbin.org",
                path="/cookies",
                secure=True,
                http_only=True,
                expires=future_date,
                same_site="Lax"
            )
        ]

        response = cycletls_client.get(
            f"{httpbin_url}/cookies",
            cookies=cookies
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cookies"]["full_cookie"] == "full_value"

    def test_multiple_cookies_with_attributes(self, cycletls_client, httpbin_url):
        """Test sending multiple cookies with different attributes"""
        cookies = [
            Cookie(name="cookie1", value="value1", path="/"),
            Cookie(name="cookie2", value="value2", secure=True),
            Cookie(name="cookie3", value="value3", http_only=True),
            Cookie(name="cookie4", value="value4", domain=".httpbin.org"),
        ]

        response = cycletls_client.get(
            f"{httpbin_url}/cookies",
            cookies=cookies
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cookies"]["cookie1"] == "value1"
        assert data["cookies"]["cookie2"] == "value2"
        assert data["cookies"]["cookie3"] == "value3"
        assert data["cookies"]["cookie4"] == "value4"

    def test_cookie_with_max_age(self, cycletls_client, httpbin_url):
        """Test sending cookie with max_age attribute"""
        cookies = [
            Cookie(
                name="maxage_cookie",
                value="maxage_value",
                max_age=3600  # 1 hour
            )
        ]

        response = cycletls_client.get(
            f"{httpbin_url}/cookies",
            cookies=cookies
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cookies"]["maxage_cookie"] == "maxage_value"

    def test_cookie_with_same_site_strict(self, cycletls_client, httpbin_url):
        """Test sending cookie with SameSite=Strict"""
        cookies = [
            Cookie(
                name="samesite_cookie",
                value="samesite_value",
                same_site="Strict"
            )
        ]

        response = cycletls_client.get(
            f"{httpbin_url}/cookies",
            cookies=cookies
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cookies"]["samesite_cookie"] == "samesite_value"

    def test_cookie_with_special_characters(self, cycletls_client, httpbin_url):
        """Test sending cookie with special characters in value"""
        cookies = [
            Cookie(
                name="special_cookie",
                value="value_with-special.chars_123"
            )
        ]

        response = cycletls_client.get(
            f"{httpbin_url}/cookies",
            cookies=cookies
        )

        assert response.status_code == 200
        data = response.json()
        assert "special_cookie" in data["cookies"]

    def test_empty_cookie_value(self, cycletls_client, httpbin_url):
        """Test sending cookie with empty value"""
        cookies = [
            Cookie(name="empty_cookie", value="")
        ]

        response = cycletls_client.get(
            f"{httpbin_url}/cookies",
            cookies=cookies
        )

        assert response.status_code == 200
        # Empty cookies may or may not be sent, but request should succeed

    def test_cookie_delete_operation(self, cycletls_client, httpbin_url):
        """Test cookie delete operation via /cookies/delete endpoint"""
        # First set a cookie
        response = cycletls_client.get(
            f"{httpbin_url}/cookies/set?test_cookie=test_value"
        )
        assert response.status_code == 200

        # Then delete it
        response = cycletls_client.get(
            f"{httpbin_url}/cookies/delete?test_cookie"
        )
        assert response.status_code == 200
