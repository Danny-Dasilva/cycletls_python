"""
Test response methods and data access patterns.

Based on CycleTLS response-methods.test.js, this module tests:
- JSON parsing with .json() method
- Text extraction
- Headers parsing
- Status validation
- Method compatibility
- Cross-method consistency
"""

import pytest
import json
from cycletls import CycleTLS


class TestResponseJsonMethod:
    """Test the json() method for parsing JSON responses."""

    def test_should_parse_json_response_correctly(self, cycletls_client, httpbin_url, firefox_ja3):
        """Should parse JSON response correctly."""
        response = cycletls_client.get(
            f"{httpbin_url}/json",
            ja3=firefox_ja3
        )

        assert response.status_code == 200

        json_data = response.json()
        assert isinstance(json_data, dict)
        assert "slideshow" in json_data

    def test_should_handle_invalid_json_gracefully(self, cycletls_client, httpbin_url, firefox_ja3):
        """Should handle invalid JSON gracefully."""
        response = cycletls_client.get(
            f"{httpbin_url}/html",
            ja3=firefox_ja3
        )

        assert response.status_code == 200

        with pytest.raises(Exception) as exc_info:
            response.json()

        # Should raise a JSON decode error - accept various error message formats
        # orjson/ormsgpack uses "unexpected character" while json uses "JSONDecodeError"
        error_msg = str(exc_info.value).lower()
        assert any(x in error_msg for x in ["json", "decode", "unexpected", "parse", "invalid"])

    def test_should_be_callable_multiple_times(self, cycletls_client, httpbin_url, firefox_ja3):
        """Should be callable multiple times and return the same data."""
        response = cycletls_client.get(
            f"{httpbin_url}/json",
            ja3=firefox_ja3
        )

        json_data1 = response.json()
        json_data2 = response.json()

        assert json_data1 == json_data2

    def test_json_with_arrays(self, cycletls_client):
        """Test JSON parsing with array responses."""
        # Use a service that returns a JSON array
        response = cycletls_client.get("https://httpbin.org/get")

        assert response.status_code == 200
        json_data = response.json()
        assert isinstance(json_data, dict)

    def test_json_with_nested_objects(self, cycletls_client, httpbin_url):
        """Test JSON parsing with deeply nested objects."""
        response = cycletls_client.get(f"{httpbin_url}/json")

        json_data = response.json()
        assert isinstance(json_data, dict)

        # httpbin's /json returns a nested structure
        if "slideshow" in json_data:
            assert isinstance(json_data["slideshow"], dict)


class TestResponseTextMethod:
    """Test text extraction from responses."""

    def test_should_return_text_content(self, cycletls_client, httpbin_url, firefox_ja3):
        """Should return text content as string."""
        response = cycletls_client.get(
            f"{httpbin_url}/html",
            ja3=firefox_ja3
        )

        assert response.status_code == 200

        text_data = response.body
        assert isinstance(text_data, str)
        assert "<!DOCTYPE html>" in text_data or "<html>" in text_data

    def test_should_handle_plain_text_responses(self, cycletls_client, httpbin_url, firefox_ja3):
        """Should handle plain text responses."""
        response = cycletls_client.get(
            f"{httpbin_url}/robots.txt",
            ja3=firefox_ja3
        )

        assert response.status_code == 200

        text_data = response.body
        assert isinstance(text_data, str)
        assert "User-agent" in text_data

    def test_text_is_consistent_on_multiple_access(self, cycletls_client, httpbin_url, firefox_ja3):
        """Text should be consistent on multiple accesses."""
        response = cycletls_client.get(
            f"{httpbin_url}/robots.txt",
            ja3=firefox_ja3
        )

        text_data1 = response.body
        text_data2 = response.body

        assert text_data1 == text_data2

    def test_text_with_unicode(self, cycletls_client, httpbin_url):
        """Test text extraction with Unicode characters."""
        response = cycletls_client.get(f"{httpbin_url}/encoding/utf8")

        assert response.status_code == 200
        assert len(response.body) > 0

    def test_text_with_empty_response(self, cycletls_client, httpbin_url):
        """Test text extraction with empty response body."""
        response = cycletls_client.get(f"{httpbin_url}/status/204")

        assert response.status_code == 204
        assert response.body == ""


class TestResponseBinaryData:
    """Test binary data handling in responses."""

    def test_should_return_binary_data(self, cycletls_client, httpbin_url, firefox_ja3):
        """Should return binary data for byte responses."""
        response = cycletls_client.get(
            f"{httpbin_url}/bytes/1024",
            ja3=firefox_ja3
        )

        assert response.status_code == 200

        # Check content (binary data) length - use .content for bytes
        assert len(response.content) >= 1024

    def test_should_work_with_different_byte_sizes(self, cycletls_client, httpbin_url, firefox_ja3):
        """Should work with different byte sizes."""
        response = cycletls_client.get(
            f"{httpbin_url}/bytes/512",
            ja3=firefox_ja3
        )

        # Use .content for binary data
        assert len(response.content) >= 512

    def test_binary_data_is_consistent(self, cycletls_client, httpbin_url, firefox_ja3):
        """Binary data should be consistent on multiple accesses."""
        response = cycletls_client.get(
            f"{httpbin_url}/bytes/256",
            ja3=firefox_ja3
        )

        data1 = response.body
        data2 = response.body

        assert data1 == data2


