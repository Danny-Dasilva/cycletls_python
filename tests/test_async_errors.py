"""
Error handling tests for async CycleTLS.

Tests error scenarios including:
- HTTP error responses (4xx, 5xx)
- Timeout handling
- Exception propagation in async context
- Invalid request handling
"""

import pytest
import asyncio
import cycletls
from cycletls import AsyncCycleTLS
from cycletls.exceptions import HTTPError


class TestAsyncHTTPErrors:
    """Test async HTTP error responses."""

    @pytest.mark.asyncio
    async def test_async_404_error(self, httpbin_url):
        """Test async handling of 404 Not Found."""
        response = await cycletls.aget(f"{httpbin_url}/status/404")
        assert response.status_code == 404
        assert not response.ok
        assert response.is_error
        assert response.is_client_error
        assert not response.is_server_error

    @pytest.mark.asyncio
    async def test_async_500_error(self, httpbin_url):
        """Test async handling of 500 Internal Server Error."""
        response = await cycletls.aget(f"{httpbin_url}/status/500")
        assert response.status_code == 500
        assert not response.ok
        assert response.is_error
        assert not response.is_client_error
        assert response.is_server_error

    @pytest.mark.asyncio
    async def test_async_403_forbidden(self, httpbin_url):
        """Test async handling of 403 Forbidden."""
        response = await cycletls.aget(f"{httpbin_url}/status/403")
        assert response.status_code == 403
        assert not response.ok
        assert response.is_client_error

    @pytest.mark.asyncio
    async def test_async_401_unauthorized(self, httpbin_url):
        """Test async handling of 401 Unauthorized."""
        response = await cycletls.aget(f"{httpbin_url}/status/401")
        assert response.status_code == 401
        assert not response.ok
        assert response.is_client_error

    @pytest.mark.asyncio
    async def test_async_503_service_unavailable(self, httpbin_url):
        """Test async handling of 503 Service Unavailable."""
        response = await cycletls.aget(f"{httpbin_url}/status/503")
        assert response.status_code == 503
        assert not response.ok
        assert response.is_server_error

    @pytest.mark.asyncio
    async def test_async_raise_for_status_success(self, httpbin_url):
        """Test raise_for_status doesn't raise on success."""
        response = await cycletls.aget(f"{httpbin_url}/status/200")
        # Should not raise
        response.raise_for_status()

    @pytest.mark.asyncio
    async def test_async_raise_for_status_client_error(self, httpbin_url):
        """Test raise_for_status raises on client error."""
        response = await cycletls.aget(f"{httpbin_url}/status/404")
        with pytest.raises(HTTPError) as exc_info:
            response.raise_for_status()
        assert "404" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_async_raise_for_status_server_error(self, httpbin_url):
        """Test raise_for_status raises on server error."""
        response = await cycletls.aget(f"{httpbin_url}/status/500")
        with pytest.raises(HTTPError) as exc_info:
            response.raise_for_status()
        assert "500" in str(exc_info.value)


class TestAsyncTimeout:
    """Test async timeout handling."""

    @pytest.mark.asyncio
    async def test_async_request_timeout(self):
        """Test async request timeout."""
        # Request with 1 second timeout to endpoint that delays 10 seconds
        with pytest.raises((asyncio.TimeoutError, Exception)):
            await cycletls.aget(
                "https://httpbin.org/delay/10",
                timeout=1  # 1 second timeout
            )

    @pytest.mark.asyncio
    async def test_async_timeout_with_client(self):
        """Test async timeout using client."""
        async with AsyncCycleTLS() as client:
            with pytest.raises((asyncio.TimeoutError, Exception)):
                await client.get(
                    "https://httpbin.org/delay/10",
                    timeout=1
                )

    @pytest.mark.asyncio
    async def test_async_no_timeout_fast_request(self, httpbin_url):
        """Test that fast requests don't timeout."""
        # Should complete successfully
        response = await cycletls.aget(
            f"{httpbin_url}/get",
            timeout=5  # 5 second timeout
        )
        assert response.status_code == 200


class TestAsyncInvalidRequests:
    """Test async handling of invalid requests."""

    @pytest.mark.asyncio
    async def test_async_invalid_url(self):
        """Test async request to invalid URL."""
        with pytest.raises(Exception):
            await cycletls.aget("not-a-valid-url")

    @pytest.mark.asyncio
    async def test_async_nonexistent_domain(self):
        """Test async request to non-existent domain."""
        with pytest.raises(Exception):
            await cycletls.aget("https://this-domain-absolutely-does-not-exist-12345.com")

    @pytest.mark.asyncio
    async def test_async_connection_error(self):
        """Test async connection error handling."""
        # Try to connect to a port that's not listening
        with pytest.raises(Exception):
            await cycletls.aget("http://127.0.0.1:9999")


