"""
Image Download Tests for CycleTLS Python library.

Based on CycleTLS TypeScript images.test.ts, these tests verify:
- JPEG image download
- PNG image download
- GIF image download
- WebP image download
- SVG image download
- Binary integrity validation

Tests use httpbin.org/image endpoints to download various image formats
and verify their integrity by checking file signatures and data consistency.
"""

import pytest
import hashlib
import os
import tempfile
from test_utils import assert_valid_response


class TestImageDownloads:
    """Test downloading various image formats."""

    def test_download_jpeg_image(self, cycletls_client, chrome_ja3):
        """Test downloading JPEG image and verifying JPEG signature."""
        response = cycletls_client.get(
            "https://httpbin.org/image/jpeg",
            ja3=chrome_ja3,
            user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0"
        )

        assert_valid_response(response, expected_status=200)

        # Get binary data
        if hasattr(response, 'body_bytes') and response.body_bytes:
            image_data = response.body_bytes
        else:
            # Convert body string to bytes if needed
            image_data = response.body.encode('latin1') if isinstance(response.body, str) else response.body

        # Verify it's a valid JPEG (starts with 0xFF 0xD8)
        assert len(image_data) > 2, "JPEG data should be at least 2 bytes"
        assert image_data[0] == 0xFF, "JPEG should start with 0xFF"
        assert image_data[1] == 0xD8, "JPEG second byte should be 0xD8"

        # Verify we got substantial data
        assert len(image_data) > 1000, "JPEG should be reasonably large"

        # Calculate hash for consistency
        jpeg_hash = hashlib.md5(image_data).hexdigest()
        assert jpeg_hash, "Should be able to calculate hash of JPEG data"

    def test_download_png_image(self, cycletls_client, chrome_ja3):
        """Test downloading PNG image and verifying PNG signature."""
        response = cycletls_client.get(
            "https://httpbin.org/image/png",
            ja3=chrome_ja3,
            user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0"
        )

        assert_valid_response(response, expected_status=200)

        # Get binary data
        if hasattr(response, 'body_bytes') and response.body_bytes:
            image_data = response.body_bytes
        else:
            image_data = response.body.encode('latin1') if isinstance(response.body, str) else response.body

        # Verify it's valid PNG data (starts with PNG signature)
        png_signature = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
        assert len(image_data) >= 8, "PNG data should be at least 8 bytes"
        assert image_data[:8] == png_signature, "PNG should start with valid PNG signature"

        # Verify we got substantial data
        assert len(image_data) > 1000, "PNG should be reasonably large"

        # Calculate hash for consistency
        png_hash = hashlib.md5(image_data).hexdigest()
        assert png_hash, "Should be able to calculate hash of PNG data"

    def test_download_webp_image(self, cycletls_client, chrome_ja3):
        """Test downloading WebP image."""
        response = cycletls_client.get(
            "https://httpbin.org/image/webp",
            ja3=chrome_ja3,
            user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0"
        )

        assert_valid_response(response, expected_status=200)

        # Get binary data
        if hasattr(response, 'body_bytes') and response.body_bytes:
            image_data = response.body_bytes
        else:
            image_data = response.body.encode('latin1') if isinstance(response.body, str) else response.body

        # WebP should have "RIFF" at start and "WEBP" at offset 8
        assert len(image_data) >= 12, "WebP data should be at least 12 bytes"
        assert image_data[:4] == b'RIFF', "WebP should start with RIFF"
        assert image_data[8:12] == b'WEBP', "WebP should have WEBP signature at offset 8"

        # Verify we got substantial data
        assert len(image_data) > 100, "WebP should have substantial data"

        # Calculate hash for consistency
        webp_hash = hashlib.md5(image_data).hexdigest()
        assert webp_hash, "Should be able to calculate hash of WebP data"

    def test_download_svg_image(self, cycletls_client, chrome_ja3):
        """Test downloading SVG image (text-based)."""
        response = cycletls_client.get(
            "https://httpbin.org/image/svg",
            ja3=chrome_ja3,
            user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0"
        )

        assert_valid_response(response, expected_status=200)

        # SVG is text-based, so should be in body as string
        assert response.body, "Response body should not be empty"

        # Convert to string if it's bytes
        svg_content = response.body
        if isinstance(svg_content, bytes):
            svg_content = svg_content.decode('utf-8')

        # Check for SVG content
        assert isinstance(svg_content, str), "SVG response should be string"
        assert '<svg' in svg_content.lower() or 'svg' in svg_content.lower(), \
            "Response should contain SVG content"

    def test_download_gif_image(self, cycletls_client, chrome_ja3):
        """Test downloading GIF image and verifying GIF signature."""
        # Note: httpbin.org doesn't have /image/gif endpoint, so we skip this
        # or use an alternative endpoint if available
        pytest.skip("httpbin.org does not provide /image/gif endpoint")


