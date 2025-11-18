"""
Basic async functionality tests for CycleTLS.

Tests core async operations including:
- Async GET/POST/PUT/PATCH/DELETE/HEAD/OPTIONS requests
- Module-level async functions (aget, apost, etc.)
- Async context manager lifecycle
- JSON/data/params handling
"""

import pytest
import cycletls
from cycletls import AsyncCycleTLS


class TestAsyncBasicMethods:
    """Test basic async HTTP methods."""

    @pytest.mark.asyncio
    async def test_async_get_request(self, httpbin_url):
        """Test async GET request."""
        async with AsyncCycleTLS() as client:
            response = await client.get(f"{httpbin_url}/get")
            assert response.status_code == 200
            assert response.ok
            data = response.json()
            assert "url" in data

    @pytest.mark.asyncio
    async def test_async_get_with_params(self, httpbin_url):
        """Test async GET request with query parameters."""
        async with AsyncCycleTLS() as client:
            params = {"foo": "bar", "test": "123"}
            response = await client.get(f"{httpbin_url}/get", params=params)
            assert response.status_code == 200
            data = response.json()
            assert data["args"]["foo"] == "bar"
            assert data["args"]["test"] == "123"

    @pytest.mark.asyncio
    async def test_async_post_json(self, httpbin_url):
        """Test async POST request with JSON data."""
        async with AsyncCycleTLS() as client:
            payload = {"key": "value", "number": 42}
            response = await client.post(
                f"{httpbin_url}/post",
                json_data=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert data["json"]["key"] == "value"
            assert data["json"]["number"] == 42

    @pytest.mark.asyncio
    async def test_async_post_data(self, httpbin_url):
        """Test async POST request with form data."""
        async with AsyncCycleTLS() as client:
            form_data = {"field1": "value1", "field2": "value2"}
            response = await client.post(
                f"{httpbin_url}/post",
                data=form_data
            )
            assert response.status_code == 200
            data = response.json()
            assert "field1=value1" in data["data"]
            assert "field2=value2" in data["data"]

    @pytest.mark.asyncio
    async def test_async_put_request(self, httpbin_url):
        """Test async PUT request."""
        async with AsyncCycleTLS() as client:
            payload = {"updated": "data"}
            response = await client.put(
                f"{httpbin_url}/put",
                json_data=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert data["json"]["updated"] == "data"

    @pytest.mark.asyncio
    async def test_async_patch_request(self, httpbin_url):
        """Test async PATCH request."""
        async with AsyncCycleTLS() as client:
            payload = {"patched": "field"}
            response = await client.patch(
                f"{httpbin_url}/patch",
                json_data=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert data["json"]["patched"] == "field"

    @pytest.mark.asyncio
    async def test_async_delete_request(self, httpbin_url):
        """Test async DELETE request."""
        async with AsyncCycleTLS() as client:
            response = await client.delete(f"{httpbin_url}/delete")
            assert response.status_code == 200
            data = response.json()
            assert "url" in data

    @pytest.mark.asyncio
    async def test_async_head_request(self, httpbin_url):
        """Test async HEAD request."""
        async with AsyncCycleTLS() as client:
            response = await client.head(f"{httpbin_url}/get")
            assert response.status_code == 200
            assert len(response.text) == 0  # HEAD has no body

    @pytest.mark.asyncio
    async def test_async_options_request(self, httpbin_url):
        """Test async OPTIONS request."""
        async with AsyncCycleTLS() as client:
            response = await client.options(f"{httpbin_url}/get")
            assert response.status_code == 200
            assert "Allow" in response.headers or "allow" in response.headers


class TestAsyncModuleFunctions:
    """Test module-level async convenience functions."""

    @pytest.mark.asyncio
    async def test_aget_function(self, httpbin_url):
        """Test module-level aget() function."""
        response = await cycletls.aget(f"{httpbin_url}/get")
        assert response.status_code == 200
        data = response.json()
        assert "url" in data

    @pytest.mark.asyncio
    async def test_aget_with_params(self, httpbin_url):
        """Test aget() with query parameters."""
        response = await cycletls.aget(
            f"{httpbin_url}/get",
            params={"test": "async"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["args"]["test"] == "async"

    @pytest.mark.asyncio
    async def test_apost_function(self, httpbin_url):
        """Test module-level apost() function."""
        response = await cycletls.apost(
            f"{httpbin_url}/post",
            json_data={"async": "post"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["json"]["async"] == "post"

    @pytest.mark.asyncio
    async def test_aput_function(self, httpbin_url):
        """Test module-level aput() function."""
        response = await cycletls.aput(
            f"{httpbin_url}/put",
            json_data={"async": "put"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["json"]["async"] == "put"

    @pytest.mark.asyncio
    async def test_apatch_function(self, httpbin_url):
        """Test module-level apatch() function."""
        response = await cycletls.apatch(
            f"{httpbin_url}/patch",
            json_data={"async": "patch"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["json"]["async"] == "patch"

    @pytest.mark.asyncio
    async def test_adelete_function(self, httpbin_url):
        """Test module-level adelete() function."""
        response = await cycletls.adelete(f"{httpbin_url}/delete")
        assert response.status_code == 200
        data = response.json()
        assert "url" in data

    @pytest.mark.asyncio
    async def test_ahead_function(self, httpbin_url):
        """Test module-level ahead() function."""
        response = await cycletls.ahead(f"{httpbin_url}/get")
        assert response.status_code == 200
        assert len(response.text) == 0

    @pytest.mark.asyncio
    async def test_aoptions_function(self, httpbin_url):
        """Test module-level aoptions() function."""
        response = await cycletls.aoptions(f"{httpbin_url}/get")
        assert response.status_code == 200


class TestAsyncContextManager:
    """Test async context manager lifecycle."""

    @pytest.mark.asyncio
    async def test_async_context_manager_basic(self, httpbin_url):
        """Test async context manager basic usage."""
        async with AsyncCycleTLS() as client:
            # Client should be usable inside context
            response = await client.get(f"{httpbin_url}/get")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_async_client_reuse(self, httpbin_url):
        """Test reusing async client for multiple requests."""
        async with AsyncCycleTLS() as client:
            response1 = await client.get(f"{httpbin_url}/get")
            response2 = await client.post(f"{httpbin_url}/post", json_data={})
            response3 = await client.put(f"{httpbin_url}/put", json_data={})

            assert response1.status_code == 200
            assert response2.status_code == 200
            assert response3.status_code == 200

    @pytest.mark.asyncio
    async def test_async_client_manual_close(self, httpbin_url):
        """Test manually closing async client."""
        client = AsyncCycleTLS()
        response = await client.get(f"{httpbin_url}/get")
        assert response.status_code == 200

        await client.close()


class TestAsyncHeaders:
    """Test async requests with custom headers."""

    @pytest.mark.asyncio
    async def test_async_custom_headers(self, httpbin_url):
        """Test async request with custom headers."""
        async with AsyncCycleTLS() as client:
            headers = {
                "X-Custom-Header": "test-value",
                "X-Another-Header": "another-value"
            }
            response = await client.get(
                f"{httpbin_url}/get",
                headers=headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["headers"]["X-Custom-Header"] == "test-value"
            assert data["headers"]["X-Another-Header"] == "another-value"

    @pytest.mark.asyncio
    async def test_async_user_agent(self, httpbin_url):
        """Test async request with custom user agent."""
        async with AsyncCycleTLS() as client:
            custom_ua = "CycleTLS-Async-Test/1.0"
            response = await client.get(
                f"{httpbin_url}/get",
                user_agent=custom_ua
            )
            assert response.status_code == 200
            data = response.json()
            assert data["headers"]["User-Agent"] == custom_ua


class TestAsyncResponseProperties:
    """Test async response object properties."""

    @pytest.mark.asyncio
    async def test_async_response_text(self, httpbin_url):
        """Test async response text property."""
        response = await cycletls.aget(f"{httpbin_url}/get")
        assert isinstance(response.text, str)
        assert len(response.text) > 0

    @pytest.mark.asyncio
    async def test_async_response_json(self, httpbin_url):
        """Test async response JSON parsing."""
        response = await cycletls.aget(f"{httpbin_url}/get")
        data = response.json()
        assert isinstance(data, dict)
        assert "url" in data

    @pytest.mark.asyncio
    async def test_async_response_headers(self, httpbin_url):
        """Test async response headers."""
        response = await cycletls.aget(f"{httpbin_url}/get")
        assert response.headers is not None
        assert isinstance(response.headers, dict)
        assert len(response.headers) > 0

    @pytest.mark.asyncio
    async def test_async_response_status_properties(self, httpbin_url):
        """Test async response status code properties."""
        response = await cycletls.aget(f"{httpbin_url}/get")
        assert response.status_code == 200
        assert response.ok
        assert not response.is_error
        assert not response.is_client_error
        assert not response.is_server_error
