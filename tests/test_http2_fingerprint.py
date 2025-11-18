"""
HTTP/2 Fingerprinting Tests for CycleTLS Python library.

Based on CycleTLS TypeScript http2-fingerprint tests, these tests verify:
- Custom HTTP/2 settings using http2_fingerprint parameter
- Priority configuration
- Stream dependency
- Fingerprint validation with various browsers
- Testing with fingerprint detection endpoints (peet.ws, scrapfly.io)

HTTP/2 fingerprints allow customization of HTTP/2 connection settings to mimic
different browsers and avoid detection.
"""

import pytest
import json
from test_utils import assert_valid_response, assert_valid_json_response


class TestHTTP2FingerprintBasic:
    """Test basic HTTP/2 fingerprinting functionality."""

    def test_firefox_http2_fingerprint_peetws(self, cycletls_client):
        """Test Firefox HTTP/2 fingerprint with peet.ws."""
        # Firefox HTTP/2 fingerprint format:
        # SETTINGS_HEADER_TABLE_SIZE:SETTINGS_ENABLE_PUSH:SETTINGS_MAX_CONCURRENT_STREAMS:SETTINGS_INITIAL_WINDOW_SIZE|WINDOW_UPDATE|PRIORITY_FRAMES|STREAM_PRIORITY
        firefox_http2 = "1:65536;2:0;4:131072;5:16384|12517377|0|m,p,a,s"

        response = cycletls_client.get(
            'https://tls.peet.ws/api/all',
            http2_fingerprint=firefox_http2,
            user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0',
            timeout=30
        )

        assert_valid_response(response, expected_status=200)

        try:
            data = response.json()

            # Validate HTTP/2 is being used
            assert 'http_version' in data or 'http2' in data, \
                "Response should contain HTTP version information"

            if 'http_version' in data:
                assert data['http_version'] in ['h2', 'HTTP/2.0', 'HTTP/2'], \
                    f"Expected HTTP/2, got {data['http_version']}"

            # Check for HTTP/2 fingerprint data
            if 'http2' in data:
                assert 'akamai_fingerprint' in data['http2'] or 'fingerprint' in data['http2'], \
                    "Response should contain HTTP/2 fingerprint information"
        except json.JSONDecodeError:
            # Response might not be JSON or endpoint might be down
            pytest.skip("peet.ws response format unexpected or endpoint unavailable")

    def test_chrome_http2_fingerprint_peetws(self, cycletls_client):
        """Test Chrome HTTP/2 fingerprint with peet.ws."""
        # Chrome HTTP/2 fingerprint
        chrome_http2 = "1:65536;2:0;4:6291456;6:262144|15663105|0|m,a,s,p"

        response = cycletls_client.get(
            'https://tls.peet.ws/api/all',
            http2_fingerprint=chrome_http2,
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            timeout=30
        )

        assert_valid_response(response, expected_status=200)

        try:
            data = response.json()

            # Validate HTTP/2 is being used
            if 'http_version' in data:
                assert data['http_version'] in ['h2', 'HTTP/2.0', 'HTTP/2'], \
                    f"Expected HTTP/2, got {data['http_version']}"

            # Check for HTTP/2 data
            if 'http2' in data:
                assert data['http2'] is not None, "HTTP/2 data should be present"
        except json.JSONDecodeError:
            pytest.skip("peet.ws response format unexpected or endpoint unavailable")

    def test_firefox_http2_fingerprint_scrapfly(self, cycletls_client):
        """Test Firefox HTTP/2 fingerprint with scrapfly.io."""
        firefox_http2 = "1:65536;2:0;4:131072;5:16384|12517377|0|m,p,a,s"

        response = cycletls_client.get(
            'https://tools.scrapfly.io/api/fp/anything',
            http2_fingerprint=firefox_http2,
            user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0',
            timeout=30
        )

        assert_valid_response(response, expected_status=200)

        try:
            data = response.json()

            # Validate HTTP/2 protocol
            assert 'http_protocol_version' in data or 'http2' in data, \
                "Response should contain HTTP protocol information"

            if 'http_protocol_version' in data:
                assert 'HTTP/2' in data['http_protocol_version'], \
                    f"Expected HTTP/2, got {data['http_protocol_version']}"

            # Check for HTTP/2 fingerprint
            if 'http2' in data:
                assert 'fingerprint' in data['http2'] or data['http2'], \
                    "HTTP/2 fingerprint data should be present"
        except json.JSONDecodeError:
            pytest.skip("scrapfly.io response format unexpected or endpoint unavailable")

    def test_chrome_http2_fingerprint_scrapfly(self, cycletls_client):
        """Test Chrome HTTP/2 fingerprint with scrapfly.io."""
        chrome_http2 = "1:65536;2:0;4:6291456;6:262144|15663105|0|m,a,s,p"

        response = cycletls_client.get(
            'https://tools.scrapfly.io/api/fp/anything',
            http2_fingerprint=chrome_http2,
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            timeout=30
        )

        assert_valid_response(response, expected_status=200)

        try:
            data = response.json()

            # Validate HTTP/2 protocol
            if 'http_protocol_version' in data:
                assert 'HTTP/2' in data['http_protocol_version'], \
                    f"Expected HTTP/2, got {data['http_protocol_version']}"

            # Check for HTTP/2 data
            if 'http2' in data:
                assert data['http2'], "HTTP/2 data should be present"
        except json.JSONDecodeError:
            pytest.skip("scrapfly.io response format unexpected or endpoint unavailable")


