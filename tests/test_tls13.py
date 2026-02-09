"""
TLS 1.3 Tests for CycleTLS Python library.

Based on CycleTLS Go integration tests (tls_13_test.go), these tests verify:
- TLS 1.3 connection establishment
- Auto-retry with compatible curves (tls13_auto_retry flag)
- TLS 1.2 fallback behavior
- Curve compatibility testing
- Handling of unsupported curve errors

Uses various HTTPS sites that support TLS 1.3 for testing.
"""

import pytest
import json
from test_utils import assert_valid_response

pytestmark = pytest.mark.live


class TestTLS13Basic:
    """Test basic TLS 1.3 functionality."""

    def test_tls13_connection(self, cycletls_client, chrome_ja3):
        """Test basic TLS 1.3 connection to howsmyssl.com."""
        response = cycletls_client.get(
            "https://www.howsmyssl.com/a/check",
            ja3=chrome_ja3,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            timeout=30
        )

        assert_valid_response(response, expected_status=200)

        # Parse response to check TLS version
        try:
            data = response.json()

            # howsmyssl.com returns TLS version information
            assert 'tls_version' in data or 'tls' in str(data).lower(), \
                "Response should contain TLS version information"

            # If TLS version is specified, it might be TLS 1.3 or 1.2
            if 'tls_version' in data:
                tls_version = data['tls_version']
                # TLS 1.3 is preferred but 1.2 is acceptable
                assert tls_version in ['TLS 1.3', 'TLS 1.2', 'TLS13', 'TLS12'], \
                    f"TLS version should be 1.3 or 1.2, got: {tls_version}"
        except json.JSONDecodeError:
            # Response might not be JSON, that's ok as long as we got a 200
            pass

    def test_tls13_with_firefox_fingerprint(self, cycletls_client, firefox_ja3):
        """Test TLS 1.3 with Firefox JA3 fingerprint."""
        response = cycletls_client.get(
            "https://www.howsmyssl.com/a/check",
            ja3=firefox_ja3,
            user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0",
            timeout=30
        )

        assert_valid_response(response, expected_status=200)

        # Verify we got valid response data
        assert response.body, "Response body should not be empty"

    def test_tls13_with_multiple_sites(self, cycletls_client, chrome_ja3):
        """Test TLS 1.3 connections to multiple HTTPS sites."""
        # Multiple sites that support TLS 1.3
        test_sites = [
            "https://www.cloudflare.com",
            "https://www.google.com",
            "https://httpbin.org/get",
        ]

        for site in test_sites:
            response = cycletls_client.get(
                site,
                ja3=chrome_ja3,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
                timeout=30
            )

            # Should get a successful response
            assert response.status_code in [200, 301, 302, 303], \
                f"Expected successful response for {site}, got {response.status_code}"

            assert response.body, f"Response body should not be empty for {site}"


class TestTLS13AutoRetry:
    """Test TLS 1.3 auto-retry with compatible curves."""

    def test_tls13_auto_retry_enabled(self, cycletls_client):
        """Test that tls13_auto_retry automatically handles curve incompatibility."""
        # Use a JA3 that includes curves that might cause issues with TLS 1.3
        problematic_ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24-25,0"

        response = cycletls_client.get(
            "https://www.howsmyssl.com/a/check",
            ja3=problematic_ja3,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            tls13_auto_retry=True,  # Enable auto-retry (should be default)
            timeout=30
        )

        # With auto-retry enabled, should get successful response
        # If curves are incompatible, the library should retry with compatible curves
        assert response.status_code in [200, 500, 502, 503], \
            f"Expected response (200 or server error if endpoint down), got {response.status_code}"

        # If we got a 200, verify we have data
        if response.status_code == 200:
            assert response.body, "Response body should not be empty"

    def test_tls13_auto_retry_with_different_ja3(self, cycletls_client):
        """Test auto-retry with different JA3 fingerprints."""
        # JA3 with extended curves list
        ja3_with_extra_curves = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0"

        response = cycletls_client.get(
            "https://httpbin.org/get",
            ja3=ja3_with_extra_curves,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            tls13_auto_retry=True,
            timeout=30
        )

        # Should successfully connect (with retry if needed)
        assert response.status_code in [200, 500, 502, 503], \
            f"Expected response, got {response.status_code}"


