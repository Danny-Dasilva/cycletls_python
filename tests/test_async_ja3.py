"""
TLS fingerprinting tests for async CycleTLS.

Tests TLS fingerprinting with async requests including:
- JA3 fingerprint spoofing
- JA4R fingerprint spoofing
- Browser profile emulation
- Fingerprint verification
"""

import pytest
import cycletls
from cycletls import AsyncCycleTLS


class TestAsyncJA3Fingerprints:
    """Test async requests with JA3 fingerprints."""

    @pytest.mark.asyncio
    async def test_async_chrome_ja3(self, chrome_ja3):
        """Test async request with Chrome JA3 fingerprint."""
        async with AsyncCycleTLS() as client:
            response = await client.get(
                "https://tls.peet.ws/api/clean",
                ja3=chrome_ja3,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            assert response.status_code == 200
            data = response.json()

            # Verify JA3 fingerprint was applied
            assert "ja3_hash" in data or "ja3n_hash" in data

    @pytest.mark.asyncio
    async def test_async_firefox_ja3(self, firefox_ja3):
        """Test async request with Firefox JA3 fingerprint."""
        async with AsyncCycleTLS() as client:
            response = await client.get(
                "https://tls.peet.ws/api/clean",
                ja3=firefox_ja3,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
            )

            assert response.status_code == 200
            data = response.json()
            assert "ja3_hash" in data or "ja3n_hash" in data

    @pytest.mark.asyncio
    async def test_async_safari_ja3(self, safari_ja3):
        """Test async request with Safari JA3 fingerprint."""
        async with AsyncCycleTLS() as client:
            response = await client.get(
                "https://tls.peet.ws/api/clean",
                ja3=safari_ja3,
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
            )

            assert response.status_code == 200
            data = response.json()
            assert "ja3_hash" in data or "ja3n_hash" in data

    @pytest.mark.asyncio
    async def test_async_module_function_with_ja3(self, chrome_ja3):
        """Test module-level async function with JA3."""
        response = await cycletls.aget(
            "https://tls.peet.ws/api/clean",
            ja3=chrome_ja3,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        assert response.status_code == 200
        data = response.json()
        assert "ja3_hash" in data or "ja3n_hash" in data


class TestAsyncConcurrentJA3:
    """Test concurrent async requests with different JA3 fingerprints."""

    @pytest.mark.asyncio
    async def test_async_concurrent_different_fingerprints(self, chrome_ja3, firefox_ja3, safari_ja3):
        """Test concurrent requests with different browser fingerprints."""
        import asyncio

        # Different JA3 fingerprints require separate connections
        tasks = [
            cycletls.aget(
                "https://tls.peet.ws/api/clean",
                ja3=chrome_ja3,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                enable_connection_reuse=False,
            ),
            cycletls.aget(
                "https://tls.peet.ws/api/clean",
                ja3=firefox_ja3,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
                enable_connection_reuse=False,
            ),
            cycletls.aget(
                "https://tls.peet.ws/api/clean",
                ja3=safari_ja3,
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
                enable_connection_reuse=False,
            ),
        ]

        responses = await asyncio.gather(*tasks)

        assert len(responses) == 3
        assert all(r.status_code == 200 for r in responses)

        # Verify all responses contain JA3 data
        for response in responses:
            data = response.json()
            assert "ja3_hash" in data or "ja3n_hash" in data

    @pytest.mark.asyncio
    async def test_async_same_fingerprint_concurrent(self, chrome_ja3):
        """Test multiple concurrent requests with same fingerprint."""
        import asyncio

        num_requests = 5
        # Same JA3 fingerprint - connection reuse should work but disable for test isolation
        tasks = [
            cycletls.aget(
                "https://tls.peet.ws/api/clean",
                ja3=chrome_ja3,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                enable_connection_reuse=False,
            )
            for _ in range(num_requests)
        ]

        responses = await asyncio.gather(*tasks)

        assert len(responses) == num_requests
        assert all(r.status_code == 200 for r in responses)


class TestAsyncJA4Fingerprints:
    """Test async requests with JA4R fingerprints."""

    @pytest.mark.asyncio
    async def test_async_chrome_ja4r(self):
        """Test async request with Chrome JA4R fingerprint."""
        async with AsyncCycleTLS() as client:
            # Chrome JA4R fingerprint
            ja4r = "t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,4469_0403,0804,0401,0503,0805,0501,0806,0601"

            response = await client.get(
                "https://tls.peet.ws/api/all",
                ja4r=ja4r,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_async_module_function_with_ja4r(self):
        """Test module-level async function with JA4R."""
        ja4r = "t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,4469_0403,0804,0401,0503,0805,0501,0806,0601"

        response = await cycletls.aget(
            "https://tls.peet.ws/api/all",
            ja4r=ja4r,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            enable_connection_reuse=False,
        )

        assert response.status_code == 200


class TestAsyncHTTP2Fingerprint:
    """Test async requests with HTTP/2 fingerprints."""

    @pytest.mark.asyncio
    async def test_async_http2_fingerprint(self):
        """Test async request with HTTP/2 fingerprint string."""
        async with AsyncCycleTLS() as client:
            # Chrome HTTP/2 fingerprint string format:
            # SETTINGS|WINDOW_UPDATE|PRIORITY|Header Order
            http2_fingerprint = "1:65536,2:0,3:1000,4:6291456,6:262144|15663105|0|m,a,s,p"

            response = await client.get(
                "https://www.google.com",
                http2_fingerprint=http2_fingerprint,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                enable_connection_reuse=False,
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_async_http2_fingerprint_concurrent(self):
        """Test concurrent async requests with HTTP/2 fingerprints."""
        import asyncio

        # Chrome HTTP/2 fingerprint string
        http2_fingerprint = "1:65536,2:0,3:1000,4:6291456,6:262144|15663105|0|m,a,s,p"

        tasks = [
            cycletls.aget(
                "https://www.google.com",
                http2_fingerprint=http2_fingerprint,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                enable_connection_reuse=False,
            )
            for _ in range(3)
        ]

        responses = await asyncio.gather(*tasks)

        assert len(responses) == 3
        assert all(r.status_code == 200 for r in responses)


class TestAsyncBrowserProfiles:
    """Test async requests with complete browser profiles."""

    @pytest.mark.asyncio
    async def test_async_chrome_profile(self, chrome_ja3):
        """Test async request with complete Chrome profile."""
        async with AsyncCycleTLS() as client:
            response = await client.get(
                "https://tls.peet.ws/api/clean",
                ja3=chrome_ja3,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    "Sec-Ch-Ua-Mobile": "?0",
                    "Sec-Ch-Ua-Platform": '"Windows"',
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Upgrade-Insecure-Requests": "1",
                },
                enable_connection_reuse=False,
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_async_firefox_profile(self, firefox_ja3):
        """Test async request with complete Firefox profile."""
        async with AsyncCycleTLS() as client:
            response = await client.get(
                "https://tls.peet.ws/api/clean",
                ja3=firefox_ja3,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Upgrade-Insecure-Requests": "1",
                },
                enable_connection_reuse=False,
            )

            assert response.status_code == 200


class TestAsyncFingerprintPersistence:
    """Test fingerprint persistence across multiple requests."""

    @pytest.mark.asyncio
    async def test_async_fingerprint_reuse(self, chrome_ja3):
        """Test using same fingerprint for multiple async requests."""
        async with AsyncCycleTLS() as client:
            # Multiple requests with same fingerprint - connection reuse disabled for test isolation
            response1 = await client.get(
                "https://tls.peet.ws/api/clean",
                ja3=chrome_ja3,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                enable_connection_reuse=False,
            )

            response2 = await client.get(
                "https://tls.peet.ws/api/clean",
                ja3=chrome_ja3,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                enable_connection_reuse=False,
            )

            assert response1.status_code == 200
            assert response2.status_code == 200

    @pytest.mark.asyncio
    async def test_async_fingerprint_switch(self, chrome_ja3, firefox_ja3):
        """Test switching fingerprints between async requests."""
        async with AsyncCycleTLS() as client:
            # Request with Chrome fingerprint - switching fingerprints requires new connections
            response1 = await client.get(
                "https://tls.peet.ws/api/clean",
                ja3=chrome_ja3,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                enable_connection_reuse=False,
            )

            # Switch to Firefox fingerprint
            response2 = await client.get(
                "https://tls.peet.ws/api/clean",
                ja3=firefox_ja3,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
                enable_connection_reuse=False,
            )

            assert response1.status_code == 200
            assert response2.status_code == 200