class TestImageBinaryIntegrity:
    """Test binary integrity of downloaded images."""

    def test_jpeg_binary_integrity(self, cycletls_client, chrome_ja3):
        """Test that JPEG binary data is preserved without corruption."""
        # Download the same image twice
        response1 = cycletls_client.get(
            "https://httpbin.org/image/jpeg",
            ja3=chrome_ja3,
            user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0"
        )

        response2 = cycletls_client.get(
            "https://httpbin.org/image/jpeg",
            ja3=chrome_ja3,
            user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0"
        )

        assert_valid_response(response1, expected_status=200)
        assert_valid_response(response2, expected_status=200)

        # Get binary data from both responses
        if hasattr(response1, 'body_bytes') and response1.body_bytes:
            data1 = response1.body_bytes
            data2 = response2.body_bytes
        else:
            data1 = response1.body.encode('latin1') if isinstance(response1.body, str) else response1.body
            data2 = response2.body.encode('latin1') if isinstance(response2.body, str) else response2.body

        # Calculate hashes - they should match
        hash1 = hashlib.md5(data1).hexdigest()
        hash2 = hashlib.md5(data2).hexdigest()

        assert hash1 == hash2, "JPEG binary data should be consistent across downloads"

    def test_png_binary_integrity(self, cycletls_client, chrome_ja3):
        """Test that PNG binary data is preserved without corruption."""
        # Download the same image twice
        response1 = cycletls_client.get(
            "https://httpbin.org/image/png",
            ja3=chrome_ja3,
            user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0"
        )

        response2 = cycletls_client.get(
            "https://httpbin.org/image/png",
            ja3=chrome_ja3,
            user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0"
        )

        assert_valid_response(response1, expected_status=200)
        assert_valid_response(response2, expected_status=200)

        # Get binary data from both responses
        if hasattr(response1, 'body_bytes') and response1.body_bytes:
            data1 = response1.body_bytes
            data2 = response2.body_bytes
        else:
            data1 = response1.body.encode('latin1') if isinstance(response1.body, str) else response1.body
            data2 = response2.body.encode('latin1') if isinstance(response2.body, str) else response2.body

        # Calculate hashes - they should match
        hash1 = hashlib.md5(data1).hexdigest()
        hash2 = hashlib.md5(data2).hexdigest()

        assert hash1 == hash2, "PNG binary data should be consistent across downloads"

    def test_webp_binary_integrity(self, cycletls_client, chrome_ja3):
        """Test that WebP binary data is preserved without corruption."""
        # Download the same image twice
        response1 = cycletls_client.get(
            "https://httpbin.org/image/webp",
            ja3=chrome_ja3,
            user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0"
        )

        response2 = cycletls_client.get(
            "https://httpbin.org/image/webp",
            ja3=chrome_ja3,
            user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0"
        )

        assert_valid_response(response1, expected_status=200)
        assert_valid_response(response2, expected_status=200)

        # Get binary data from both responses
        if hasattr(response1, 'body_bytes') and response1.body_bytes:
            data1 = response1.body_bytes
            data2 = response2.body_bytes
        else:
            data1 = response1.body.encode('latin1') if isinstance(response1.body, str) else response1.body
            data2 = response2.body.encode('latin1') if isinstance(response2.body, str) else response2.body

        # Calculate hashes - they should match
        hash1 = hashlib.md5(data1).hexdigest()
        hash2 = hashlib.md5(data2).hexdigest()

        assert hash1 == hash2, "WebP binary data should be consistent across downloads"


