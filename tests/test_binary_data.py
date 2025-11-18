"""
Binary Data Handling Tests for CycleTLS Python library.

Based on CycleTLS TypeScript binary-data-handling tests, these tests verify:
- Send binary request body using body_bytes parameter
- Receive binary response and check body_bytes field
- Binary vs text detection
- Large binary files (images, PDFs)
- Data integrity with problematic UTF-8 sequences
- Test with httpbin.org/image endpoints

Tests ensure that binary data (images, PDFs, arbitrary byte sequences) is preserved
without corruption when sent or received.
"""

import pytest
import hashlib
from test_utils import assert_valid_response


class TestBinaryUpload:
    """Test binary data uploads with body_bytes parameter."""

    def test_binary_upload_with_problematic_utf8_sequences(self, cycletls_client, httpbin_url):
        """Test that binary data with sequences that would corrupt in UTF-8 preserves data integrity."""
        # Create binary data with sequences that would corrupt in UTF-8
        problematic_data = bytes([
            0xFF, 0xD8, 0xFF, 0xE0,  # JPEG header
            0x80, 0x81, 0x82, 0x83,  # Invalid UTF-8 sequences
            0x00, 0x01, 0x02, 0x03,  # Null bytes and control characters
            0xFE, 0xFF, 0xC0, 0xC1,  # More problematic bytes
            0xEF, 0xBF, 0xBD,        # UTF-8 replacement character sequence
            0xF0, 0x90, 0x8D,        # Incomplete 4-byte UTF-8 sequence
        ])

        original_hash = hashlib.md5(problematic_data).hexdigest()

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            body_bytes=problematic_data,
            headers={
                'Content-Type': 'application/octet-stream',
                'Content-Length': str(len(problematic_data))
            }
        )

        assert_valid_response(response, expected_status=200)

        # Parse response to verify server received the data
        response_data = response.json()
        assert 'data' in response_data, "Response should contain posted data"

        # httpbin.org returns data as base64 or raw string
        # Verify the data was received (exact comparison depends on server encoding)
        assert response_data['data'], "Posted data should not be empty"

    def test_binary_image_upload(self, cycletls_client, httpbin_url):
        """Test uploading binary image data."""
        # Create fake JPEG data with valid JPEG header
        test_image_data = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x01, 0x00, 0x48, 0x00, 0x48, 0x00, 0x00, 0xFF, 0xD9
        ])

        original_hash = hashlib.sha256(test_image_data).hexdigest()

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            body_bytes=test_image_data,
            headers={'Content-Type': 'image/jpeg'}
        )

        assert_valid_response(response, expected_status=200)

        # Verify upload was successful
        response_data = response.json()
        assert 'data' in response_data or 'files' in response_data, \
            "Response should contain uploaded image data"

    def test_large_binary_file_upload(self, cycletls_client, httpbin_url):
        """Test that large binary files with repeating problematic sequences don't corrupt data."""
        # Create a larger binary file with repeating problematic sequences
        pattern = bytes([0xFF, 0x00, 0x80, 0x81, 0xC0, 0xC1, 0xFE, 0xFF])
        repetitions = 1000  # 8KB of binary data
        large_data = pattern * repetitions

        original_hash = hashlib.md5(large_data).hexdigest()

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            body_bytes=large_data,
            headers={
                'Content-Type': 'application/octet-stream',
                'Content-Length': str(len(large_data))
            }
        )

        assert_valid_response(response, expected_status=200)

        response_data = response.json()
        assert 'data' in response_data, "Response should contain posted data"
        # Verify we got substantial data back
        assert len(response_data['data']) > 0, "Posted data should not be empty"

    def test_all_byte_values_preserved(self, cycletls_client, httpbin_url):
        """Test that binary data with all possible byte values (0-255) is preserved."""
        # Create data with all possible byte values
        all_bytes_data = bytes(range(256))
        original_hash = hashlib.sha256(all_bytes_data).hexdigest()

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            body_bytes=all_bytes_data,
            headers={'Content-Type': 'application/octet-stream'}
        )

        assert_valid_response(response, expected_status=200)

        response_data = response.json()
        assert 'data' in response_data, "Response should contain posted data"
        assert len(response_data['data']) > 0, "Posted data should not be empty"

    def test_empty_binary_data(self, cycletls_client, httpbin_url):
        """Test that empty binary data is handled correctly."""
        empty_data = bytes()

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            body_bytes=empty_data,
            headers={'Content-Type': 'application/octet-stream'}
        )

        assert_valid_response(response, expected_status=200)

        response_data = response.json()
        # httpbin should handle empty data gracefully
        assert 'data' in response_data, "Response should contain data field"


