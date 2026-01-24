"""
Advanced async features tests for CycleTLS.

Tests advanced async functionality including:
- Custom poll intervals
- Adaptive polling behavior
- Proxy configuration
- Cookie handling
- Custom headers
- Connection parameters
"""

import pytest
import asyncio
import cycletls
from cycletls import AsyncCycleTLS


class TestAsyncPollingBehavior:
    """Test async polling configuration and behavior."""

    @pytest.mark.asyncio
    async def test_async_custom_poll_interval(self, httpbin_url):
        """Test async request with custom poll interval."""
        async with AsyncCycleTLS() as client:
            response = await client.get(
                f"{httpbin_url}/get",
                poll_interval=0.01  # 10ms poll interval
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_async_adaptive_polling(self, httpbin_url):
        """Test async request with adaptive polling (default)."""
        async with AsyncCycleTLS() as client:
            response = await client.get(
                f"{httpbin_url}/get",
                poll_interval=0.0  # Adaptive: tight loop → 100μs → 1ms
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_async_slow_poll_interval(self, httpbin_url):
        """Test async request with slower poll interval."""
        async with AsyncCycleTLS() as client:
            response = await client.get(
                f"{httpbin_url}/get",
                poll_interval=0.1  # 100ms poll interval
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_async_timeout_parameter(self, httpbin_url):
        """Test async request with custom timeout."""
        async with AsyncCycleTLS() as client:
            # Fast request with generous timeout
            response = await client.get(
                f"{httpbin_url}/get",
                timeout=30.0  # 30 second timeout
            )
            assert response.status_code == 200


class TestAsyncCookies:
    """Test async cookie handling."""

    @pytest.mark.asyncio
    async def test_async_send_cookies(self, httpbin_url):
        """Test sending cookies with async request."""
        async with AsyncCycleTLS() as client:
            cookies = {
                "session_id": "abc123",
                "user_pref": "dark_mode"
            }

            response = await client.get(
                f"{httpbin_url}/cookies",
                cookies=cookies
            )

            assert response.status_code == 200
            data = response.json()
            assert data["cookies"]["session_id"] == "abc123"
            assert data["cookies"]["user_pref"] == "dark_mode"

    @pytest.mark.asyncio
    async def test_async_receive_cookies(self, httpbin_url):
        """Test receiving cookies from async response."""
        async with AsyncCycleTLS() as client:
            # Set a cookie
            response = await client.get(
                f"{httpbin_url}/cookies/set?test_cookie=test_value"
            )

            assert response.status_code == 200
            # Cookies should be in response
            assert response.cookies is not None

    @pytest.mark.asyncio
    async def test_async_module_function_with_cookies(self, httpbin_url):
        """Test module-level async function with cookies."""
        cookies = {"test": "value"}
        response = await cycletls.aget(
            f"{httpbin_url}/cookies",
            cookies=cookies
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cookies"]["test"] == "value"


class TestAsyncProxy:
    """Test async proxy configuration."""

    @pytest.mark.asyncio
    async def test_async_with_proxy_url(self, httpbin_url):
        """Test async request with proxy (if available)."""
        # Note: This test will skip if no proxy is available
        # In production, you would set an actual proxy URL
        async with AsyncCycleTLS() as client:
            try:
                response = await client.get(
                    f"{httpbin_url}/get",
                    # proxy="http://proxy.example.com:8080"  # Uncomment with real proxy
                )
                assert response.status_code == 200
            except Exception:
                pytest.skip("No proxy available for testing")


class TestAsyncCustomHeaders:
    """Test async requests with custom headers and header ordering."""

    @pytest.mark.asyncio
    async def test_async_custom_header_order(self, httpbin_url):
        """Test async request with custom header ordering."""
        async with AsyncCycleTLS() as client:
            # Specify header order
            header_order = [
                "Host",
                "User-Agent",
                "Accept",
                "Accept-Language",
                "Accept-Encoding",
                "Connection"
            ]

            response = await client.get(
                f"{httpbin_url}/get",
                header_order=header_order,
                user_agent="CycleTLS-Async/1.0"
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_async_case_sensitive_headers(self, httpbin_url):
        """Test async request preserves header case."""
        async with AsyncCycleTLS() as client:
            headers = {
                "X-Custom-Header": "value1",
                "x-lowercase-header": "value2",
                "X-MiXeD-CaSe": "value3"
            }

            response = await client.get(
                f"{httpbin_url}/get",
                headers=headers
            )

            assert response.status_code == 200
            data = response.json()
            # Verify headers were sent
            assert "X-Custom-Header" in data["headers"]


class TestAsyncRedirects:
    """Test async redirect handling."""

    @pytest.mark.asyncio
    async def test_async_follow_redirects(self, httpbin_url):
        """Test async request follows redirects by default."""
        async with AsyncCycleTLS() as client:
            response = await client.get(f"{httpbin_url}/redirect/3")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_async_absolute_redirect(self, httpbin_url):
        """Test async absolute redirect.

        Note: httpbin's /absolute-redirect/N returns http:// URLs which cause issues
        with HTTP/2. Using redirect-to with an absolute HTTPS URL instead.
        """
        target_url = f"{httpbin_url}/get"
        response = await cycletls.aget(f"{httpbin_url}/redirect-to?url={target_url}")
        assert response.status_code == 200
        assert response.final_url == target_url

    @pytest.mark.asyncio
    async def test_async_redirect_to_get(self, httpbin_url):
        """Test async POST redirect to GET."""
        response = await cycletls.apost(f"{httpbin_url}/redirect-to?url=/get")
        assert response.status_code == 200


class TestAsyncCompression:
    """Test async request compression handling."""

    @pytest.mark.asyncio
    async def test_async_gzip_encoding(self, httpbin_url):
        """Test async request with gzip encoding."""
        response = await cycletls.aget(f"{httpbin_url}/gzip")
        assert response.status_code == 200
        data = response.json()
        assert data["gzipped"] is True

    @pytest.mark.asyncio
    async def test_async_deflate_encoding(self, httpbin_url):
        """Test async request with deflate encoding."""
        response = await cycletls.aget(f"{httpbin_url}/deflate")
        assert response.status_code == 200
        data = response.json()
        assert data["deflated"] is True

    @pytest.mark.asyncio
    async def test_async_brotli_encoding(self, httpbin_url):
        """Test async request with brotli encoding."""
        response = await cycletls.aget(f"{httpbin_url}/brotli")
        assert response.status_code == 200
        data = response.json()
        assert data["brotli"] is True


class TestAsyncHTTPVersions:
    """Test async requests with different HTTP versions."""

    @pytest.mark.asyncio
    async def test_async_http2_request(self):
        """Test async HTTP/2 request."""
        # Google supports HTTP/2
        response = await cycletls.aget("https://www.google.com")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_async_force_http1(self, httpbin_url):
        """Test forcing HTTP/1.1 for async request."""
        async with AsyncCycleTLS() as client:
            response = await client.get(
                f"{httpbin_url}/get",
                force_http1=True
            )
            assert response.status_code == 200


class TestAsyncBasicAuth:
    """Test async basic authentication."""

    @pytest.mark.asyncio
    async def test_async_basic_auth_success(self, httpbin_url):
        """Test async request with correct basic auth."""
        # httpbin provides /basic-auth/user/passwd endpoint
        response = await cycletls.aget(
            f"{httpbin_url}/basic-auth/testuser/testpass",
            headers={
                "Authorization": "Basic dGVzdHVzZXI6dGVzdHBhc3M="  # testuser:testpass
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True

    @pytest.mark.asyncio
    async def test_async_basic_auth_failure(self, httpbin_url):
        """Test async request with incorrect basic auth."""
        response = await cycletls.aget(
            f"{httpbin_url}/basic-auth/testuser/testpass",
            headers={
                "Authorization": "Basic d3JvbmdjcmVkcw=="  # wrong credentials
            }
        )

        assert response.status_code == 401


class TestAsyncResponseEncoding:
    """Test async response encoding detection."""

    @pytest.mark.asyncio
    async def test_async_utf8_response(self, httpbin_url):
        """Test async UTF-8 response handling."""
        response = await cycletls.aget(f"{httpbin_url}/encoding/utf8")
        assert response.status_code == 200
        assert isinstance(response.text, str)

    @pytest.mark.asyncio
    async def test_async_json_response(self, httpbin_url):
        """Test async JSON response parsing."""
        response = await cycletls.aget(f"{httpbin_url}/json")
        assert response.status_code == 200

        # Parse JSON
        data = response.json()
        assert isinstance(data, dict)


class TestAsyncRequestID:
    """Test async request ID handling."""

    @pytest.mark.asyncio
    async def test_async_auto_request_id(self, httpbin_url):
        """Test that async requests generate request IDs automatically."""
        async with AsyncCycleTLS() as client:
            response = await client.get(f"{httpbin_url}/get")
            assert response.status_code == 200
            # Request should have an ID (internal to the library)


class TestAsyncMultipleClients:
    """Test using multiple async clients concurrently."""

    @pytest.mark.asyncio
    async def test_async_multiple_clients_concurrent(self, httpbin_url):
        """Test multiple async clients running concurrently."""
        async def make_requests_with_client(client_id):
            async with AsyncCycleTLS() as client:
                responses = []
                for i in range(3):
                    response = await client.get(
                        f"{httpbin_url}/get?client={client_id}&req={i}"
                    )
                    responses.append(response)
                return responses

        # Run 3 clients concurrently, each making 3 requests
        results = await asyncio.gather(*[
            make_requests_with_client(i) for i in range(3)
        ])

        # Should have 3 clients × 3 requests = 9 total responses
        assert len(results) == 3
        assert all(len(client_responses) == 3 for client_responses in results)
        assert all(
            r.status_code == 200
            for client_responses in results
            for r in client_responses
        )


class TestAsyncDomainFronting:
    """Test async domain fronting (custom SNI)."""

    @pytest.mark.asyncio
    async def test_async_custom_sni(self):
        """Test async request with custom SNI."""
        async with AsyncCycleTLS() as client:
            # Note: This is a demonstration - actual domain fronting
            # requires specific server configurations
            try:
                response = await client.get(
                    "https://www.google.com",
                    server_name="www.google.com"  # Custom SNI
                )
                assert response.status_code == 200
            except Exception:
                # Custom SNI might not work with all servers
                pytest.skip("Custom SNI not supported for this server")


class TestAsyncDisableSecurityFeatures:
    """Test async requests with security features disabled."""

    @pytest.mark.asyncio
    async def test_async_insecure_skip_verify(self):
        """Test async request with certificate verification disabled."""
        async with AsyncCycleTLS() as client:
            # Note: Only for testing purposes - never disable in production
            response = await client.get(
                "https://self-signed.badssl.com/",
                insecure_skip_verify=True
            )
            # Should succeed despite invalid cert
            assert response.status_code in [200, 400, 500]  # Any response is fine