class TestHTTP2Settings:
    """Test custom HTTP/2 settings configuration."""

    def test_custom_header_table_size(self, cycletls_client):
        """Test custom SETTINGS_HEADER_TABLE_SIZE."""
        # Custom HTTP/2 settings with specific header table size
        custom_http2 = "1:32768;2:0;4:131072;5:16384|12517377|0|m,p,a,s"

        response = cycletls_client.get(
            'https://httpbin.org/get',
            http2_fingerprint=custom_http2,
            timeout=30
        )

        # Should successfully connect with custom settings
        assert response.status_code in [200, 500, 502, 503], \
            f"Expected response, got {response.status_code}"

    def test_custom_initial_window_size(self, cycletls_client):
        """Test custom SETTINGS_INITIAL_WINDOW_SIZE."""
        # Custom window size settings
        custom_http2 = "1:65536;2:0;4:262144;5:16384|12517377|0|m,p,a,s"

        response = cycletls_client.get(
            'https://httpbin.org/get',
            http2_fingerprint=custom_http2,
            timeout=30
        )

        assert response.status_code in [200, 500, 502, 503], \
            f"Expected response, got {response.status_code}"

    def test_custom_max_concurrent_streams(self, cycletls_client):
        """Test custom SETTINGS_MAX_CONCURRENT_STREAMS."""
        # Custom max concurrent streams
        custom_http2 = "1:65536;2:0;4:100;5:16384|12517377|0|m,p,a,s"

        response = cycletls_client.get(
            'https://httpbin.org/get',
            http2_fingerprint=custom_http2,
            timeout=30
        )

        assert response.status_code in [200, 500, 502, 503], \
            f"Expected response, got {response.status_code}"


class TestHTTP2Priority:
    """Test HTTP/2 priority configuration."""

    def test_firefox_priority_order(self, cycletls_client):
        """Test Firefox priority order (m,p,a,s)."""
        # Firefox uses: method, path, authority, scheme
        firefox_http2 = "1:65536;2:0;4:131072;5:16384|12517377|0|m,p,a,s"

        response = cycletls_client.get(
            'https://httpbin.org/get',
            http2_fingerprint=firefox_http2,
            user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0',
            timeout=30
        )

        assert_valid_response(response, expected_status=200)

    def test_chrome_priority_order(self, cycletls_client):
        """Test Chrome priority order (m,a,s,p)."""
        # Chrome uses: method, authority, scheme, path
        chrome_http2 = "1:65536;2:0;4:6291456;6:262144|15663105|0|m,a,s,p"

        response = cycletls_client.get(
            'https://httpbin.org/get',
            http2_fingerprint=chrome_http2,
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            timeout=30
        )

        assert_valid_response(response, expected_status=200)

    def test_safari_priority_order(self, cycletls_client):
        """Test Safari-like priority order."""
        # Safari-like settings
        safari_http2 = "1:65536;2:0;4:131072;5:16384|12517377|0|m,a,p,s"

        response = cycletls_client.get(
            'https://httpbin.org/get',
            http2_fingerprint=safari_http2,
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            timeout=30
        )

        assert_valid_response(response, expected_status=200)