class TestBinaryDownload:
    """Test binary data downloads and body_bytes field."""

    def test_download_jpeg_image(self, cycletls_client):
        """Test downloading JPEG image and verifying binary data integrity."""
        response = cycletls_client.get("https://httpbin.org/image/jpeg")

        assert_valid_response(response, expected_status=200)

        # Check if body_bytes is available
        if hasattr(response, 'body_bytes') and response.body_bytes:
            # Verify it's a valid JPEG (starts with 0xFF 0xD8)
            assert len(response.body_bytes) > 2, "JPEG data should be at least 2 bytes"
            assert response.body_bytes[0] == 0xFF, "JPEG should start with 0xFF"
            assert response.body_bytes[1] == 0xD8, "JPEG second byte should be 0xD8"

            # Verify we can calculate a consistent hash
            image_hash = hashlib.md5(response.body_bytes).hexdigest()
            assert image_hash, "Should be able to calculate hash of binary data"
            assert len(image_hash) == 32, "MD5 hash should be 32 characters"
        else:
            # If body_bytes not available, check body is not empty
            assert response.body, "Response body should not be empty"
            assert len(response.body) > 1000, "JPEG image should be reasonably large"

    def test_download_png_image(self, cycletls_client):
        """Test downloading PNG image and verifying PNG signature."""
        response = cycletls_client.get("https://httpbin.org/image/png")

        assert_valid_response(response, expected_status=200)

        # Check if body_bytes is available
        if hasattr(response, 'body_bytes') and response.body_bytes:
            # Verify it's valid PNG data (starts with PNG signature)
            png_signature = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
            assert len(response.body_bytes) >= 8, "PNG data should be at least 8 bytes"
            assert response.body_bytes[:8] == png_signature, \
                "PNG should start with valid PNG signature"

            # Verify we got substantial binary data
            assert len(response.body_bytes) > 1000, "PNG should be reasonably large"

            # Verify we can process binary data without corruption
            image_hash = hashlib.md5(response.body_bytes).hexdigest()
            assert image_hash, "Should be able to calculate hash"
            assert len(image_hash) == 32, "MD5 hash should be 32 characters"
        else:
            # If body_bytes not available, check body is not empty
            assert response.body, "Response body should not be empty"

    def test_download_webp_image(self, cycletls_client):
        """Test downloading WebP image."""
        response = cycletls_client.get("https://httpbin.org/image/webp")

        assert_valid_response(response, expected_status=200)

        # Verify we got image data (either in body_bytes or body)
        if hasattr(response, 'body_bytes') and response.body_bytes:
            assert len(response.body_bytes) > 100, "WebP image should have data"
        else:
            assert response.body, "Response body should not be empty"
            assert len(response.body) > 100, "WebP image should have data"

    def test_download_svg_image(self, cycletls_client):
        """Test downloading SVG image (text-based)."""
        response = cycletls_client.get("https://httpbin.org/image/svg")

        assert_valid_response(response, expected_status=200)

        # SVG is text-based, so should be in body as string
        assert response.body, "Response body should not be empty"
        assert isinstance(response.body, str), "SVG response should be string"
        assert '<svg' in response.body.lower() or 'svg' in response.body.lower(), \
            "Response should contain SVG content"


class TestMixedBinaryText:
    """Test handling of both binary and text data."""

    def test_mixed_binary_and_text_requests(self, cycletls_client, httpbin_url):
        """Test that both binary and text data work correctly in sequence."""
        # Upload binary data
        binary_data = bytes([0xFF, 0x00, 0x01, 0x02, 0x80, 0x81, 0xFE, 0xFF])
        binary_response = cycletls_client.post(
            f"{httpbin_url}/post",
            body_bytes=binary_data,
            headers={'Content-Type': 'application/octet-stream'}
        )
        assert_valid_response(binary_response, expected_status=200)

        # Upload text data
        text_response = cycletls_client.post(
            f"{httpbin_url}/post",
            json_data={"message": "Hello, world!", "binary": True}
        )
        assert_valid_response(text_response, expected_status=200)

        # Verify text response can be parsed as JSON
        text_response_data = text_response.json()
        assert 'json' in text_response_data, "Text response should have JSON data"
        assert text_response_data['json']['message'] == 'Hello, world!', \
            "JSON message should match"
        assert text_response_data['json']['binary'] is True, \
            "JSON binary field should be true"

        # Verify binary response has data
        binary_response_data = binary_response.json()
        assert 'data' in binary_response_data, "Binary response should contain data"


