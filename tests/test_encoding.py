"""
Tests for encoding/compression functionality.
Based on CycleTLS/tests/encoding.test.ts
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


def test_gzip_decompression(client, chrome_ja3, chrome_user_agent):
    """Test that gzip-compressed responses are properly decompressed"""
    url = "https://httpbin.org/gzip"

    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        headers={"Accept-Encoding": "gzip, deflate, br"}
    )

    assert result.status_code == 200

    # Response should be automatically decompressed and parseable as JSON
    data = result.json()
    assert "gzipped" in data
    assert data["gzipped"] is True
    assert "method" in data
    assert data["method"] == "GET"
    assert "headers" in data


def test_deflate_decompression(client, chrome_ja3, chrome_user_agent):
    """Test that deflate-compressed responses are properly decompressed"""
    url = "https://httpbin.org/deflate"

    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        headers={"Accept-Encoding": "gzip, deflate, br"}
    )

    assert result.status_code == 200

    # Response should be automatically decompressed and parseable as JSON
    data = result.json()
    assert "deflated" in data
    assert data["deflated"] is True
    assert "method" in data
    assert data["method"] == "GET"
    assert "headers" in data


def test_brotli_decompression(client, chrome_ja3, chrome_user_agent):
    """Test that brotli-compressed responses are properly decompressed"""
    url = "https://httpbin.org/brotli"

    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        headers={"Accept-Encoding": "gzip, deflate, br"}
    )

    assert result.status_code == 200

    # Response should be automatically decompressed and parseable as JSON
    data = result.json()
    assert "brotli" in data
    assert data["brotli"] is True
    assert "method" in data
    assert data["method"] == "GET"
    assert "headers" in data


def test_gzip_response_headers(client, chrome_ja3, chrome_user_agent):
    """Test that gzip response contains correct headers"""
    url = "https://httpbin.org/gzip"

    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        headers={"Accept-Encoding": "gzip, deflate, br"}
    )

    assert result.status_code == 200
    data = result.json()

    # Verify Accept-Encoding header was sent
    assert "headers" in data
    headers = data["headers"]
    assert "Accept-Encoding" in headers
    assert "gzip" in headers["Accept-Encoding"].lower()


def test_deflate_response_headers(client, chrome_ja3, chrome_user_agent):
    """Test that deflate response contains correct headers"""
    url = "https://httpbin.org/deflate"

    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        headers={"Accept-Encoding": "gzip, deflate, br"}
    )

    assert result.status_code == 200
    data = result.json()

    # Verify Accept-Encoding header was sent
    assert "headers" in data
    headers = data["headers"]
    assert "Accept-Encoding" in headers
    assert "deflate" in headers["Accept-Encoding"].lower()


def test_brotli_response_headers(client, chrome_ja3, chrome_user_agent):
    """Test that brotli response contains correct headers"""
    url = "https://httpbin.org/brotli"

    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        headers={"Accept-Encoding": "gzip, deflate, br"}
    )

    assert result.status_code == 200
    data = result.json()

    # Verify Accept-Encoding header was sent
    assert "headers" in data
    headers = data["headers"]
    assert "Accept-Encoding" in headers
    assert "br" in headers["Accept-Encoding"].lower()


def test_multiple_encodings_support(client, chrome_ja3, chrome_user_agent):
    """Test that client can handle multiple encoding types"""
    urls = [
        "https://httpbin.org/gzip",
        "https://httpbin.org/deflate",
        "https://httpbin.org/brotli"
    ]

    for url in urls:
        result = client.get(
            url,
            ja3=chrome_ja3,
            user_agent=chrome_user_agent,
            headers={"Accept-Encoding": "gzip, deflate, br"}
        )

        assert result.status_code == 200
        data = result.json()
        assert "method" in data
        assert data["method"] == "GET"


def test_no_encoding_header(client, chrome_ja3, chrome_user_agent):
    """Test request without Accept-Encoding header"""
    url = "https://httpbin.org/get"

    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent
    )

    assert result.status_code == 200
    data = result.json()
    assert "url" in data


def test_gzip_with_post_request(client, chrome_ja3, chrome_user_agent):
    """Test that encoding works with POST requests"""
    url = "https://httpbin.org/post"

    result = client.post(
        url,
        body='{"test": "data", "encoding": "test"}',
        headers={
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip, deflate, br"
        },
        ja3=chrome_ja3,
        user_agent=chrome_user_agent
    )

    assert result.status_code == 200
    data = result.json()
    assert "json" in data
    assert data["json"]["test"] == "data"
    assert data["json"]["encoding"] == "test"


def test_encoding_with_large_response(client, chrome_ja3, chrome_user_agent):
    """Test encoding with large response body"""
    # Request a large amount of data
    url = "https://httpbin.org/bytes/10000"

    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        headers={"Accept-Encoding": "gzip, deflate, br"}
    )

    assert result.status_code == 200
    # Should receive 10000 bytes of data
    assert len(result.content) == 10000


def test_gzip_text_response(client, chrome_ja3, chrome_user_agent):
    """Test that gzip-compressed text responses are readable"""
    url = "https://httpbin.org/gzip"

    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        headers={"Accept-Encoding": "gzip, deflate, br"}
    )

    assert result.status_code == 200
    # Text should be decompressed and readable
    text = result.text
    assert len(text) > 0
    assert isinstance(text, str)


def test_deflate_text_response(client, chrome_ja3, chrome_user_agent):
    """Test that deflate-compressed text responses are readable"""
    url = "https://httpbin.org/deflate"

    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        headers={"Accept-Encoding": "gzip, deflate, br"}
    )

    assert result.status_code == 200
    # Text should be decompressed and readable
    text = result.text
    assert len(text) > 0
    assert isinstance(text, str)


def test_brotli_text_response(client, chrome_ja3, chrome_user_agent):
    """Test that brotli-compressed text responses are readable"""
    url = "https://httpbin.org/brotli"

    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        headers={"Accept-Encoding": "gzip, deflate, br"}
    )

    assert result.status_code == 200
    # Text should be decompressed and readable
    text = result.text
    assert len(text) > 0
    assert isinstance(text, str)


def test_encoding_with_redirects(client, chrome_ja3, chrome_user_agent):
    """Test that encoding works correctly with redirects"""
    # This will redirect and the final response should still be decompressed
    url = "https://httpbin.org/redirect-to?url=https://httpbin.org/gzip"

    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        headers={"Accept-Encoding": "gzip, deflate, br"}
    )

    assert result.status_code == 200
    data = result.json()
    assert "gzipped" in data


def test_selective_encoding_gzip_only(client, chrome_ja3, chrome_user_agent):
    """Test requesting only gzip encoding"""
    url = "https://httpbin.org/gzip"

    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        headers={"Accept-Encoding": "gzip"}
    )

    assert result.status_code == 200
    data = result.json()
    assert "gzipped" in data
    assert "headers" in data
    assert data["headers"]["Accept-Encoding"] == "gzip"


def test_selective_encoding_brotli_only(client, chrome_ja3, chrome_user_agent):
    """Test requesting only brotli encoding"""
    url = "https://httpbin.org/brotli"

    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        headers={"Accept-Encoding": "br"}
    )

    assert result.status_code == 200
    data = result.json()
    assert "brotli" in data
    assert "headers" in data
    assert data["headers"]["Accept-Encoding"] == "br"


@pytest.mark.parametrize("url,encoding_key", [
    ("https://httpbin.org/gzip", "gzipped"),
    ("https://httpbin.org/deflate", "deflated"),
    ("https://httpbin.org/brotli", "brotli"),
])
def test_encodings_parametrized(client, chrome_ja3, chrome_user_agent, url, encoding_key):
    """Parametrized test for various encoding types"""
    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        headers={"Accept-Encoding": "gzip, deflate, br"}
    )

    assert result.status_code == 200

    # Response should be decompressed and parseable
    data = result.json()
    assert encoding_key in data
    assert data[encoding_key] is True
    assert "method" in data
    assert data["method"] == "GET"
    assert "headers" in data
    assert "Accept-Encoding" in data["headers"]


def test_encoding_content_length(client, chrome_ja3, chrome_user_agent):
    """Test that decompressed content has appropriate length"""
    url = "https://httpbin.org/gzip"

    result = client.get(
        url,
        ja3=chrome_ja3,
        user_agent=chrome_user_agent,
        headers={"Accept-Encoding": "gzip, deflate, br"}
    )

    assert result.status_code == 200

    # Content should exist and have reasonable length
    assert len(result.content) > 0
    assert len(result.text) > 0

    # JSON should be parseable, indicating proper decompression
    data = result.json()
    assert isinstance(data, dict)
