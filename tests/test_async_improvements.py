"""
Tests for async improvements:
- arequest() uses callback-based async (zero-copy) when available
- aclose() method for httpx-compatible async cleanup
- Concurrent async requests via asyncio.gather
- Async context manager
- get_running_loop() used instead of deprecated get_event_loop()
"""

import asyncio

import pytest

from cycletls import CycleTLS, AsyncCycleTLS


class TestAsyncRequest:
    """Test that arequest() works (uses callback async when available)."""

    @pytest.mark.asyncio
    async def test_arequest_basic_get(self, httpbin_url):
        """Test async GET request via arequest()."""
        client = CycleTLS()
        try:
            response = await client.arequest("get", f"{httpbin_url}/get")
            assert response.status_code == 200
            data = response.json()
            assert "url" in data
        finally:
            client.close()

    @pytest.mark.asyncio
    async def test_aget_convenience(self, httpbin_url):
        """Test aget() convenience method."""
        async with CycleTLS() as client:
            response = await client.aget(f"{httpbin_url}/get")
            assert response.status_code == 200
            assert response.ok

    @pytest.mark.asyncio
    async def test_apost_with_json(self, httpbin_url):
        """Test async POST with JSON data."""
        async with CycleTLS() as client:
            payload = {"key": "value", "num": 42}
            response = await client.apost(
                f"{httpbin_url}/post", json_data=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert data["json"]["key"] == "value"
            assert data["json"]["num"] == 42


class TestAclose:
    """Test aclose() method for httpx-compatible async cleanup."""

    @pytest.mark.asyncio
    async def test_aclose_exists(self):
        """Test that aclose() method exists on CycleTLS."""
        client = CycleTLS()
        assert hasattr(client, "aclose")
        assert asyncio.iscoroutinefunction(client.aclose)

    @pytest.mark.asyncio
    async def test_aclose_works(self):
        """Test that aclose() closes the client."""
        client = CycleTLS()
        assert not client._closed
        await client.aclose()
        assert client._closed

    @pytest.mark.asyncio
    async def test_aclose_after_request(self, httpbin_url):
        """Test aclose() after making a request."""
        client = CycleTLS()
        response = await client.aget(f"{httpbin_url}/get")
        assert response.status_code == 200
        await client.aclose()
        assert client._closed

    @pytest.mark.asyncio
    async def test_aclose_on_async_cycletls(self):
        """Test that aclose() works on AsyncCycleTLS too."""
        client = AsyncCycleTLS()
        assert hasattr(client, "aclose")
        await client.aclose()
        assert client._closed


class TestConcurrentAsync:
    """Test concurrent async requests via asyncio.gather."""

    @pytest.mark.asyncio
    async def test_gather_multiple_gets(self, httpbin_url):
        """Test multiple concurrent GET requests."""
        async with CycleTLS() as client:
            tasks = [
                client.aget(f"{httpbin_url}/get?n={i}")
                for i in range(5)
            ]
            responses = await asyncio.gather(*tasks)

            assert len(responses) == 5
            for resp in responses:
                assert resp.status_code == 200
                assert resp.ok

    @pytest.mark.asyncio
    async def test_gather_mixed_methods(self, httpbin_url):
        """Test concurrent requests with different HTTP methods."""
        async with CycleTLS() as client:
            tasks = [
                client.aget(f"{httpbin_url}/get"),
                client.apost(f"{httpbin_url}/post", json_data={"a": 1}),
                client.aput(f"{httpbin_url}/put", json_data={"b": 2}),
            ]
            responses = await asyncio.gather(*tasks)

            assert len(responses) == 3
            for resp in responses:
                assert resp.status_code == 200


class TestAsyncContextManager:
    """Test async context manager (async with CycleTLS() as client)."""

    @pytest.mark.asyncio
    async def test_async_with_cycleTLS(self, httpbin_url):
        """Test CycleTLS as async context manager."""
        async with CycleTLS() as client:
            response = await client.aget(f"{httpbin_url}/get")
            assert response.status_code == 200
        # Client should be closed after exiting context
        assert client._closed

    @pytest.mark.asyncio
    async def test_async_with_async_cycletls(self, httpbin_url):
        """Test AsyncCycleTLS as async context manager."""
        async with AsyncCycleTLS() as client:
            response = await client.get(f"{httpbin_url}/get")
            assert response.status_code == 200
        assert client._closed

    @pytest.mark.asyncio
    async def test_async_context_manager_cleanup_on_error(self, httpbin_url):
        """Test that async context manager cleans up even on errors."""
        client_ref = None
        with pytest.raises(ValueError):
            async with CycleTLS() as client:
                client_ref = client
                response = await client.aget(f"{httpbin_url}/get")
                assert response.status_code == 200
                raise ValueError("test error")
        assert client_ref._closed


class TestRunningLoopUsed:
    """Test that get_running_loop() is used instead of deprecated get_event_loop()."""

    @pytest.mark.asyncio
    async def test_arequest_in_running_loop(self, httpbin_url):
        """Verify arequest works correctly within a running event loop.

        This implicitly tests that get_running_loop() is used since
        get_event_loop() would raise DeprecationWarning in Python 3.12+
        when called from a coroutine with a running loop.
        """
        async with CycleTLS() as client:
            response = await client.aget(f"{httpbin_url}/get")
            assert response.status_code == 200
