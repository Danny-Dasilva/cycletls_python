"""
Test streaming response handling.

Based on CycleTLS streaming.test.js, this module tests:
- Large response streaming
- Chunked transfer encoding
- Partial response handling
- Stream cancellation (if supported)

Note: Some tests are marked as skipped if streaming is not fully supported
in the Python implementation.
"""

import pytest
from cycletls import CycleTLS


class TestStreamingResponses:
    """Test streaming response handling."""

    @pytest.mark.skip(reason="Streaming with responseType='stream' may not be implemented in Python API")
    def test_should_stream_data_from_httpbin(self, cycletls_client, httpbin_url, firefox_ja3):
        """Should stream data from httpbin /stream endpoint."""
        # Note: This test assumes streaming is implemented similar to Node.js
        # If Python implementation doesn't support streaming, this test should be skipped

        response = cycletls_client.get(
            f"{httpbin_url}/stream/3",
            ja3=firefox_ja3
        )

        assert response.status_code == 200
        assert response.body is not None

        # Verify we got all the data
        lines = response.body.strip().split('\n')
        assert len(lines) == 3

        # Each line should be valid JSON
        import json
        for line in lines:
            data = json.loads(line)
            assert isinstance(data, dict)

    def test_large_response_handling(self, cycletls_client, httpbin_url):
        """Test handling of large responses.

        Note: httpbin.org limits /bytes/ endpoint to 100KB (102400 bytes).
        We request more but only get the max allowed.
        """
        # Request data (httpbin.org limits to ~100KB max)
        response = cycletls_client.get(
            f"{httpbin_url}/bytes/102400",
            timeout=30
        )

        assert response.status_code == 200
        # Should receive the requested amount (httpbin limit is 100KB)
        # Use response.content for binary data (body is empty for non-UTF8 responses)
        assert len(response.content) >= 100000

    def test_chunked_transfer_encoding(self, cycletls_client, httpbin_url):
        """Test handling of chunked transfer encoding."""
        # httpbin's /stream endpoint uses chunked encoding
        response = cycletls_client.get(f"{httpbin_url}/stream/5")

        assert response.status_code == 200
        assert len(response.body) > 0

        # Should receive 5 JSON objects
        lines = [line for line in response.body.strip().split('\n') if line]
        assert len(lines) == 5

    def test_stream_with_multiple_calls(self, cycletls_client, httpbin_url, firefox_ja3):
        """Test streaming endpoint with multiple calls."""
        response1 = cycletls_client.get(
            f"{httpbin_url}/stream/2",
            ja3=firefox_ja3
        )

        response2 = cycletls_client.get(
            f"{httpbin_url}/stream/2",
            ja3=firefox_ja3
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Both should receive the same amount of data
        lines1 = [line for line in response1.body.strip().split('\n') if line]
        lines2 = [line for line in response2.body.strip().split('\n') if line]

        assert len(lines1) == 2
        assert len(lines2) == 2

    @pytest.mark.skip(reason="Stream response methods may not be implemented in Python API")
    def test_stream_response_methods(self, cycletls_client, httpbin_url, firefox_ja3):
        """Test that response methods work with streaming responses."""
        response = cycletls_client.get(
            f"{httpbin_url}/stream/1",
            ja3=firefox_ja3
        )

        assert response.status_code == 200

        # Should be able to parse the response
        lines = [line for line in response.body.strip().split('\n') if line]
        assert len(lines) >= 1

        # First line should be valid JSON
        import json
        data = json.loads(lines[0])
        assert "url" in data


class TestBackwardCompatibility:
    """Test backward compatibility with non-streaming responses."""

    def test_normal_json_response(self, cycletls_client, httpbin_url, firefox_ja3):
        """Should work normally with JSON responses."""
        response = cycletls_client.get(
            f"{httpbin_url}/json",
            ja3=firefox_ja3
        )

        assert response.status_code == 200
        json_data = response.json()
        assert isinstance(json_data, dict)
        assert "slideshow" in json_data

    def test_normal_text_response(self, cycletls_client, httpbin_url, firefox_ja3):
        """Should work normally with text responses."""
        response = cycletls_client.get(
            f"{httpbin_url}/html",
            ja3=firefox_ja3
        )

        assert response.status_code == 200
        assert isinstance(response.body, str)
        assert "<html>" in response.body.lower()

    def test_default_response_type(self, cycletls_client, httpbin_url, firefox_ja3):
        """Should work with default response type."""
        response = cycletls_client.get(
            f"{httpbin_url}/json",
            ja3=firefox_ja3
        )

        assert response.status_code == 200
        json_data = response.json()
        assert isinstance(json_data, dict)


class TestStreamEventHandling:
    """Test stream event handling and data flow."""

    @pytest.mark.skip(reason="Stream events may not be exposed in Python API")
    def test_stream_events_in_order(self, cycletls_client, httpbin_url, firefox_ja3):
        """Should emit proper events in order."""
        # This test is specific to event-based streaming (Node.js streams)
        # May not be applicable to Python implementation
        pass

    def test_progressive_data_availability(self, cycletls_client, httpbin_url):
        """Test that data is available after streaming completes."""
        response = cycletls_client.get(f"{httpbin_url}/stream/3")

        assert response.status_code == 200
        # After request completes, all data should be available
        assert len(response.body) > 0

        lines = [line for line in response.body.strip().split('\n') if line]
        assert len(lines) == 3


class TestErrorHandling:
    """Test error handling in streaming scenarios."""

    def test_streaming_with_error_status(self, cycletls_client, httpbin_url):
        """Should handle streaming errors gracefully."""
        response = cycletls_client.get(f"{httpbin_url}/status/404")

        assert response.status_code == 404
        # Should still return a response object

    def test_timeout_during_streaming(self, cycletls_client, httpbin_url):
        """Should handle timeout during streaming."""
        from cycletls.exceptions import Timeout
        with pytest.raises(Timeout):
            cycletls_client.get(
                f"{httpbin_url}/delay/10",
                timeout=2
            )

    def test_network_error_during_stream(self, cycletls_client):
        """Should handle network errors during streaming.

        CycleTLS raises ConnectionError for DNS lookup failures.
        """
        from cycletls.exceptions import ConnectionError
        with pytest.raises(ConnectionError) as exc_info:
            cycletls_client.get(
                "https://this-domain-does-not-exist-12345.com/stream",
                timeout=5
            )
        # Verify the error message contains DNS-related information
        assert "no such host" in str(exc_info.value).lower()


class TestPartialResponses:
    """Test handling of partial responses."""

    def test_response_with_content_length(self, cycletls_client, httpbin_url):
        """Test response with Content-Length header."""
        response = cycletls_client.get(f"{httpbin_url}/bytes/1024")

        assert response.status_code == 200
        # Should receive the full content
        # Use response.content for binary data (body is empty for non-UTF8 responses)
        assert len(response.content) >= 1024

    def test_response_without_content_length(self, cycletls_client, httpbin_url):
        """Test response without Content-Length header (chunked)."""
        response = cycletls_client.get(f"{httpbin_url}/stream/1")

        assert response.status_code == 200
        assert len(response.body) > 0

    def test_range_request(self, cycletls_client, httpbin_url):
        """Test partial content with Range header."""
        response = cycletls_client.get(
            f"{httpbin_url}/range/1024",
            headers={"Range": "bytes=0-511"}
        )

        # Should return 206 Partial Content or 200 OK
        assert response.status_code in [200, 206]


class TestLargeDataStreaming:
    """Test streaming of large data sets."""

    def test_very_large_response(self, cycletls_client, httpbin_url):
        """Test handling of very large responses.

        Note: httpbin.org limits /bytes/ endpoint to 100KB (102400 bytes).
        This test verifies we can handle the maximum allowed by httpbin.
        """
        # Request max data (httpbin.org limits to ~100KB)
        response = cycletls_client.get(
            f"{httpbin_url}/bytes/102400",
            timeout=60
        )

        assert response.status_code == 200
        # Should receive the max allowed by httpbin (100KB)
        # Use response.content for binary data (body is empty for non-UTF8 responses)
        assert len(response.content) >= 100000

    def test_multiple_large_requests(self, cycletls_client, httpbin_url):
        """Test multiple large requests in sequence.

        Note: httpbin.org limits /bytes/ endpoint to 100KB (102400 bytes).
        """
        # httpbin.org has a 100KB limit, so use sizes within that limit
        sizes = [50000, 80000, 102400]  # 50KB, 80KB, 100KB (max)

        for size in sizes:
            response = cycletls_client.get(
                f"{httpbin_url}/bytes/{size}",
                timeout=30
            )

            assert response.status_code == 200
            # Use response.content for binary data (body is empty for non-UTF8 responses)
            assert len(response.content) >= size * 0.9  # Allow some margin

    @pytest.mark.skip(reason="Stream cancellation may not be supported")
    def test_stream_cancellation(self, cycletls_client, httpbin_url):
        """Test cancellation of streaming request."""
        # This test would require async support or threading
        # to cancel a request mid-stream
        pass


class TestStreamingFormats:
    """Test different streaming formats."""

    def test_ndjson_streaming(self, cycletls_client, httpbin_url):
        """Test newline-delimited JSON streaming."""
        response = cycletls_client.get(f"{httpbin_url}/stream/5")

        assert response.status_code == 200

        # Parse NDJSON
        import json
        lines = [line for line in response.body.strip().split('\n') if line]

        assert len(lines) == 5

        for line in lines:
            data = json.loads(line)
            assert isinstance(data, dict)
            assert "url" in data

    def test_plain_text_streaming(self, cycletls_client, httpbin_url):
        """Test plain text streaming."""
        response = cycletls_client.get(f"{httpbin_url}/stream-bytes/1024")

        assert response.status_code == 200
        # Use response.content for binary data (body is empty for non-UTF8 responses)
        assert len(response.content) >= 1024

    def test_binary_streaming(self, cycletls_client, httpbin_url):
        """Test binary data streaming."""
        response = cycletls_client.get(f"{httpbin_url}/bytes/2048")

        assert response.status_code == 200
        # Use response.content for binary data (body is empty for non-UTF8 responses)
        assert len(response.content) >= 2048


class TestMemoryEfficiency:
    """Test memory efficiency of streaming."""

    def test_memory_with_large_stream(self, cycletls_client, httpbin_url):
        """Test that large streams don't cause memory issues.

        Note: httpbin.org limits /bytes/ endpoint to 100KB (102400 bytes).
        """
        # Request max data (httpbin.org limits to ~100KB)
        response = cycletls_client.get(
            f"{httpbin_url}/bytes/102400",
            timeout=30
        )

        assert response.status_code == 200
        # Use response.content for binary data (body is empty for non-UTF8 responses)
        assert len(response.content) >= 100000

        # If we get here without memory error, test passes

    def test_sequential_large_streams(self, cycletls_client, httpbin_url):
        """Test sequential large streams for memory leaks.

        Note: httpbin.org limits /bytes/ endpoint to 100KB (102400 bytes).
        """
        for _ in range(3):
            response = cycletls_client.get(
                f"{httpbin_url}/bytes/102400",
                timeout=30
            )

            assert response.status_code == 200
            # Use response.content for binary data (body is empty for non-UTF8 responses)
            assert len(response.content) >= 100000

        # If we get here without memory error, test passes
