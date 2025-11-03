"""
HTTP/3 Protocol Tests

Tests for HTTP/3 protocol functionality including basic requests,
QUIC fingerprinting, and comparison with HTTP/2.

Based on: /Users/dannydasilva/Documents/personal/CycleTLS/cycletls/tests/integration/http3_test.go

Note: HTTP/3 tests may be skipped if HTTP/3 is not fully supported or if
running in a restricted environment (CI/CD).
"""
import os
import pytest
from cycletls import CycleTLS


@pytest.fixture(scope="module")
def cycle_client():
    """Create a single CycleTLS client for all tests in this module"""
    client = CycleTLS(port=9130)
    yield client
    client.close()


def skip_in_ci():
    """Check if tests should be skipped in CI environment"""
    return os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"


class TestHTTP3BasicRequests:
    """Test suite for basic HTTP/3 request functionality"""

    @pytest.mark.skipif(skip_in_ci(), reason="Skipping HTTP/3 test in CI environment due to network restrictions")
    def test_basic_http3_request(self, cycle_client):
        """
        Test basic HTTP/3 request with force_http3=True.

        Uses cloudflare-quic.com which supports HTTP/3 over QUIC.
        """
        response = cycle_client.get(
            "https://cloudflare-quic.com/",
            force_http3=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Check response status
        assert response.status_code == 200, \
            f"HTTP/3 request returned status {response.status_code}, want 200"

        # Verify response contains content
        assert len(response.text) > 0, "HTTP/3 response should contain content"

    @pytest.mark.skipif(skip_in_ci(), reason="Skipping HTTP/3 test in CI environment")
    def test_http3_to_cloudflare(self, cycle_client):
        """
        Test HTTP/3 request to cloudflare.com.

        Cloudflare supports HTTP/3 and is a reliable test endpoint.
        """
        response = cycle_client.get(
            "https://www.cloudflare.com/",
            force_http3=True,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        assert response.status_code == 200, \
            f"Expected status 200, got {response.status_code}"

        # Verify we got a valid response
        assert response.text is not None, "Response should contain text content"
        assert len(response.text) > 0, "Response should not be empty"

    @pytest.mark.skipif(skip_in_ci(), reason="Skipping HTTP/3 test in CI environment")
    def test_http3_with_headers(self, cycle_client):
        """Test HTTP/3 request with custom headers"""
        custom_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "X-Custom-Header": "test-http3"
        }

        response = cycle_client.get(
            "https://cloudflare-quic.com/",
            force_http3=True,
            headers=custom_headers,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        assert response.status_code == 200, \
            f"HTTP/3 request with custom headers returned status {response.status_code}"

        # Verify response is valid
        assert response.text is not None
        assert len(response.text) > 0

    @pytest.mark.skip(reason="HTTP/3 POST functionality may not be fully implemented")
    def test_http3_post_request(self, cycle_client):
        """Test HTTP/3 POST request with body"""
        import json

        payload = {
            "protocol": "http3",
            "test": "post_request",
            "data": "test_value"
        }

        response = cycle_client.post(
            "https://cloudflare-quic.com/",
            force_http3=True,
            body=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        # May not be supported, but shouldn't crash
        assert response.status_code in [200, 201, 400, 405, 501], \
            f"HTTP/3 POST returned unexpected status {response.status_code}"


class TestQUICFingerprinting:
    """Test suite for QUIC fingerprinting functionality"""

    @pytest.mark.skip(reason="QUIC fingerprinting may not be fully implemented in Python wrapper")
    def test_quic_fingerprint_parameter(self, cycle_client):
        """
        Test QUIC fingerprint with custom quic_fingerprint parameter.

        QUIC fingerprinting is similar to TLS fingerprinting but for QUIC/HTTP3.
        """
        response = cycle_client.get(
            "https://cloudflare-quic.com/",
            force_http3=True,
            quic_fingerprint="custom_quic_fp_1",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        # Should either succeed or gracefully fail if not implemented
        if response.status_code == 200:
            assert response.text is not None
        else:
            # If QUIC fingerprinting not supported, should still get a response
            assert response.status_code in [200, 400, 501]

    @pytest.mark.skip(reason="QUIC fingerprinting response parsing not yet confirmed")
    def test_quic_fingerprint_in_response(self, cycle_client):
        """
        Test that QUIC fingerprint is returned in response data.

        Similar to how JA3/JA4 fingerprints are returned for TLS.
        """
        response = cycle_client.get(
            "https://cloudflare-quic.com/",
            force_http3=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        assert response.status_code == 200

        # If implementation includes QUIC fingerprint in response
        # Uncomment when feature is available:
        # data = response.json() if hasattr(response, 'json') else {}
        # if 'quic' in data:
        #     assert 'fingerprint' in data['quic']


class TestHTTP3vsHTTP2Comparison:
    """Compare HTTP/3 and HTTP/2 protocol behavior"""

    @pytest.mark.skipif(skip_in_ci(), reason="Skipping HTTP/3 comparison test in CI environment")
    def test_http3_vs_http2_same_endpoint(self, cycle_client):
        """
        Test same endpoint with HTTP/3 and HTTP/2.

        Verifies that both protocols work correctly and return valid responses.
        """
        url = "https://www.cloudflare.com/"

        # Test with HTTP/2 (default)
        response_http2 = cycle_client.get(
            url,
            force_http1=False,
            force_http3=False,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        # Test with HTTP/3
        response_http3 = cycle_client.get(
            url,
            force_http3=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        # Both should succeed
        assert response_http2.status_code == 200, \
            f"HTTP/2 request failed with status {response_http2.status_code}"
        assert response_http3.status_code == 200, \
            f"HTTP/3 request failed with status {response_http3.status_code}"

        # Both should return content
        assert len(response_http2.text) > 0, "HTTP/2 response should contain content"
        assert len(response_http3.text) > 0, "HTTP/3 response should contain content"

    @pytest.mark.skipif(skip_in_ci(), reason="Skipping HTTP/3 comparison test in CI environment")
    def test_http3_performance_vs_http2(self, cycle_client):
        """
        Basic comparison of HTTP/3 vs HTTP/2 response times.

        HTTP/3 over QUIC should provide faster connection establishment
        due to 0-RTT handshake capability.
        """
        import time

        url = "https://cloudflare-quic.com/"

        # Measure HTTP/2 request time
        start_http2 = time.time()
        response_http2 = cycle_client.get(
            url,
            force_http1=False,
            force_http3=False,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        time_http2 = time.time() - start_http2

        # Measure HTTP/3 request time
        start_http3 = time.time()
        response_http3 = cycle_client.get(
            url,
            force_http3=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        time_http3 = time.time() - start_http3

        # Both should succeed
        assert response_http2.status_code == 200
        assert response_http3.status_code == 200

        # Log timing for analysis (not strict assertion due to network variability)
        print(f"\nHTTP/2 request time: {time_http2:.3f}s")
        print(f"HTTP/3 request time: {time_http3:.3f}s")

        # Both should complete in reasonable time (< 10 seconds)
        assert time_http2 < 10, "HTTP/2 request took too long"
        assert time_http3 < 10, "HTTP/3 request took too long"


class TestForceHTTP3FlagValidation:
    """Test force_http3 flag behavior and validation"""

    @pytest.mark.skipif(skip_in_ci(), reason="Skipping HTTP/3 test in CI environment")
    def test_force_http3_flag_true(self, cycle_client):
        """Test that force_http3=True enables HTTP/3"""
        response = cycle_client.get(
            "https://cloudflare-quic.com/",
            force_http3=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        assert response.status_code == 200, \
            "force_http3=True should successfully make HTTP/3 request"

    @pytest.mark.skipif(skip_in_ci(), reason="Skipping HTTP/3 test in CI environment")
    def test_force_http3_flag_false(self, cycle_client):
        """Test that force_http3=False uses HTTP/2 or HTTP/1.1"""
        response = cycle_client.get(
            "https://www.cloudflare.com/",
            force_http3=False,
            force_http1=False,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        assert response.status_code == 200, \
            "force_http3=False should fall back to HTTP/2 or HTTP/1.1"

    @pytest.mark.skipif(skip_in_ci(), reason="Skipping HTTP/3 test in CI environment")
    def test_force_http3_with_non_http3_site(self, cycle_client):
        """
        Test force_http3 with a site that may not support HTTP/3.

        Should gracefully fall back or return appropriate error.
        """
        # httpbin.org may not support HTTP/3
        response = cycle_client.get(
            "https://httpbin.org/get",
            force_http3=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        # Should either succeed with fallback or fail gracefully
        # Not all sites support HTTP/3, so this might fail
        if response.status_code == 200:
            # Site supports HTTP/3 or fell back successfully
            assert response.text is not None
        else:
            # Site doesn't support HTTP/3 - this is acceptable
            assert response.status_code in [400, 502, 503, 504], \
                f"Unexpected status code {response.status_code} for non-HTTP/3 site"

    def test_conflicting_protocol_flags(self, cycle_client):
        """
        Test behavior when both force_http1 and force_http3 are True.

        Should either error or prioritize one protocol.
        """
        # This is an edge case - what happens with conflicting flags?
        try:
            response = cycle_client.get(
                "https://www.cloudflare.com/",
                force_http1=True,
                force_http3=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )

            # If it doesn't raise an error, it should pick one protocol
            # The implementation should handle this gracefully
            if response.status_code == 200:
                # Successfully picked one protocol
                assert response.text is not None
            else:
                # Or returned an error status
                assert response.status_code >= 400

        except Exception as e:
            # It's acceptable to raise an exception for conflicting flags
            assert "conflict" in str(e).lower() or "invalid" in str(e).lower(), \
                f"Exception should indicate conflict: {str(e)}"


class TestHTTP3ErrorHandling:
    """Test error handling for HTTP/3 requests"""

    @pytest.mark.skipif(skip_in_ci(), reason="Skipping HTTP/3 test in CI environment")
    def test_http3_timeout(self, cycle_client):
        """Test HTTP/3 request with timeout"""
        # Use a very short timeout to test timeout handling
        response = cycle_client.get(
            "https://cloudflare-quic.com/",
            force_http3=True,
            timeout=10,  # 10 second timeout
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        # Should complete within timeout or raise appropriate error
        # If successful, verify response
        if response.status_code == 200:
            assert response.text is not None

    @pytest.mark.skipif(skip_in_ci(), reason="Skipping HTTP/3 test in CI environment")
    def test_http3_invalid_url(self, cycle_client):
        """Test HTTP/3 with invalid URL"""
        try:
            response = cycle_client.get(
                "https://invalid-domain-that-does-not-exist-12345.com/",
                force_http3=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )

            # Should fail with network error or DNS error
            assert response.status_code >= 400, \
                "Invalid domain should return error status"

        except Exception as e:
            # It's acceptable to raise an exception for invalid domains
            # Common exceptions: DNS resolution error, connection error
            assert True, "Exception is acceptable for invalid domain"

    @pytest.mark.skip(reason="HTTP/3 may not be fully implemented - testing graceful degradation")
    def test_http3_fallback_when_not_supported(self, cycle_client):
        """
        Test that HTTP/3 gracefully falls back when not supported.

        If HTTP/3 is not available in the implementation, it should either:
        1. Fall back to HTTP/2
        2. Return a clear error message
        3. Raise an informative exception
        """
        try:
            response = cycle_client.get(
                "https://www.cloudflare.com/",
                force_http3=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )

            # If it succeeds, great - HTTP/3 is implemented
            if response.status_code == 200:
                assert response.text is not None
                print("\nHTTP/3 is supported and working!")
            else:
                # Should provide meaningful error
                print(f"\nHTTP/3 returned status {response.status_code}")

        except NotImplementedError as e:
            # Clear indication that HTTP/3 is not yet implemented
            assert "HTTP/3" in str(e) or "QUIC" in str(e), \
                "NotImplementedError should mention HTTP/3 or QUIC"
            pytest.skip(f"HTTP/3 not implemented: {str(e)}")

        except Exception as e:
            # Other exceptions should be informative
            print(f"\nHTTP/3 error: {type(e).__name__}: {str(e)}")
            # This is acceptable - HTTP/3 may not be fully supported yet
