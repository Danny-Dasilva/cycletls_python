"""Tests for the unified CycleTLS client (sync + async in one class)."""

import pytest
from unittest.mock import patch, MagicMock


# Mock response data that the FFI layer would return
MOCK_RESPONSE = {
    "RequestID": "test",
    "Status": 200,
    "Body": '{"ok": true}',
    "Headers": {"Content-Type": "application/json"},
    "FinalUrl": "https://example.com",
    "Cookies": [],
}


class TestUnifiedClassStructure:
    """Verify CycleTLS has both sync and async methods."""

    def test_has_sync_methods(self):
        from cycletls import CycleTLS
        client = CycleTLS()
        assert callable(client.get)
        assert callable(client.post)
        assert callable(client.put)
        assert callable(client.patch)
        assert callable(client.delete)
        assert callable(client.head)
        assert callable(client.options)
        assert callable(client.request)
        assert callable(client.batch)
        client.close()

    def test_has_async_methods(self):
        from cycletls import CycleTLS
        client = CycleTLS()
        assert callable(client.aget)
        assert callable(client.apost)
        assert callable(client.aput)
        assert callable(client.apatch)
        assert callable(client.adelete)
        assert callable(client.ahead)
        assert callable(client.aoptions)
        assert callable(client.arequest)
        assert callable(client.abatch)
        client.close()

    def test_has_both_context_managers(self):
        from cycletls import CycleTLS
        client = CycleTLS()
        # Sync context manager
        assert hasattr(client, '__enter__')
        assert hasattr(client, '__exit__')
        # Async context manager
        assert hasattr(client, '__aenter__')
        assert hasattr(client, '__aexit__')
        client.close()


class TestSyncContextManager:
    @patch('cycletls.api.ffi_send_request', return_value=MOCK_RESPONSE)
    def test_sync_with_statement(self, mock_ffi):
        from cycletls import CycleTLS
        with CycleTLS() as client:
            response = client.get("https://example.com")
            assert response.status_code == 200

    @patch('cycletls.api.ffi_send_request', return_value=MOCK_RESPONSE)
    def test_client_closed_after_exit(self, mock_ffi):
        from cycletls import CycleTLS
        client = CycleTLS()
        with client:
            pass
        assert client._closed is True


class TestAsyncContextManager:
    @pytest.mark.asyncio
    @patch('cycletls.api.ffi_send_request_async', return_value=MOCK_RESPONSE)
    async def test_async_with_statement(self, mock_ffi):
        from cycletls import CycleTLS
        async with CycleTLS() as client:
            response = await client.aget("https://example.com")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_client_closed_after_async_exit(self):
        from cycletls import CycleTLS
        client = CycleTLS()
        async with client:
            pass
        assert client._closed is True


class TestAsyncMethods:
    @pytest.mark.asyncio
    @patch('cycletls.api.ffi_send_request_async', return_value=MOCK_RESPONSE)
    async def test_aget(self, mock_ffi):
        from cycletls import CycleTLS
        async with CycleTLS() as client:
            response = await client.aget("https://example.com")
            assert response.status_code == 200

    @pytest.mark.asyncio
    @patch('cycletls.api.ffi_send_request_async', return_value=MOCK_RESPONSE)
    async def test_apost(self, mock_ffi):
        from cycletls import CycleTLS
        async with CycleTLS() as client:
            response = await client.apost("https://example.com", json_data={"key": "value"})
            assert response.status_code == 200

    @pytest.mark.asyncio
    @patch('cycletls.api.ffi_send_request_async', return_value=MOCK_RESPONSE)
    async def test_arequest_with_fingerprint(self, mock_ffi):
        """Verify fingerprint parameter works in async (was missing before unification)."""
        from cycletls import CycleTLS
        async with CycleTLS() as client:
            response = await client.aget("https://example.com", fingerprint="chrome_120")
            assert response.status_code == 200


class TestBackwardCompatibility:
    @pytest.mark.asyncio
    @patch('cycletls.api.ffi_send_request_async', return_value=MOCK_RESPONSE)
    async def test_async_cycletls_import(self, mock_ffi):
        """AsyncCycleTLS should still be importable and work."""
        from cycletls import AsyncCycleTLS
        async with AsyncCycleTLS() as client:
            response = await client.get("https://example.com")
            assert response.status_code == 200

    @pytest.mark.asyncio
    @patch('cycletls.api.ffi_send_request_async', return_value=MOCK_RESPONSE)
    async def test_async_cycletls_from_async_api(self, mock_ffi):
        """Import from async_api module should still work."""
        from cycletls.async_api import AsyncCycleTLS
        async with AsyncCycleTLS() as client:
            response = await client.get("https://example.com")
            assert response.status_code == 200

    def test_async_cycletls_is_subclass(self):
        from cycletls import CycleTLS, AsyncCycleTLS
        assert issubclass(AsyncCycleTLS, CycleTLS)


class TestPrepareRequest:
    """Test that _prepare_request is used internally."""

    @patch('cycletls.api.ffi_send_request', return_value=MOCK_RESPONSE)
    def test_prepare_request_exists(self, mock_ffi):
        from cycletls import CycleTLS
        client = CycleTLS()
        assert callable(client._prepare_request)
        client.close()

    @patch('cycletls.api.ffi_send_request', return_value=MOCK_RESPONSE)
    def test_sync_uses_prepare_request(self, mock_ffi):
        from cycletls import CycleTLS
        with CycleTLS() as client:
            with patch.object(client, '_prepare_request', wraps=client._prepare_request) as mock_prep:
                client.get("https://example.com")
                mock_prep.assert_called_once()