class TestImageFileWrite:
    """Test writing downloaded images to files."""

    def test_write_all_image_types_to_file(self, cycletls_client, chrome_ja3):
        """Test downloading all image types and writing them to files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download and write JPEG
            jpeg_response = cycletls_client.get(
                "https://httpbin.org/image/jpeg",
                ja3=chrome_ja3,
                user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0"
            )
            assert_valid_response(jpeg_response, expected_status=200)

            jpeg_data = jpeg_response.body_bytes if hasattr(jpeg_response, 'body_bytes') and jpeg_response.body_bytes else \
                        (jpeg_response.body.encode('latin1') if isinstance(jpeg_response.body, str) else jpeg_response.body)

            jpeg_path = os.path.join(temp_dir, "output.jpeg")
            with open(jpeg_path, 'wb') as f:
                f.write(jpeg_data)

            assert os.path.exists(jpeg_path), "JPEG file should be written"
            assert os.path.getsize(jpeg_path) > 0, "JPEG file should not be empty"

            # Download and write PNG
            png_response = cycletls_client.get(
                "https://httpbin.org/image/png",
                ja3=chrome_ja3,
                user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0"
            )
            assert_valid_response(png_response, expected_status=200)

            png_data = png_response.body_bytes if hasattr(png_response, 'body_bytes') and png_response.body_bytes else \
                       (png_response.body.encode('latin1') if isinstance(png_response.body, str) else png_response.body)

            png_path = os.path.join(temp_dir, "output.png")
            with open(png_path, 'wb') as f:
                f.write(png_data)

            assert os.path.exists(png_path), "PNG file should be written"
            assert os.path.getsize(png_path) > 0, "PNG file should not be empty"

            # Download and write WebP
            webp_response = cycletls_client.get(
                "https://httpbin.org/image/webp",
                ja3=chrome_ja3,
                user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0"
            )
            assert_valid_response(webp_response, expected_status=200)

            webp_data = webp_response.body_bytes if hasattr(webp_response, 'body_bytes') and webp_response.body_bytes else \
                        (webp_response.body.encode('latin1') if isinstance(webp_response.body, str) else webp_response.body)

            webp_path = os.path.join(temp_dir, "output.webp")
            with open(webp_path, 'wb') as f:
                f.write(webp_data)

            assert os.path.exists(webp_path), "WebP file should be written"
            assert os.path.getsize(webp_path) > 0, "WebP file should not be empty"

            # Download and write SVG
            svg_response = cycletls_client.get(
                "https://httpbin.org/image/svg",
                ja3=chrome_ja3,
                user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0"
            )
            assert_valid_response(svg_response, expected_status=200)

            svg_data = svg_response.body
            if isinstance(svg_data, str):
                svg_data = svg_data.encode('utf-8')

            svg_path = os.path.join(temp_dir, "output.svg")
            with open(svg_path, 'wb') as f:
                f.write(svg_data)

            assert os.path.exists(svg_path), "SVG file should be written"
            assert os.path.getsize(svg_path) > 0, "SVG file should not be empty"

            # Verify files can be read back
            with open(jpeg_path, 'rb') as f:
                jpeg_readback = f.read()
                assert jpeg_readback[:2] == b'\xff\xd8', "JPEG file should be valid after write/read"

            with open(png_path, 'rb') as f:
                png_readback = f.read()
                assert png_readback[:8] == bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]), \
                    "PNG file should be valid after write/read"

            with open(webp_path, 'rb') as f:
                webp_readback = f.read()
                assert webp_readback[:4] == b'RIFF', "WebP file should be valid after write/read"
                assert webp_readback[8:12] == b'WEBP', "WebP file should be valid after write/read"
