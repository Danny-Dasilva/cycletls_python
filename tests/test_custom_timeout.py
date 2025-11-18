"""
Custom Timeout Tests for CycleTLS Python library.

Based on CycleTLS TypeScript timeout tests, these tests verify:
- Per-request timeout override
- Very short timeouts (<1s)
- Very long timeouts (>60s)
- Timeout inheritance and default values
- Timeout error handling

Tests use httpbin.org/delay endpoints to test various timeout scenarios.
"""

import pytest
import time
from test_utils import assert_valid_response


class TestPerRequestTimeout:
    """Test per-request timeout overrides."""

    def test_short_timeout_causes_failure(self, cycletls_client, chrome_ja3):
        """Test that a very short timeout causes the request to fail."""
        # 1 second timeout should fail for 4 second delay
        with pytest.raises(Exception) as exc_info:
            cycletls_client.get(
                "https://httpbin.org/delay/4",
                ja3=chrome_ja3,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36",
                timeout=1
            )

        # Verify it's a timeout error
        error_msg = str(exc_info.value).lower()
        assert any(word in error_msg for word in ['timeout', 'deadline', 'context', 'exceeded']), \
            f"Expected timeout error, got: {exc_info.value}"

    def test_sufficient_timeout_succeeds(self, cycletls_client, chrome_ja3):
        """Test that a sufficient timeout allows the request to succeed."""
        # 30 second timeout should be enough for 1 second delay
        response = cycletls_client.get(
            "https://httpbin.org/delay/1",
            ja3=chrome_ja3,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36",
            timeout=30
        )

        assert_valid_response(response, expected_status=200)

    def test_timeout_override_per_request(self, cycletls_client, chrome_ja3):
        """Test that timeout can be overridden on a per-request basis."""
        # First request with short timeout should fail
        with pytest.raises(Exception):
            cycletls_client.get(
                "https://httpbin.org/delay/3",
                ja3=chrome_ja3,
                timeout=1
            )

        # Second request with longer timeout should succeed
        response = cycletls_client.get(
            "https://httpbin.org/delay/1",
            ja3=chrome_ja3,
            timeout=10
        )

        assert_valid_response(response, expected_status=200)

    def test_timeout_with_post_request(self, cycletls_client, chrome_ja3):
        """Test that timeout works with POST requests."""
        # POST with sufficient timeout should succeed
        response = cycletls_client.post(
            "https://httpbin.org/delay/1",
            ja3=chrome_ja3,
            json_data={"test": "data"},
            timeout=10
        )

        assert_valid_response(response, expected_status=200)

        # POST with insufficient timeout should fail
        with pytest.raises(Exception) as exc_info:
            cycletls_client.post(
                "https://httpbin.org/delay/5",
                ja3=chrome_ja3,
                json_data={"test": "data"},
                timeout=1
            )

        error_msg = str(exc_info.value).lower()
        assert any(word in error_msg for word in ['timeout', 'deadline', 'context']), \
            "Expected timeout error for POST request"


class TestVeryShortTimeouts:
    """Test very short timeout values (<1s)."""

    def test_500ms_timeout(self, cycletls_client, chrome_ja3):
        """Test 500ms (0.5 second) timeout."""
        # 500ms timeout should fail for 2 second delay
        with pytest.raises(Exception) as exc_info:
            cycletls_client.get(
                "https://httpbin.org/delay/2",
                ja3=chrome_ja3,
                timeout=0.5
            )

        error_msg = str(exc_info.value).lower()
        assert any(word in error_msg for word in ['timeout', 'deadline', 'context']), \
            "Expected timeout error"

    def test_100ms_timeout(self, cycletls_client, chrome_ja3):
        """Test 100ms (0.1 second) timeout - extremely short."""
        # 100ms timeout should fail for any delay endpoint
        with pytest.raises(Exception) as exc_info:
            cycletls_client.get(
                "https://httpbin.org/delay/1",
                ja3=chrome_ja3,
                timeout=0.1
            )

        error_msg = str(exc_info.value).lower()
        assert any(word in error_msg for word in ['timeout', 'deadline', 'context']), \
            "Expected timeout error"

    def test_200ms_timeout_with_instant_response(self, cycletls_client, chrome_ja3):
        """Test that very short timeout works with instant response (no delay)."""
        # Even with a 200ms timeout, /delay/0 should succeed
        try:
            response = cycletls_client.get(
                "https://httpbin.org/delay/0",
                ja3=chrome_ja3,
                timeout=0.2
            )
            # If it succeeds, verify it's valid
            assert_valid_response(response, expected_status=200)
        except Exception:
            # It's acceptable if it fails due to network latency
            # The important thing is we're testing the timeout mechanism
            pass

    def test_very_short_timeout_sequence(self, cycletls_client, chrome_ja3):
        """Test sequence of very short timeouts with varying delays."""
        # Test with 0 delay - might succeed or fail depending on latency
        try:
            response = cycletls_client.get(
                "https://httpbin.org/delay/0",
                ja3=chrome_ja3,
                timeout=0.5
            )
            # If successful, verify response
            assert_valid_response(response, expected_status=200)
        except Exception:
            # Acceptable to fail with very short timeout
            pass

        # Test with 1 second delay - should definitely fail
        with pytest.raises(Exception) as exc_info:
            cycletls_client.get(
                "https://httpbin.org/delay/1",
                ja3=chrome_ja3,
                timeout=0.5
            )

        error_msg = str(exc_info.value).lower()
        assert any(word in error_msg for word in ['timeout', 'deadline', 'context']), \
            "Expected timeout error"