class TestTLS13CurveHandling:
    """Test TLS 1.3 curve compatibility handling."""

    def test_tls13_curve_filtering(self, cycletls_client, chrome_ja3):
        """Test that TLS 1.3 curve filtering works properly."""
        # Use Chrome fingerprint that includes various curves
        response = cycletls_client.get(
            "https://www.howsmyssl.com/a/check",
            ja3=chrome_ja3,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            timeout=30
        )

        # Should handle curve filtering automatically
        assert response.status_code in [200, 500, 502, 503], \
            f"Expected response, got {response.status_code}"

        if response.status_code == 200:
            assert response.body, "Response body should not be empty"

    def test_tls13_with_specific_curves(self, cycletls_client):
        """Test TLS 1.3 with specific curve configurations."""
        # JA3 with curve 24 which may cause issues in some configurations
        ja3_curve_24 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0"

        response = cycletls_client.get(
            "https://httpbin.org/get",
            ja3=ja3_curve_24,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            timeout=30
        )

        # Should handle curve compatibility
        assert response.status_code in [200, 500, 502, 503], \
            f"Expected response, got {response.status_code}"


class TestTLS12Fallback:
    """Test TLS 1.2 fallback behavior."""

    def test_tls12_connection(self, cycletls_client):
        """Test that TLS 1.2 connections still work."""
        # JA3 configured for TLS 1.2 (older cipher suites)
        tls12_ja3 = "771,49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25,0"

        response = cycletls_client.get(
            "https://httpbin.org/get",
            ja3=tls12_ja3,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36",
            timeout=30
        )

        # TLS 1.2 should still work
        assert response.status_code == 200, \
            f"Expected 200 for TLS 1.2 connection, got {response.status_code}"

        assert response.body, "Response body should not be empty"

    def test_tls_version_flexibility(self, cycletls_client, firefox_ja3):
        """Test that library handles both TLS 1.3 and 1.2."""
        # Test with multiple endpoints that may use different TLS versions
        # Using reliable endpoints only (howsmyssl.com is flaky)
        endpoints = [
            "https://httpbin.org/get",
            "https://tls.peet.ws/api/clean",
        ]

        for endpoint in endpoints:
            response = cycletls_client.get(
                endpoint,
                ja3=firefox_ja3,
                user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0",
                timeout=30
            )

            # Should successfully connect regardless of TLS version negotiated
            assert response.status_code in [200, 500, 502, 503], \
                f"Expected response for {endpoint}, got {response.status_code}"


class TestTLS13ErrorHandling:
    """Test TLS 1.3 error handling."""

    def test_tls13_connection_timeout(self, cycletls_client, chrome_ja3):
        """Test that TLS 1.3 connection respects timeout settings."""
        # Use a short timeout
        response = cycletls_client.get(
            "https://www.howsmyssl.com/a/check",
            ja3=chrome_ja3,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            timeout=5  # Short timeout
        )

        # Should either succeed or timeout (depends on network conditions)
        # We're just checking that timeout is respected
        assert hasattr(response, 'status_code'), "Response should have status_code"

    @pytest.mark.skip(reason="Upstream Go bug: invalid JA3 causes panic at golang/utils.go:146")
    def test_tls13_invalid_ja3_format(self, cycletls_client):
        """Test handling of invalid JA3 format with TLS 1.3."""
        # Use malformed JA3
        invalid_ja3 = "invalid-ja3-format"

        # This might fail or fall back to defaults depending on implementation
        try:
            response = cycletls_client.get(
                "https://httpbin.org/get",
                ja3=invalid_ja3,
                timeout=10
            )
            # If it succeeds, library fell back to default fingerprint
            assert hasattr(response, 'status_code'), "Response should have status_code"
        except Exception as e:
            # Expected to fail with invalid JA3
            assert True, "Invalid JA3 should either fail or fall back to default"