class TestHTTP2WindowUpdate:
    """Test HTTP/2 window update configuration."""

    def test_firefox_window_update(self, cycletls_client):
        """Test Firefox window update value."""
        # Firefox window update: 12517377
        firefox_http2 = "1:65536;2:0;4:131072;5:16384|12517377|0|m,p,a,s"

        response = cycletls_client.get(
            'https://httpbin.org/get',
            http2_fingerprint=firefox_http2,
            timeout=30
        )

        assert_valid_response(response, expected_status=200)

    def test_chrome_window_update(self, cycletls_client):
        """Test Chrome window update value."""
        # Chrome window update: 15663105
        chrome_http2 = "1:65536;2:0;4:6291456;6:262144|15663105|0|m,a,s,p"

        response = cycletls_client.get(
            'https://httpbin.org/get',
            http2_fingerprint=chrome_http2,
            timeout=30
        )

        assert_valid_response(response, expected_status=200)

    def test_custom_window_update(self, cycletls_client):
        """Test custom window update value."""
        # Custom window update value
        custom_http2 = "1:65536;2:0;4:131072;5:16384|10000000|0|m,p,a,s"

        response = cycletls_client.get(
            'https://httpbin.org/get',
            http2_fingerprint=custom_http2,
            timeout=30
        )

        assert response.status_code in [200, 500, 502, 503], \
            f"Expected response, got {response.status_code}"


class TestHTTP2WithOtherFeatures:
    """Test HTTP/2 fingerprinting combined with other features."""

    def test_http2_with_custom_headers(self, cycletls_client):
        """Test HTTP/2 fingerprint with custom headers."""
        chrome_http2 = "1:65536;2:0;4:6291456;6:262144|15663105|0|m,a,s,p"

        custom_headers = {
            'X-Custom-Header': 'HTTP2-Test',
            'Authorization': 'Bearer test-token'
        }

        response = cycletls_client.get(
            'https://httpbin.org/headers',
            http2_fingerprint=chrome_http2,
            headers=custom_headers,
            timeout=30
        )

        assert_valid_response(response, expected_status=200)

        # Verify headers were sent
        data = response.json()
        assert 'headers' in data, "Response should contain headers"
        assert 'X-Custom-Header' in data['headers'], "Custom header should be present"

    def test_http2_with_cookies(self, cycletls_client):
        """Test HTTP/2 fingerprint with cookies."""
        firefox_http2 = "1:65536;2:0;4:131072;5:16384|12517377|0|m,p,a,s"

        cookies = [
            {
                "name": "http2_test",
                "value": "test_value",
                "expires": "2026-01-02T15:04:05Z"
            }
        ]

        response = cycletls_client.get(
            'https://httpbin.org/cookies',
            http2_fingerprint=firefox_http2,
            cookies=cookies,
            timeout=30
        )

        assert_valid_response(response, expected_status=200)

        # Verify cookies were sent
        data = response.json()
        assert 'cookies' in data, "Response should contain cookies"
        assert 'http2_test' in data['cookies'], "Test cookie should be present"

    def test_http2_with_ja3_fingerprint(self, cycletls_client, chrome_ja3):
        """Test HTTP/2 fingerprint combined with JA3 fingerprint."""
        chrome_http2 = "1:65536;2:0;4:6291456;6:262144|15663105|0|m,a,s,p"

        response = cycletls_client.get(
            'https://httpbin.org/get',
            http2_fingerprint=chrome_http2,
            ja3=chrome_ja3,
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            timeout=30
        )

        assert_valid_response(response, expected_status=200)

    def test_http2_post_request(self, cycletls_client):
        """Test HTTP/2 fingerprint with POST request."""
        firefox_http2 = "1:65536;2:0;4:131072;5:16384|12517377|0|m,p,a,s"

        payload = {"test": "http2", "data": "value"}

        response = cycletls_client.post(
            'https://httpbin.org/post',
            json_data=payload,
            http2_fingerprint=firefox_http2,
            timeout=30
        )

        assert_valid_response(response, expected_status=200)

        # Verify payload was received
        data = response.json()
        assert 'json' in data or 'data' in data, "Response should contain posted data"


