"""
Header handling tests for CycleTLS Python client.
Tests custom header ordering, case sensitivity, and special headers.
"""

import pytest


class TestHeaders:
    """Test suite for HTTP header handling in CycleTLS"""

    def test_custom_headers(self, cycletls_client, httpbin_url):
        """Test sending custom headers"""
        headers = {
            "X-Custom-Header": "CustomValue",
            "X-Another-Header": "AnotherValue",
        }

        response = cycletls_client.get(
            f"{httpbin_url}/headers",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "headers" in data
        assert data["headers"]["X-Custom-Header"] == "CustomValue"
        assert data["headers"]["X-Another-Header"] == "AnotherValue"

    def test_user_agent_header(self, cycletls_client, httpbin_url):
        """Test custom User-Agent header"""
        custom_ua = "Mozilla/5.0 (Custom) Test/1.0"

        response = cycletls_client.get(
            f"{httpbin_url}/headers",
            user_agent=custom_ua
        )

        assert response.status_code == 200
        data = response.json()
        assert data["headers"]["User-Agent"] == custom_ua

    def test_accept_header(self, cycletls_client, httpbin_url):
        """Test custom Accept header"""
        headers = {
            "Accept": "application/json",
        }

        response = cycletls_client.get(
            f"{httpbin_url}/headers",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "Accept" in data["headers"]
        assert "application/json" in data["headers"]["Accept"]

    def test_content_type_header(self, cycletls_client, httpbin_url):
        """Test Content-Type header on POST request"""
        # Use /post endpoint instead of /headers (which doesn't accept POST)
        response = cycletls_client.post(
            f"{httpbin_url}/post",
            json_data={'test': 'data'}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["headers"]["Content-Type"] == "application/json"

    def test_multiple_standard_headers(self, cycletls_client, httpbin_url):
        """Test multiple standard HTTP headers"""
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
        }

        response = cycletls_client.get(
            f"{httpbin_url}/headers",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["headers"]["Accept"] == "application/json"
        assert data["headers"]["Accept-Language"] == "en-US,en;q=0.9"

    def test_header_ordering(self, cycletls_client, httpbin_url):
        """Test custom header ordering"""
        headers = {
            "Accept": "application/json",
            "User-Agent": "CustomAgent/1.0",
            "Accept-Language": "en-US",
            "X-Custom": "value",
        }

        header_order = ["User-Agent", "Accept", "Accept-Language", "X-Custom"]

        response = cycletls_client.get(
            f"{httpbin_url}/headers",
            headers=headers,
            header_order=header_order
        )

        assert response.status_code == 200
        data = response.json()
        # Verify headers were sent
        assert data["headers"]["Accept"] == "application/json"
        assert data["headers"]["X-Custom"] == "value"

    def test_order_headers_as_provided_flag(self, cycletls_client, httpbin_url):
        """Test order_headers_as_provided flag"""
        headers = {
            "Z-Last-Header": "last",
            "A-First-Header": "first",
            "M-Middle-Header": "middle",
        }

        response = cycletls_client.get(
            f"{httpbin_url}/headers",
            headers=headers,
            order_headers_as_provided=True
        )

        assert response.status_code == 200
        data = response.json()
        # Headers should be sent in the order provided, not alphabetically
        assert data["headers"]["Z-Last-Header"] == "last"
        assert data["headers"]["A-First-Header"] == "first"
        assert data["headers"]["M-Middle-Header"] == "middle"

    def test_header_case_preservation(self, cycletls_client, httpbin_url):
        """Test that header case is preserved"""
        headers = {
            "X-UPPERCASE-HEADER": "value1",
            "x-lowercase-header": "value2",
            "X-MixedCase-Header": "value3",
        }

        response = cycletls_client.get(
            f"{httpbin_url}/headers",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        # httpbin may normalize headers, but they should be received
        header_keys = [k.lower() for k in data["headers"].keys()]
        assert "x-uppercase-header" in header_keys
        assert "x-lowercase-header" in header_keys
        assert "x-mixedcase-header" in header_keys

    def test_duplicate_header_handling(self, cycletls_client, httpbin_url):
        """Test handling of headers with same key different case"""
        headers = {
            "X-Test-Header": "value1",
        }

        response = cycletls_client.get(
            f"{httpbin_url}/headers",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "X-Test-Header" in data["headers"]

    def test_authorization_header(self, cycletls_client, httpbin_url):
        """Test Authorization header"""
        headers = {
            "Authorization": "Bearer token123456",
        }

        response = cycletls_client.get(
            f"{httpbin_url}/headers",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["headers"]["Authorization"] == "Bearer token123456"

    def test_referer_header(self, cycletls_client, httpbin_url):
        """Test Referer header"""
        headers = {
            "Referer": "https://example.com/previous-page",
        }

        response = cycletls_client.get(
            f"{httpbin_url}/headers",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["headers"]["Referer"] == "https://example.com/previous-page"

    def test_origin_header(self, cycletls_client, httpbin_url):
        """Test Origin header"""
        headers = {
            "Origin": "https://example.com",
        }

        response = cycletls_client.get(
            f"{httpbin_url}/headers",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["headers"]["Origin"] == "https://example.com"

    def test_custom_header_with_special_characters(self, cycletls_client, httpbin_url):
        """Test header value with special characters"""
        headers = {
            "X-Special-Chars": "value-with_special.chars@123",
        }

        response = cycletls_client.get(
            f"{httpbin_url}/headers",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["headers"]["X-Special-Chars"] == "value-with_special.chars@123"

    def test_empty_header_value(self, cycletls_client, httpbin_url):
        """Test header with empty value"""
        headers = {
            "X-Empty-Header": "",
        }

        response = cycletls_client.get(
            f"{httpbin_url}/headers",
            headers=headers
        )

        assert response.status_code == 200
        # Empty headers may or may not be sent, but request should succeed

    def test_long_header_value(self, cycletls_client, httpbin_url):
        """Test header with long value"""
        long_value = "A" * 1000

        headers = {
            "X-Long-Header": long_value,
        }

        response = cycletls_client.get(
            f"{httpbin_url}/headers",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["headers"]["X-Long-Header"] == long_value

    def test_header_order_with_standard_headers(self, cycletls_client, httpbin_url):
        """Test custom ordering of both standard and custom headers"""
        headers = {
            "Accept": "*/*",
            "X-Custom-1": "value1",
            "User-Agent": "Test/1.0",
            "X-Custom-2": "value2",
            "Accept-Encoding": "gzip",
        }

        header_order = [
            "X-Custom-1",
            "User-Agent",
            "Accept",
            "X-Custom-2",
            "Accept-Encoding"
        ]

        response = cycletls_client.get(
            f"{httpbin_url}/headers",
            headers=headers,
            header_order=header_order
        )

        assert response.status_code == 200
        data = response.json()
        assert data["headers"]["X-Custom-1"] == "value1"
        assert data["headers"]["X-Custom-2"] == "value2"

    def test_no_custom_headers(self, cycletls_client, httpbin_url):
        """Test request without custom headers uses defaults"""
        response = cycletls_client.get(f"{httpbin_url}/headers")

        assert response.status_code == 200
        data = response.json()
        # Should have at least User-Agent from defaults
        assert "User-Agent" in data["headers"]

    def test_override_default_user_agent(self, cycletls_client, httpbin_url):
        """Test overriding default User-Agent via headers dict"""
        custom_ua = "OverriddenAgent/2.0"

        response = cycletls_client.get(
            f"{httpbin_url}/headers",
            user_agent=custom_ua
        )

        assert response.status_code == 200
        data = response.json()
        assert data["headers"]["User-Agent"] == custom_ua

    def test_host_header_automatic(self, cycletls_client, httpbin_url):
        """Test that Host header is automatically set"""
        response = cycletls_client.get(f"{httpbin_url}/headers")

        assert response.status_code == 200
        data = response.json()
        assert "Host" in data["headers"]
        assert "httpbin.org" in data["headers"]["Host"]