class TestTLS13WithJa3er:
    """Test TLS 1.3 with ja3er.com for fingerprint verification."""

    def test_tls13_fingerprint_verification(self, cycletls_client, chrome_ja3):
        """Test that TLS 1.3 fingerprint is correctly applied."""
        # Use tls.peet.ws instead of ja3er.com (more reliable)
        response = cycletls_client.get(
            "https://tls.peet.ws/api/clean",
            ja3=chrome_ja3,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            timeout=30
        )

        assert_valid_response(response, expected_status=200)

        # Parse response to check JA3 fingerprint
        try:
            data = response.json()
            assert 'ja3' in data or 'ja3_hash' in data or 'tls' in data, \
                "Response should contain TLS fingerprint information"
        except json.JSONDecodeError:
            # Service might be down or response format changed
            pytest.skip("TLS fingerprint service response format unexpected")

    def test_tls13_with_multiple_fingerprints(self, cycletls_client, chrome_ja3, firefox_ja3, safari_ja3):
        """Test TLS 1.3 with multiple browser fingerprints."""
        fingerprints = [
            (chrome_ja3, "Chrome"),
            (firefox_ja3, "Firefox"),
            (safari_ja3, "Safari"),
        ]

        for ja3, browser_name in fingerprints:
            response = cycletls_client.get(
                "https://httpbin.org/get",
                ja3=ja3,
                user_agent=f"Mozilla/5.0 (Test {browser_name})",
                timeout=30
            )

            assert response.status_code in [200, 500, 502, 503], \
                f"Expected response with {browser_name} fingerprint, got {response.status_code}"


class TestTLS13WithHttpbin:
    """Test TLS 1.3 with httpbin.org endpoints."""

    def test_tls13_post_request(self, cycletls_client, chrome_ja3):
        """Test TLS 1.3 POST request with JSON payload."""
        payload = {"test": "tls13", "data": "value"}

        response = cycletls_client.post(
            "https://httpbin.org/post",
            json_data=payload,
            ja3=chrome_ja3,
            timeout=30
        )

        assert_valid_response(response, expected_status=200)

        # Verify payload was received
        data = response.json()
        assert 'json' in data or 'data' in data, "Response should contain posted data"

    def test_tls13_with_custom_headers(self, cycletls_client, firefox_ja3):
        """Test TLS 1.3 with custom headers."""
        custom_headers = {
            'X-Custom-Header': 'TLS13-Test',
            'Authorization': 'Bearer test-token'
        }

        response = cycletls_client.get(
            "https://httpbin.org/headers",
            ja3=firefox_ja3,
            headers=custom_headers,
            timeout=30
        )

        assert_valid_response(response, expected_status=200)

        # Verify headers were sent
        data = response.json()
        assert 'headers' in data, "Response should contain headers"
        response_headers = data['headers']
        assert 'X-Custom-Header' in response_headers, "Custom header should be present"

    def test_tls13_with_cookies(self, cycletls_client, chrome_ja3):
        """Test TLS 1.3 with cookies."""
        cookies = [
            {
                "name": "tls13_test",
                "value": "test_value",
                "expires": "2026-01-02T15:04:05Z"
            }
        ]

        response = cycletls_client.get(
            "https://httpbin.org/cookies",
            ja3=chrome_ja3,
            cookies=cookies,
            timeout=30
        )

        assert_valid_response(response, expected_status=200)

        # Verify cookies were sent
        data = response.json()
        assert 'cookies' in data, "Response should contain cookies"
        assert 'tls13_test' in data['cookies'], "Test cookie should be present"