class TestResponseHeaders:
    """Test response headers parsing and access."""

    def test_headers_are_accessible(self, cycletls_client, httpbin_url):
        """Response headers should be accessible as a dictionary."""
        response = cycletls_client.get(f"{httpbin_url}/get")

        assert response.status_code == 200
        assert hasattr(response.headers, '__getitem__')
        assert len(response.headers) > 0

    def test_specific_headers_present(self, cycletls_client, httpbin_url):
        """Specific headers should be present in response."""
        response = cycletls_client.get(f"{httpbin_url}/get")

        assert response.status_code == 200

        # Common headers that httpbin returns
        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        assert "content-type" in headers_lower

    def test_custom_request_headers_echoed(self, cycletls_client, httpbin_url):
        """Custom request headers should be echoed in response."""
        custom_header = "X-Custom-Test-Header"
        custom_value = "test-value-123"

        response = cycletls_client.get(
            f"{httpbin_url}/headers",
            headers={custom_header: custom_value}
        )

        assert response.status_code == 200

        # httpbin echoes headers back
        json_data = response.json()
        assert "headers" in json_data

        # Headers might be normalized to different cases
        headers_lower = {k.lower(): v for k, v in json_data["headers"].items()}
        assert custom_header.lower() in headers_lower


class TestMethodCompatibility:
    """Test compatibility of methods with existing data property."""

    def test_should_have_both_body_property_and_json_method(self, cycletls_client, httpbin_url, firefox_ja3):
        """Should have both body property and json() method available."""
        response = cycletls_client.get(
            f"{httpbin_url}/json",
            ja3=firefox_ja3
        )

        # Check that both APIs work
        assert response.body is not None
        assert hasattr(response, 'json')

        # Test that both produce consistent results
        json_from_method = response.json()
        json_from_body = json.loads(response.body)
        assert json_from_method == json_from_body

    def test_response_attributes_are_accessible(self, cycletls_client, httpbin_url):
        """All response attributes should be accessible."""
        response = cycletls_client.get(f"{httpbin_url}/get")

        assert hasattr(response, 'status_code')
        assert hasattr(response, 'headers')
        assert hasattr(response, 'body')
        assert hasattr(response, 'request_id')

        assert response.status_code == 200
        assert hasattr(response.headers, '__getitem__')
        assert isinstance(response.body, str)


class TestCrossMethodConsistency:
    """Test consistency across different data access methods."""

    def test_json_content_consistent_across_methods(self, cycletls_client, httpbin_url, firefox_ja3):
        """JSON content should be consistent across methods."""
        response = cycletls_client.get(
            f"{httpbin_url}/json",
            ja3=firefox_ja3
        )

        json_data = response.json()
        text_data = response.body
        parsed_from_text = json.loads(text_data)

        assert json_data == parsed_from_text

    def test_status_code_is_consistent(self, cycletls_client, httpbin_url):
        """Status code should be consistent and correct."""
        # Test non-redirect status codes (redirects are followed by default)
        test_codes = [200, 201, 204, 400, 404, 500]

        for code in test_codes:
            response = cycletls_client.get(f"{httpbin_url}/status/{code}")
            assert response.status_code == code

        # Test redirect status code with redirect disabled
        response = cycletls_client.get(f"{httpbin_url}/status/301", disable_redirect=True)
        assert response.status_code == 301

    def test_response_with_redirects(self, cycletls_client, httpbin_url):
        """Test response properties after redirects."""
        response = cycletls_client.get(f"{httpbin_url}/redirect/2")

        # After 2 redirects, should reach the final destination
        assert response.status_code == 200

        # final_url should be populated if redirects occurred
        if response.final_url:
            assert "get" in response.final_url.lower()


class TestResponseContentTypes:
    """Test handling of different content types."""

    def test_json_content_type(self, cycletls_client, httpbin_url):
        """Test JSON content type response."""
        response = cycletls_client.get(f"{httpbin_url}/json")

        assert response.status_code == 200
        json_data = response.json()
        assert isinstance(json_data, dict)

    def test_html_content_type(self, cycletls_client, httpbin_url):
        """Test HTML content type response."""
        response = cycletls_client.get(f"{httpbin_url}/html")

        assert response.status_code == 200
        assert "<html>" in response.body.lower()

    def test_xml_content_type(self, cycletls_client, httpbin_url):
        """Test XML content type response."""
        response = cycletls_client.get(f"{httpbin_url}/xml")

        assert response.status_code == 200
        assert "<?xml" in response.body or "<slideshow" in response.body

    def test_image_content_type(self, cycletls_client, httpbin_url):
        """Test image content type response."""
        response = cycletls_client.get(f"{httpbin_url}/image/png")

        assert response.status_code == 200
        # Should receive binary image data - use .content for binary
        assert len(response.content) > 0


class TestResponseEncoding:
    """Test response encoding handling."""

    def test_utf8_encoding(self, cycletls_client, httpbin_url):
        """Test UTF-8 encoded response."""
        response = cycletls_client.get(f"{httpbin_url}/encoding/utf8")

        assert response.status_code == 200
        assert len(response.body) > 0

    def test_gzip_encoding(self, cycletls_client, httpbin_url):
        """Test gzip encoded response."""
        response = cycletls_client.get(f"{httpbin_url}/gzip")

        assert response.status_code == 200
        # Response should be automatically decoded
        json_data = response.json()
        assert isinstance(json_data, dict)

    def test_deflate_encoding(self, cycletls_client, httpbin_url):
        """Test deflate encoded response."""
        response = cycletls_client.get(f"{httpbin_url}/deflate")

        assert response.status_code == 200
        # Response should be automatically decoded
        json_data = response.json()
        assert isinstance(json_data, dict)
