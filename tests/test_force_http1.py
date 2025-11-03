"""
Tests for force_http1 functionality.
Based on CycleTLS/tests/forceHTTP1.test.ts
"""

import pytest
from cycletls import CycleTLS


@pytest.fixture
def client():
    """Create a CycleTLS client instance"""
    cycle = CycleTLS()
    yield cycle
    cycle.close()


@pytest.fixture
def chrome_ja3():
    """Chrome 83 JA3 fingerprint"""
    return "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"


@pytest.fixture
def chrome_user_agent():
    """Chrome 83 User Agent"""
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36"


def test_http2_by_default(client, chrome_ja3, chrome_user_agent):
    """Test that HTTP/2 is used by default when server supports it"""
    url = "https://tls.peet.ws/api/all"

    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        force_http1=False
    )

    assert result.status_code == 200
    data = result.json()

    # Check that HTTP/2 was used
    assert "http_version" in data
    assert data["http_version"] == "h2" or data["http_version"] == "HTTP/2.0"


def test_force_http1_on_http2_server(client, chrome_ja3, chrome_user_agent):
    """Test that HTTP/1.1 is forced when force_http1 is True"""
    url = "https://tls.peet.ws/api/all"

    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        force_http1=True
    )

    assert result.status_code == 200
    data = result.json()

    # Check that HTTP/1.1 was used
    assert "http_version" in data
    assert data["http_version"] == "HTTP/1.1"


def test_http1_with_httpbin(client, chrome_ja3, chrome_user_agent):
    """Test force_http1 with httpbin.org"""
    url = "https://httpbin.org/get"

    # First verify default behavior (should use HTTP/2 if available)
    result_default = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        force_http1=False
    )
    assert result_default.status_code == 200

    # Then force HTTP/1.1
    result_http1 = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        force_http1=True
    )
    assert result_http1.status_code == 200

    # Both requests should succeed
    assert result_default.json() is not None
    assert result_http1.json() is not None


def test_http1_with_post_request(client, chrome_ja3, chrome_user_agent):
    """Test that force_http1 works with POST requests"""
    url = "https://httpbin.org/post"

    result = client.post(
        url,
        body='{"test": "data"}',
        headers={"Content-Type": "application/json"},
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        force_http1=True
    )

    assert result.status_code == 200
    data = result.json()
    assert "json" in data
    assert data["json"]["test"] == "data"


def test_http1_with_headers(client, chrome_ja3, chrome_user_agent):
    """Test that custom headers work correctly with force_http1"""
    url = "https://httpbin.org/headers"

    custom_headers = {
        "X-Custom-Header": "test-value",
        "X-Another-Header": "another-value"
    }

    result = client.get(
        url,
        headers=custom_headers,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        force_http1=True
    )

    assert result.status_code == 200
    data = result.json()
    assert "headers" in data
    assert data["headers"]["X-Custom-Header"] == "test-value"
    assert data["headers"]["X-Another-Header"] == "another-value"


def test_http1_with_query_parameters(client, chrome_ja3, chrome_user_agent):
    """Test that query parameters work correctly with force_http1"""
    url = "https://httpbin.org/get?param1=value1&param2=value2"

    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        force_http1=True
    )

    assert result.status_code == 200
    data = result.json()
    assert "args" in data
    assert data["args"]["param1"] == "value1"
    assert data["args"]["param2"] == "value2"


def test_http1_with_cookies(client, chrome_ja3, chrome_user_agent):
    """Test that cookies work correctly with force_http1"""
    url = "https://httpbin.org/cookies"

    # Set cookies using the cookies/set endpoint first
    set_url = "https://httpbin.org/cookies/set?test_cookie=test_value"
    client.get(
        set_url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        force_http1=True
    )

    # Now check cookies
    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        force_http1=True
    )

    assert result.status_code == 200


def test_http1_with_redirects(client, chrome_ja3, chrome_user_agent):
    """Test that redirects work correctly with force_http1"""
    url = "https://httpbin.org/redirect/2"

    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        force_http1=True
    )

    # Should follow redirects and succeed
    assert result.status_code == 200
    assert "url" in result.json()


def test_http1_no_redirect_follow(client, chrome_ja3, chrome_user_agent):
    """Test that redirect following can be disabled with force_http1"""
    url = "https://httpbin.org/redirect/1"

    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        force_http1=True,
        disable_redirect=True
    )

    # Should return redirect status code
    assert result.status_code in [301, 302, 303, 307, 308]


def test_http1_with_compression(client, chrome_ja3, chrome_user_agent):
    """Test that compression works correctly with force_http1"""
    url = "https://httpbin.org/gzip"

    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        force_http1=True
    )

    assert result.status_code == 200
    data = result.json()
    assert "gzipped" in data
    assert data["gzipped"] is True


def test_http1_performance_comparison(client, chrome_ja3, chrome_user_agent):
    """Compare response times between HTTP/1.1 and HTTP/2"""
    import time

    url = "https://httpbin.org/get"

    # Test HTTP/2
    start_http2 = time.time()
    result_http2 = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        force_http1=False
    )
    time_http2 = time.time() - start_http2

    # Test HTTP/1.1
    start_http1 = time.time()
    result_http1 = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        force_http1=True
    )
    time_http1 = time.time() - start_http1

    # Both should succeed
    assert result_http2.status_code == 200
    assert result_http1.status_code == 200

    # Times should be reasonable (within 10 seconds)
    assert time_http2 < 10
    assert time_http1 < 10


@pytest.mark.parametrize("method,url", [
    ("GET", "https://httpbin.org/get"),
    ("POST", "https://httpbin.org/post"),
    ("PUT", "https://httpbin.org/put"),
    ("DELETE", "https://httpbin.org/delete"),
    ("PATCH", "https://httpbin.org/patch"),
])
def test_http1_with_various_methods(client, chrome_ja3, chrome_user_agent, method, url):
    """Test that force_http1 works with various HTTP methods"""
    if method == "GET":
        result = client.get(url, ja3=chrome_ja3, user_agent=chrome_user_agent, force_http1=True)
    elif method == "POST":
        result = client.post(url, body='{"test": "data"}', ja3=chrome_ja3, user_agent=chrome_user_agent, force_http1=True)
    elif method == "PUT":
        result = client.put(url, body='{"test": "data"}', ja3=chrome_ja3, user_agent=chrome_user_agent, force_http1=True)
    elif method == "DELETE":
        result = client.delete(url, ja3=chrome_ja3, user_agent=chrome_user_agent, force_http1=True)
    elif method == "PATCH":
        result = client.patch(url, body='{"test": "data"}', ja3=chrome_ja3, user_agent=chrome_user_agent, force_http1=True)

    assert result.status_code == 200