class TestAsyncExceptionPropagation:
    """Test exception propagation in async context."""

    @pytest.mark.asyncio
    async def test_async_exception_in_context_manager(self):
        """Test exception handling in async context manager."""
        try:
            async with AsyncCycleTLS() as client:
                # Make a successful request
                response = await client.get("https://httpbin.org/get")
                assert response.status_code == 200

                # Raise an exception
                raise ValueError("Test exception")
        except ValueError as e:
            assert str(e) == "Test exception"

    @pytest.mark.asyncio
    async def test_async_multiple_errors_in_gather(self, httpbin_url):
        """Test multiple errors when using gather."""
        tasks = [
            cycletls.aget("https://invalid-domain-12345.com"),
            cycletls.aget(f"{httpbin_url}/status/200"),
            cycletls.aget("https://another-invalid-domain-12345.com"),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        assert len(results) == 3
        assert isinstance(results[0], Exception)
        assert results[1].status_code == 200
        assert isinstance(results[2], Exception)


class TestAsyncRedirectErrors:
    """Test async redirect error handling."""

    @pytest.mark.asyncio
    async def test_async_redirect_success(self, httpbin_url):
        """Test async handling of successful redirects."""
        # httpbin redirects to the target URL
        response = await cycletls.aget(f"{httpbin_url}/redirect/3")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_async_redirect_chain(self, httpbin_url):
        """Test async handling of redirect chains."""
        # Multiple redirects
        response = await cycletls.aget(f"{httpbin_url}/absolute-redirect/5")
        assert response.status_code == 200


class TestAsyncErrorResponses:
    """Test async response error properties."""

    @pytest.mark.asyncio
    async def test_async_error_response_properties_404(self, httpbin_url):
        """Test error response properties for 404."""
        response = await cycletls.aget(f"{httpbin_url}/status/404")

        assert response.status_code == 404
        assert not response.ok
        assert response.is_error
        assert response.is_client_error
        assert not response.is_server_error
        assert not response.is_redirect

    @pytest.mark.asyncio
    async def test_async_error_response_properties_500(self, httpbin_url):
        """Test error response properties for 500."""
        response = await cycletls.aget(f"{httpbin_url}/status/500")

        assert response.status_code == 500
        assert not response.ok
        assert response.is_error
        assert not response.is_client_error
        assert response.is_server_error
        assert not response.is_redirect

    @pytest.mark.asyncio
    async def test_async_success_response_properties(self, httpbin_url):
        """Test success response properties."""
        response = await cycletls.aget(f"{httpbin_url}/status/200")

        assert response.status_code == 200
        assert response.ok
        assert not response.is_error
        assert not response.is_client_error
        assert not response.is_server_error


class TestAsyncConcurrentErrors:
    """Test error handling in concurrent async requests."""

    @pytest.mark.asyncio
    async def test_async_partial_failure_in_batch(self, httpbin_url):
        """Test handling partial failures in batch requests."""
        tasks = [
            cycletls.aget(f"{httpbin_url}/status/200"),
            cycletls.aget(f"{httpbin_url}/status/404"),
            cycletls.aget(f"{httpbin_url}/status/500"),
            cycletls.aget(f"{httpbin_url}/status/200"),
        ]

        responses = await asyncio.gather(*tasks)

        assert len(responses) == 4
        assert responses[0].status_code == 200
        assert responses[0].ok

        assert responses[1].status_code == 404
        assert not responses[1].ok

        assert responses[2].status_code == 500
        assert not responses[2].ok

        assert responses[3].status_code == 200
        assert responses[3].ok

    @pytest.mark.asyncio
    async def test_async_all_failures_in_batch(self, httpbin_url):
        """Test handling all failures in batch requests."""
        responses = await asyncio.gather(*[
            cycletls.aget(f"{httpbin_url}/status/404"),
            cycletls.aget(f"{httpbin_url}/status/500"),
            cycletls.aget(f"{httpbin_url}/status/503"),
        ])

        assert len(responses) == 3
        assert all(not r.ok for r in responses)
        assert responses[0].status_code == 404
        assert responses[1].status_code == 500
        assert responses[2].status_code == 503


class TestAsyncPollingTimeout:
    """Test async polling and timeout behavior."""

    @pytest.mark.asyncio
    async def test_async_custom_poll_interval_success(self, httpbin_url):
        """Test async request with custom poll interval succeeds."""
        async with AsyncCycleTLS() as client:
            response = await client.get(
                f"{httpbin_url}/get",
                poll_interval=0.01  # 10ms poll interval
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_async_adaptive_polling_success(self, httpbin_url):
        """Test async request with adaptive polling (default) succeeds."""
        async with AsyncCycleTLS() as client:
            response = await client.get(
                f"{httpbin_url}/get",
                poll_interval=0.0  # Adaptive polling
            )
            assert response.status_code == 200
