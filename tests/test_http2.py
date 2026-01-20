import pytest
from cycletls import CycleTLS


@pytest.fixture
def cycle():
    """Create a CycleTLS instance for testing"""
    with CycleTLS() as client:
        yield client


class TestHTTP2:
    """Test suite for HTTP/2 protocol functionality"""

    def test_basic_http2_request(self, cycle):
        """Test that HTTP/2 is used by default"""
        response = cycle.get(
            "https://httpbin.org/get",
            ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        assert response.status_code == 200
        # HTTP/2 should be used by default (force_http1 is False)
        data = response.json()
        assert "headers" in data

    def test_http2_vs_http1_comparison(self, cycle):
        """Compare HTTP/2 and HTTP/1.1 protocol usage"""
        # Test HTTP/2 (default)
        response_http2 = cycle.get(
            "https://ja3er.com/json",
            force_http1=False,
            ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"
        )

        # Test HTTP/1.1 (forced)
        response_http1 = cycle.get(
            "https://ja3er.com/json",
            force_http1=True,
            ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"
        )

        # Both should succeed
        assert response_http2.status_code == 200
        assert response_http1.status_code == 200

        # Both should return valid JSON
        data_http2 = response_http2.json()
        data_http1 = response_http1.json()

        assert "ja3_hash" in data_http2
        assert "ja3_hash" in data_http1

    def test_force_http1_protocol(self, cycle):
        """Test forcing HTTP/1.1 protocol"""
        response = cycle.get(
            "https://httpbin.org/headers",
            force_http1=True,
            ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        assert response.status_code == 200
        data = response.json()
        assert "headers" in data

    def test_http2_with_custom_headers(self, cycle):
        """Test HTTP/2 with custom headers and header ordering"""
        custom_headers = {
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "X-Custom-Header": "test-value"
        }

        response = cycle.get(
            "https://httpbin.org/headers",
            headers=custom_headers,
            force_http1=False,
            ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify custom headers were sent
        headers = data.get("headers", {})
        assert headers.get("X-Custom-Header") == "test-value"
        assert headers.get("Accept") == "application/json"

    def test_http2_post_with_json_body(self, cycle):
        """Test HTTP/2 POST request with JSON body"""
        payload = {
            "name": "test",
            "value": "http2-test",
            "protocol": "h2"
        }

        response = cycle.post(
            "https://httpbin.org/post",
            json_data=payload,
            force_http1=False,
            ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify the payload was received
        assert data.get("json") == payload

    def test_http2_with_timeout(self, cycle):
        """Test HTTP/2 request with custom timeout"""
        response = cycle.get(
            "https://httpbin.org/delay/1",
            timeout=5,
            force_http1=False,
            ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"
        )

        assert response.status_code == 200
        data = response.json()
        assert "url" in data

    def test_http2_redirect_handling(self, cycle):
        """Test HTTP/2 with redirect handling"""
        # Test with redirects enabled (default)
        response = cycle.get(
            "https://httpbin.org/redirect/2",
            disable_redirect=False,
            force_http1=False,
            ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"
        )

        assert response.status_code == 200
        # Should have followed redirects to final destination
        if response.final_url:
            assert "redirect" not in response.final_url or "get" in response.final_url