class TestHTTP2EdgeCases:
    """Test edge cases in HTTP/2 fingerprinting."""

    def test_http2_with_minimal_settings(self, cycletls_client):
        """Test HTTP/2 with minimal settings."""
        # Minimal HTTP/2 settings
        minimal_http2 = "1:4096;2:0;4:65536|10000000|0|m,p,a,s"

        response = cycletls_client.get(
            'https://httpbin.org/get',
            http2_fingerprint=minimal_http2,
            timeout=30
        )

        assert response.status_code in [200, 500, 502, 503], \
            f"Expected response, got {response.status_code}"

    def test_http2_with_large_settings(self, cycletls_client):
        """Test HTTP/2 with large settings values."""
        # Large settings values
        large_http2 = "1:131072;2:0;4:16777216;6:524288|20000000|0|m,a,s,p"

        response = cycletls_client.get(
            'https://httpbin.org/get',
            http2_fingerprint=large_http2,
            timeout=30
        )

        assert response.status_code in [200, 500, 502, 503], \
            f"Expected response, got {response.status_code}"

    def test_http2_without_fingerprint(self, cycletls_client):
        """Test that requests work without HTTP/2 fingerprint (uses defaults)."""
        response = cycletls_client.get(
            'https://httpbin.org/get',
            timeout=30
        )

        assert_valid_response(response, expected_status=200)

    def test_http2_empty_fingerprint(self, cycletls_client):
        """Test handling of empty HTTP/2 fingerprint."""
        # Empty fingerprint should fall back to defaults
        response = cycletls_client.get(
            'https://httpbin.org/get',
            http2_fingerprint="",
            timeout=30
        )

        # Should either use defaults or handle gracefully
        assert response.status_code in [200, 400, 500, 502, 503], \
            f"Expected response or error, got {response.status_code}"


class TestHTTP2MultipleBrowsers:
    """Test HTTP/2 fingerprints from multiple browsers."""

    def test_compare_firefox_chrome_fingerprints(self, cycletls_client):
        """Test that different browser fingerprints both work."""
        firefox_http2 = "1:65536;2:0;4:131072;5:16384|12517377|0|m,p,a,s"
        chrome_http2 = "1:65536;2:0;4:6291456;6:262144|15663105|0|m,a,s,p"

        # Test Firefox fingerprint
        firefox_response = cycletls_client.get(
            'https://httpbin.org/get',
            http2_fingerprint=firefox_http2,
            user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0',
            timeout=30
        )
        assert_valid_response(firefox_response, expected_status=200)

        # Test Chrome fingerprint
        chrome_response = cycletls_client.get(
            'https://httpbin.org/get',
            http2_fingerprint=chrome_http2,
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            timeout=30
        )
        assert_valid_response(chrome_response, expected_status=200)

    def test_edge_http2_fingerprint(self, cycletls_client):
        """Test Edge browser HTTP/2 fingerprint."""
        # Edge typically uses similar settings to Chrome
        edge_http2 = "1:65536;2:0;4:6291456;6:262144|15663105|0|m,a,s,p"

        response = cycletls_client.get(
            'https://httpbin.org/get',
            http2_fingerprint=edge_http2,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
            timeout=30
        )

        assert_valid_response(response, expected_status=200)


class TestHTTP2FingerprintValidation:
    """Test HTTP/2 fingerprint validation and error handling."""

    def test_http2_with_multiple_endpoints(self, cycletls_client):
        """Test HTTP/2 fingerprint works across multiple endpoints."""
        chrome_http2 = "1:65536;2:0;4:6291456;6:262144|15663105|0|m,a,s,p"

        endpoints = [
            'https://httpbin.org/get',
            'https://httpbin.org/headers',
            'https://httpbin.org/user-agent',
        ]

        for endpoint in endpoints:
            response = cycletls_client.get(
                endpoint,
                http2_fingerprint=chrome_http2,
                timeout=30
            )

            assert_valid_response(response, expected_status=200), \
                f"Failed for endpoint: {endpoint}"

    def test_http2_connection_reuse(self, cycletls_client):
        """Test that HTTP/2 fingerprint works with connection reuse."""
        firefox_http2 = "1:65536;2:0;4:131072;5:16384|12517377|0|m,p,a,s"

        # Make multiple requests to same host
        for i in range(3):
            response = cycletls_client.get(
                'https://httpbin.org/get',
                http2_fingerprint=firefox_http2,
                timeout=30
            )

            assert_valid_response(response, expected_status=200), \
                f"Failed on request {i+1}"
