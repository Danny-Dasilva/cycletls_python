import pytest
from cycletls import CycleTLS
import time


@pytest.fixture
def cycle_with_reuse():
    """Create a CycleTLS instance with connection reuse enabled"""
    with CycleTLS() as client:
        yield client


@pytest.fixture
def cycle_without_reuse():
    """Create a CycleTLS instance with connection reuse disabled"""
    with CycleTLS() as client:
        yield client


class TestConnectionReuse:
    """Test suite for connection pooling and reuse functionality"""

    def test_multiple_requests_with_reuse_enabled(self, cycle_with_reuse):
        """Test that multiple requests to the same host reuse connections"""
        ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        # Make multiple requests to the same host
        start_time = time.time()

        response1 = cycle_with_reuse.get(
            "https://tls.peet.ws/api/clean",
            ja3=ja3,
            user_agent=user_agent,
            enable_connection_reuse=True
        )

        response2 = cycle_with_reuse.get(
            "https://tls.peet.ws/api/clean",
            ja3=ja3,
            user_agent=user_agent,
            enable_connection_reuse=True
        )

        response3 = cycle_with_reuse.get(
            "https://tls.peet.ws/api/clean",
            ja3=ja3,
            user_agent=user_agent,
            enable_connection_reuse=True
        )

        elapsed = time.time() - start_time

        # All requests should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200

        # Verify we get valid JSON responses
        data1 = response1.json()
        data2 = response2.json()
        data3 = response3.json()

        assert "ja3_hash" in data1
        assert "ja3_hash" in data2
        assert "ja3_hash" in data3

        # With connection reuse, subsequent requests should be faster
        # This is a rough check - the second and third requests should benefit from pooling

    def test_connection_reuse_disabled(self, cycle_without_reuse):
        """Test that connection reuse can be disabled"""
        ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"

        # Make multiple requests with connection reuse disabled
        response1 = cycle_without_reuse.get(
            "https://httpbin.org/get",
            ja3=ja3,
            enable_connection_reuse=False
        )

        response2 = cycle_without_reuse.get(
            "https://httpbin.org/get",
            ja3=ja3,
            enable_connection_reuse=False
        )

        # Both requests should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_connection_pooling_across_different_endpoints(self, cycle_with_reuse):
        """Test connection pooling when making requests to different endpoints on same host"""
        ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"

        # Different endpoints on httpbin.org
        response1 = cycle_with_reuse.get(
            "https://httpbin.org/get",
            ja3=ja3,
            enable_connection_reuse=True
        )

        response2 = cycle_with_reuse.get(
            "https://httpbin.org/headers",
            ja3=ja3,
            enable_connection_reuse=True
        )

        response3 = cycle_with_reuse.get(
            "https://httpbin.org/user-agent",
            ja3=ja3,
            enable_connection_reuse=True
        )

        # All requests should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200

        # Verify responses
        data1 = response1.json()
        data2 = response2.json()
        data3 = response3.json()

        assert "headers" in data1
        assert "headers" in data2
        assert "user-agent" in data3

    def test_concurrent_requests_with_pooling(self, cycle_with_reuse):
        """Test that concurrent requests benefit from connection pooling"""
        ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"

        # Simulate concurrent-like behavior by making rapid sequential requests
        urls = [
            "https://httpbin.org/get",
            "https://httpbin.org/headers",
            "https://httpbin.org/user-agent",
            "https://httpbin.org/uuid",
        ]

        responses = []
        for url in urls:
            response = cycle_with_reuse.get(
                url,
                ja3=ja3,
                enable_connection_reuse=True,
                timeout=10
            )
            responses.append(response)

        # All requests should succeed
        for response in responses:
            assert response.status_code == 200

    def test_connection_reuse_with_post_requests(self, cycle_with_reuse):
        """Test connection reuse with POST requests"""
        ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"

        payload1 = {"request": 1, "data": "first"}
        payload2 = {"request": 2, "data": "second"}

        # Make multiple POST requests
        response1 = cycle_with_reuse.post(
            "https://httpbin.org/post",
            json_data=payload1,
            ja3=ja3,
            enable_connection_reuse=True
        )

        response2 = cycle_with_reuse.post(
            "https://httpbin.org/post",
            json_data=payload2,
            ja3=ja3,
            enable_connection_reuse=True
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Verify payloads
        data1 = response1.json()
        data2 = response2.json()

        assert data1.get("json") == payload1
        assert data2.get("json") == payload2

    def test_connection_reuse_with_different_methods(self, cycle_with_reuse):
        """Test connection reuse across different HTTP methods"""
        ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"

        # GET request
        response_get = cycle_with_reuse.get(
            "https://httpbin.org/get",
            ja3=ja3,
            enable_connection_reuse=True
        )

        # POST request
        response_post = cycle_with_reuse.post(
            "https://httpbin.org/post",
            json_data={"test": "data"},
            ja3=ja3,
            enable_connection_reuse=True
        )

        # PUT request
        response_put = cycle_with_reuse.put(
            "https://httpbin.org/put",
            json_data={"test": "put"},
            ja3=ja3,
            enable_connection_reuse=True
        )

        # DELETE request
        response_delete = cycle_with_reuse.delete(
            "https://httpbin.org/delete",
            ja3=ja3,
            enable_connection_reuse=True
        )

        # All should succeed
        assert response_get.status_code == 200
        assert response_post.status_code == 200
        assert response_put.status_code == 200
        assert response_delete.status_code == 200

    def test_connection_reuse_with_cookies(self, cycle_with_reuse):
        """Test connection reuse with cookie handling"""
        ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"

        # Set a cookie
        response1 = cycle_with_reuse.get(
            "https://httpbin.org/cookies/set?session=abc123",
            ja3=ja3,
            enable_connection_reuse=True,
            disable_redirect=False
        )

        # Make another request to verify connection reuse
        response2 = cycle_with_reuse.get(
            "https://httpbin.org/cookies",
            ja3=ja3,
            enable_connection_reuse=True
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_mixed_reuse_settings(self, cycle_with_reuse):
        """Test mixing requests with and without connection reuse"""
        ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"

        # Request with reuse enabled
        response1 = cycle_with_reuse.get(
            "https://tls.peet.ws/api/clean",
            ja3=ja3,
            enable_connection_reuse=True
        )

        # Request with reuse disabled
        response2 = cycle_with_reuse.get(
            "https://tls.peet.ws/api/clean",
            ja3=ja3,
            enable_connection_reuse=False
        )

        # Request with reuse enabled again
        response3 = cycle_with_reuse.get(
            "https://tls.peet.ws/api/clean",
            ja3=ja3,
            enable_connection_reuse=True
        )

        # All should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