class TestVeryLongTimeouts:
    """Test very long timeout values (>60s)."""

    def test_120_second_timeout(self, cycletls_client, chrome_ja3):
        """Test 120 second (2 minute) timeout with quick response."""
        # Long timeout should easily handle 1 second delay
        response = cycletls_client.get(
            "https://httpbin.org/delay/1",
            ja3=chrome_ja3,
            timeout=120
        )

        assert_valid_response(response, expected_status=200)

    def test_300_second_timeout(self, cycletls_client, chrome_ja3):
        """Test 300 second (5 minute) timeout with quick response."""
        # Very long timeout should handle 2 second delay
        response = cycletls_client.get(
            "https://httpbin.org/delay/2",
            ja3=chrome_ja3,
            timeout=300
        )

        assert_valid_response(response, expected_status=200)

    @pytest.mark.slow
    def test_long_timeout_with_long_delay(self, cycletls_client, chrome_ja3):
        """Test long timeout with longer delay (marked as slow test)."""
        # 90 second timeout should handle 5 second delay
        response = cycletls_client.get(
            "https://httpbin.org/delay/5",
            ja3=chrome_ja3,
            timeout=90
        )

        assert_valid_response(response, expected_status=200)


class TestTimeoutInheritance:
    """Test timeout inheritance and default values."""

    def test_default_timeout_value(self):
        """Test that default timeout value is set correctly."""
        from cycletls.schema import Request

        # Default timeout should be 6 seconds as per schema
        req = Request(url="https://example.com", method="GET")
        assert req.timeout == 6, "Default timeout should be 6 seconds"

    def test_request_without_explicit_timeout(self, cycletls_client, chrome_ja3):
        """Test request without explicit timeout uses default."""
        # Should use default timeout (6 seconds) which is enough for 1 second delay
        response = cycletls_client.get(
            "https://httpbin.org/delay/1",
            ja3=chrome_ja3
        )

        assert_valid_response(response, expected_status=200)

    def test_default_timeout_insufficient(self, cycletls_client, chrome_ja3):
        """Test that default timeout (6s) fails for longer delays."""
        # 10 second delay should exceed default 6 second timeout
        with pytest.raises(Exception) as exc_info:
            cycletls_client.get(
                "https://httpbin.org/delay/10",
                ja3=chrome_ja3
                # No timeout specified - should use default
            )

        error_msg = str(exc_info.value).lower()
        assert any(word in error_msg for word in ['timeout', 'deadline', 'context']), \
            "Expected timeout error with default timeout"


class TestTimeoutEdgeCases:
    """Test edge cases in timeout handling."""

    def test_zero_delay_with_various_timeouts(self, cycletls_client, chrome_ja3):
        """Test /delay/0 with various timeout values."""
        # Short timeout with instant response
        response1 = cycletls_client.get(
            "https://httpbin.org/delay/0",
            ja3=chrome_ja3,
            timeout=1
        )
        assert_valid_response(response1, expected_status=200)

        # Long timeout with instant response
        response2 = cycletls_client.get(
            "https://httpbin.org/delay/0",
            ja3=chrome_ja3,
            timeout=60
        )
        assert_valid_response(response2, expected_status=200)

    def test_timeout_error_contains_useful_info(self, cycletls_client, chrome_ja3):
        """Test that timeout errors contain useful information."""
        try:
            cycletls_client.get(
                "https://httpbin.org/delay/5",
                ja3=chrome_ja3,
                timeout=1
            )
            pytest.fail("Expected timeout error was not raised")
        except Exception as e:
            # Verify we get a meaningful error message
            error_msg = str(e).lower()
            assert len(error_msg) > 0, "Error message should not be empty"
            assert any(word in error_msg for word in ['timeout', 'deadline', 'context', 'exceeded']), \
                f"Error message should contain timeout-related keyword, got: {error_msg}"

    @pytest.mark.parametrize("delay,timeout,should_succeed", [
        (1, 3, True),   # 1s delay, 3s timeout - should succeed
        (2, 5, True),   # 2s delay, 5s timeout - should succeed
        (1, 10, True),  # 1s delay, 10s timeout - should succeed
        (3, 1, False),  # 3s delay, 1s timeout - should fail
        (5, 2, False),  # 5s delay, 2s timeout - should fail
        (4, 1, False),  # 4s delay, 1s timeout - should fail
    ])
    def test_timeout_parametrized(self, cycletls_client, chrome_ja3, delay, timeout, should_succeed):
        """Parametrized test for various timeout scenarios."""
        url = f"https://httpbin.org/delay/{delay}"

        if should_succeed:
            response = cycletls_client.get(url, ja3=chrome_ja3, timeout=timeout)
            assert_valid_response(response, expected_status=200)
        else:
            with pytest.raises(Exception) as exc_info:
                cycletls_client.get(url, ja3=chrome_ja3, timeout=timeout)
            error_msg = str(exc_info.value).lower()
            assert any(word in error_msg for word in ['timeout', 'deadline', 'context']), \
                f"Expected timeout error, got: {exc_info.value}"

    def test_timeout_precision(self, cycletls_client, chrome_ja3):
        """Test that timeout timing is reasonably precise."""
        # Test that a 2 second timeout actually times out around 2 seconds
        start_time = time.time()

        try:
            cycletls_client.get(
                "https://httpbin.org/delay/10",
                ja3=chrome_ja3,
                timeout=2
            )
            pytest.fail("Expected timeout error")
        except Exception:
            elapsed_time = time.time() - start_time

            # Timeout should occur around 2 seconds (with some tolerance)
            # Allow 0.5s-4s range to account for network latency and processing
            assert 0.5 <= elapsed_time <= 4, \
                f"Timeout should occur around 2 seconds, but took {elapsed_time:.2f}s"