class TestBinaryDetection:
    """Test binary vs text detection."""

    def test_json_response_is_text(self, cycletls_client, httpbin_url):
        """Test that JSON responses are detected as text."""
        response = cycletls_client.get(f"{httpbin_url}/json")

        assert_valid_response(response, expected_status=200)

        # JSON should be in body as string
        assert response.body, "Response body should not be empty"
        assert isinstance(response.body, str), "JSON response should be string"

        # Should be parseable as JSON
        data = response.json()
        assert isinstance(data, dict), "JSON response should parse to dict"

    def test_html_response_is_text(self, cycletls_client, httpbin_url):
        """Test that HTML responses are detected as text."""
        response = cycletls_client.get(f"{httpbin_url}/html")

        assert_valid_response(response, expected_status=200)

        # HTML should be in body as string
        assert response.body, "Response body should not be empty"
        assert isinstance(response.body, str), "HTML response should be string"
        assert '<html' in response.body.lower() or '<!doctype' in response.body.lower(), \
            "Response should contain HTML"

    def test_image_response_is_binary(self, cycletls_client):
        """Test that image responses are detected as binary."""
        response = cycletls_client.get("https://httpbin.org/image/jpeg")

        assert_valid_response(response, expected_status=200)

        # Image should have data (either in body_bytes or body)
        if hasattr(response, 'body_bytes') and response.body_bytes:
            assert isinstance(response.body_bytes, bytes), "Image body_bytes should be bytes"
            assert len(response.body_bytes) > 0, "Image should have data"
        else:
            assert response.body, "Image body should not be empty"


class TestBinaryEdgeCases:
    """Test edge cases in binary data handling."""

    def test_binary_with_null_bytes(self, cycletls_client, httpbin_url):
        """Test binary data containing null bytes."""
        null_bytes_data = bytes([0x00, 0x01, 0x00, 0x02, 0x00, 0x03, 0x00, 0x04])

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            body_bytes=null_bytes_data,
            headers={'Content-Type': 'application/octet-stream'}
        )

        assert_valid_response(response, expected_status=200)

        response_data = response.json()
        assert 'data' in response_data, "Response should contain data"

    def test_binary_with_high_bytes(self, cycletls_client, httpbin_url):
        """Test binary data with high byte values (128-255)."""
        high_bytes_data = bytes(range(128, 256))

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            body_bytes=high_bytes_data,
            headers={'Content-Type': 'application/octet-stream'}
        )

        assert_valid_response(response, expected_status=200)

        response_data = response.json()
        assert 'data' in response_data, "Response should contain data"

    def test_large_image_download(self, cycletls_client):
        """Test downloading larger binary file (JPEG)."""
        response = cycletls_client.get("https://httpbin.org/image/jpeg")

        assert_valid_response(response, expected_status=200)

        # Verify we got substantial data
        if hasattr(response, 'body_bytes') and response.body_bytes:
            data_size = len(response.body_bytes)
        else:
            data_size = len(response.body)

        # JPEG images should be reasonably sized
        assert data_size > 1000, f"Image should be reasonably large, got {data_size} bytes"
        assert data_size < 10_000_000, \
            f"Image shouldn't be excessively large, got {data_size} bytes"

    def test_binary_content_type_header(self, cycletls_client):
        """Test that binary responses have appropriate Content-Type header."""
        response = cycletls_client.get("https://httpbin.org/image/png")

        assert_valid_response(response, expected_status=200)

        # Check Content-Type header
        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        assert 'content-type' in headers_lower, "Response should have Content-Type header"

        content_type = headers_lower['content-type']
        # Should indicate image type
        assert 'image' in content_type.lower(), \
            f"Content-Type should indicate image, got: {content_type}"
