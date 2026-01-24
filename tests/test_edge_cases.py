"""
Test edge cases and error conditions for CycleTLS.

Tests various edge cases including:
- Empty responses
- No content responses (204)
- Redirect loops
- Invalid URLs
- DNS failures
- Connection refused
- Malformed responses
"""

import pytest
from cycletls import CycleTLS


class TestEdgeCases:
    """Test various edge cases and error conditions."""

    def test_empty_response_body(self, cycletls_client, httpbin_url):
        """Test handling of empty response body."""
        # /status/200 returns a 200 with no body
        response = cycletls_client.get(f"{httpbin_url}/status/200")

        assert response.status_code == 200
        assert response.body == ""

    def test_no_content_204(self, cycletls_client, httpbin_url):
        """Test handling of 204 No Content response."""
        response = cycletls_client.get(f"{httpbin_url}/status/204")

        assert response.status_code == 204
        assert response.body == ""

    def test_redirect_loop(self, cycletls_client, httpbin_url):
        """Test handling of redirect loops."""
        # httpbin's /redirect-to endpoint can be used to create a loop
        # Construct a redirect loop by redirecting to the same URL
        url = f"{httpbin_url}/redirect-to?url={httpbin_url}/redirect-to?url={httpbin_url}/get"

        try:
            # With redirects enabled, this should eventually succeed or timeout
            response = cycletls_client.get(url, timeout=5)
            # Should either work or raise an error
            assert response.status_code in [200, 301, 302, 307, 308]
        except Exception as e:
            # Expect timeout or redirect error
            assert "timeout" in str(e).lower() or "redirect" in str(e).lower()

    def test_invalid_url_missing_scheme(self, cycletls_client):
        """Test handling of invalid URL without scheme."""
        with pytest.raises(Exception):
            cycletls_client.get("example.com/path")

    def test_invalid_url_malformed(self, cycletls_client):
        """Test handling of malformed URL."""
        with pytest.raises(Exception):
            cycletls_client.get("http://not a valid url with spaces")

    def test_invalid_url_empty(self, cycletls_client):
        """Test handling of empty URL."""
        with pytest.raises(Exception):
            cycletls_client.get("")

    def test_dns_failure_nonexistent_domain(self, cycletls_client):
        """Test handling of DNS lookup failure."""
        with pytest.raises(Exception):
            cycletls_client.get(
                "https://this-domain-definitely-does-not-exist-12345.com",
                timeout=5
            )

    def test_connection_refused(self, cycletls_client):
        """Test handling of connection refused (port not listening)."""
        # Try to connect to localhost on a port that's unlikely to be in use
        with pytest.raises(Exception):
            cycletls_client.get(
                "http://localhost:59999",
                timeout=5
            )

    def test_timeout_on_slow_response(self, cycletls_client, httpbin_url):
        """Test timeout on slow responses."""
        # httpbin's /delay endpoint delays the response
        with pytest.raises(Exception):
            cycletls_client.get(
                f"{httpbin_url}/delay/10",
                timeout=2  # Request timeout of 2 seconds, but server delays 10
            )

    def test_various_http_error_codes(self, cycletls_client, httpbin_url):
        """Test handling of various HTTP error status codes."""
        error_codes = [400, 401, 403, 404, 405, 408, 429, 500, 502, 503, 504]

        for code in error_codes:
            response = cycletls_client.get(f"{httpbin_url}/status/{code}")
            assert response.status_code == code

    def test_gzip_empty_response(self, cycletls_client, httpbin_url):
        """Test handling of gzip compressed empty response."""
        response = cycletls_client.get(
            f"{httpbin_url}/gzip",
            headers={"Accept-Encoding": "gzip"}
        )

        assert response.status_code == 200
        # The response should be automatically decompressed
        assert "gzipped" in response.body.lower() or "true" in response.body.lower()

    def test_deflate_response(self, cycletls_client, httpbin_url):
        """Test handling of deflate compressed response."""
        response = cycletls_client.get(
            f"{httpbin_url}/deflate",
            headers={"Accept-Encoding": "deflate"}
        )

        assert response.status_code == 200
        # The response should be automatically decompressed
        assert "deflated" in response.body.lower() or "true" in response.body.lower()

    def test_large_response_body(self, cycletls_client, httpbin_url):
        """Test handling of large response body."""
        # Request 100KB of random bytes (httpbin caps at ~100KB)
        response = cycletls_client.get(f"{httpbin_url}/bytes/102400")

        assert response.status_code == 200
        # Binary data is in content (body_bytes), not body (which is empty for non-UTF-8)
        assert len(response.content) >= 100000  # Should be close to 100KB

    def test_special_characters_in_headers(self, cycletls_client, httpbin_url):
        """Test handling of special characters in headers."""
        response = cycletls_client.get(
            f"{httpbin_url}/headers",
            headers={
                "X-Custom-Header": "value-with-special-chars: !@#$%^&*()",
                "X-Unicode-Header": "Test-\u00e9\u00e8\u00ea"
            }
        )

        assert response.status_code == 200

    def test_multiple_set_cookie_headers(self, cycletls_client, httpbin_url):
        """Test handling of multiple Set-Cookie headers."""
        response = cycletls_client.get(f"{httpbin_url}/cookies/set?cookie1=value1&cookie2=value2")

        assert response.status_code == 200
        # Should handle multiple cookies
        if response.cookies:
            assert len(response.cookies) >= 1

    def test_redirect_with_different_method(self, cycletls_client, httpbin_url):
        """Test redirect that changes the HTTP method."""
        # POST to /redirect-to should be handled
        response = cycletls_client.post(
            f"{httpbin_url}/redirect-to?url={httpbin_url}/get",
            body="test data"
        )

        # After redirect, should be a GET request
        assert response.status_code == 200

    def test_very_long_url(self, cycletls_client, httpbin_url):
        """Test handling of very long URLs."""
        # Create a very long URL with query parameters
        long_query = "&".join([f"param{i}=value{i}" for i in range(100)])
        url = f"{httpbin_url}/get?{long_query}"

        response = cycletls_client.get(url)
        assert response.status_code == 200

    def test_response_with_null_bytes(self, cycletls_client, httpbin_url):
        """Test handling of response with null bytes."""
        # Request binary data which may contain null bytes
        response = cycletls_client.get(f"{httpbin_url}/bytes/256")

        assert response.status_code == 200
        # Binary data is in content (body_bytes), not body (which is empty for non-UTF-8)
        assert len(response.content) > 0

    def test_json_parse_error_handling(self, cycletls_client, httpbin_url):
        """Test json() method with non-JSON response."""
        response = cycletls_client.get(f"{httpbin_url}/html")

        assert response.status_code == 200
        with pytest.raises(Exception):
            response.json()

    def test_ipv6_url(self, cycletls_client):
        """Test handling of IPv6 URLs (if supported)."""
        # Note: This may fail if IPv6 is not available
        try:
            response = cycletls_client.get(
                "http://[::1]:80",
                timeout=2
            )
            # If it works, it should return a response
            assert response is not None
        except Exception:
            # It's okay if IPv6 is not supported
            pytest.skip("IPv6 not available or not supported")

    def test_mixed_case_headers(self, cycletls_client, httpbin_url):
        """Test handling of mixed case header names."""
        response = cycletls_client.get(
            f"{httpbin_url}/headers",
            headers={
                "Content-Type": "application/json",
                "content-type": "text/plain",  # Duplicate with different case
                "ACCEPT": "text/html"
            }
        )

        assert response.status_code == 200

    def test_empty_header_value(self, cycletls_client, httpbin_url):
        """Test handling of empty header values."""
        response = cycletls_client.get(
            f"{httpbin_url}/headers",
            headers={
                "X-Empty-Header": "",
                "X-Normal-Header": "value"
            }
        )

        assert response.status_code == 200

    def test_request_with_fragment(self, cycletls_client, httpbin_url):
        """Test URL with fragment identifier."""
        response = cycletls_client.get(f"{httpbin_url}/get#fragment")

        assert response.status_code == 200
        # Fragments are typically not sent to the server

    def test_303_see_other_redirect(self, cycletls_client, httpbin_url):
        """Test 303 See Other redirect handling."""
        response = cycletls_client.get(f"{httpbin_url}/status/303")

        # Should handle the redirect properly
        assert response.status_code in [200, 303]

    def test_100_continue_response(self, cycletls_client, httpbin_url):
        """Test handling of 100 Continue interim response."""
        # Most HTTP libraries handle this transparently
        response = cycletls_client.post(
            f"{httpbin_url}/post",
            headers={"Expect": "100-continue"},
            body="test data"
        )

        assert response.status_code == 200
