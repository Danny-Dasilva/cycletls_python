"""
Compression tests against tlsfingerprint.com.

Tests gzip, deflate, and brotli compression handling.
The CycleTLS client returns raw response bytes, so we manually
decompress in the tests to validate the response.

Mirrors TypeScript tests in tests/tlsfingerprint/compression.test.ts
"""

import re
import pytest
from .conftest import (
    TEST_SERVER_URL,
    get_default_options,
    assert_tls_fields_present,
    decompress_gzip,
    decompress_deflate,
    decompress_brotli,
    is_service_available,
)


# Check service availability at module level
pytestmark = pytest.mark.skipif(
    not is_service_available(),
    reason="tlsfingerprint.com is unavailable (received 521 or timeout)"
)


class TestTLSFingerprintCompressionGzip:
    """Gzip Compression tests."""

    def test_should_handle_gzip_compressed_response(self, cycle_client):
        """Should handle gzip compressed response."""
        options = get_default_options()
        response = cycle_client.get(
            f"{TEST_SERVER_URL}/gzip",
            headers={"Accept-Encoding": "gzip, deflate, br"},
            **options,
        )

        assert response.status_code == 200

        # Get raw body bytes and manually decompress
        raw_body = response.body if isinstance(response.body, bytes) else response.text.encode()
        body = decompress_gzip(raw_body)

        assert_tls_fields_present(body)

        # Verify gzipped flag is true
        assert body.get("gzipped") is True

    def test_should_decompress_gzip_and_validate_tls_fields(self, cycle_client):
        """Should decompress gzip and validate TLS fields."""
        options = get_default_options()
        response = cycle_client.get(f"{TEST_SERVER_URL}/gzip", **options)

        assert response.status_code == 200

        # Decompress and parse JSON
        raw_body = response.body if isinstance(response.body, bytes) else response.text.encode()
        body = decompress_gzip(raw_body)

        assert body.get("gzipped") is True
        assert_tls_fields_present(body)

        # Verify JA3 fingerprint is present
        assert "ja3" in body
        assert len(body["ja3"]) > 50


class TestTLSFingerprintCompressionDeflate:
    """Deflate Compression tests."""

    def test_should_handle_deflate_compressed_response(self, cycle_client):
        """Should handle deflate compressed response."""
        options = get_default_options()
        response = cycle_client.get(
            f"{TEST_SERVER_URL}/deflate",
            headers={"Accept-Encoding": "deflate"},
            **options,
        )

        assert response.status_code == 200

        # Manually decompress the deflate response
        raw_body = response.body if isinstance(response.body, bytes) else response.text.encode()
        body = decompress_deflate(raw_body)

        assert_tls_fields_present(body)

        # Verify deflated flag is true
        assert body.get("deflated") is True

    def test_should_decompress_deflate_and_validate_tls_fields(self, cycle_client):
        """Should decompress deflate and validate TLS fields."""
        options = get_default_options()
        response = cycle_client.get(f"{TEST_SERVER_URL}/deflate", **options)

        assert response.status_code == 200

        raw_body = response.body if isinstance(response.body, bytes) else response.text.encode()
        body = decompress_deflate(raw_body)

        assert body.get("deflated") is True
        assert_tls_fields_present(body)


class TestTLSFingerprintCompressionBrotli:
    """Brotli Compression tests."""

    def test_should_handle_brotli_compressed_response(self, cycle_client):
        """Should handle brotli compressed response."""
        options = get_default_options()
        response = cycle_client.get(
            f"{TEST_SERVER_URL}/brotli",
            headers={"Accept-Encoding": "gzip, deflate, br"},
            **options,
        )

        assert response.status_code == 200

        # Manually decompress the brotli response
        raw_body = response.body if isinstance(response.body, bytes) else response.text.encode()
        body = decompress_brotli(raw_body)

        assert_tls_fields_present(body)

        # Verify brotli flag is true
        assert body.get("brotli") is True

    def test_should_decompress_brotli_and_validate_tls_fields(self, cycle_client):
        """Should decompress brotli and validate TLS fields."""
        options = get_default_options()
        response = cycle_client.get(f"{TEST_SERVER_URL}/brotli", **options)

        assert response.status_code == 200

        raw_body = response.body if isinstance(response.body, bytes) else response.text.encode()
        body = decompress_brotli(raw_body)

        assert body.get("brotli") is True
        assert_tls_fields_present(body)


class TestTLSFingerprintCompressionSpecificAcceptEncoding:
    """Compression with specific Accept-Encoding tests."""

    def test_should_work_with_only_gzip_accept_encoding(self, cycle_client):
        """Should work with only gzip Accept-Encoding."""
        options = get_default_options()
        response = cycle_client.get(
            f"{TEST_SERVER_URL}/gzip",
            headers={"Accept-Encoding": "gzip"},
            **options,
        )

        assert response.status_code == 200

        raw_body = response.body if isinstance(response.body, bytes) else response.text.encode()
        body = decompress_gzip(raw_body)
        assert body.get("gzipped") is True

    def test_should_work_with_only_deflate_accept_encoding(self, cycle_client):
        """Should work with only deflate Accept-Encoding."""
        options = get_default_options()
        response = cycle_client.get(
            f"{TEST_SERVER_URL}/deflate",
            headers={"Accept-Encoding": "deflate"},
            **options,
        )

        assert response.status_code == 200

        raw_body = response.body if isinstance(response.body, bytes) else response.text.encode()
        body = decompress_deflate(raw_body)
        assert body.get("deflated") is True

    def test_should_work_with_only_br_accept_encoding(self, cycle_client):
        """Should work with only br Accept-Encoding."""
        options = get_default_options()
        response = cycle_client.get(
            f"{TEST_SERVER_URL}/brotli",
            headers={"Accept-Encoding": "br"},
            **options,
        )

        assert response.status_code == 200

        raw_body = response.body if isinstance(response.body, bytes) else response.text.encode()
        body = decompress_brotli(raw_body)
        assert body.get("brotli") is True


class TestTLSFingerprintCompressionAllTypesWithTLSValidation:
    """All compression types with TLS fingerprint validation tests."""

    def test_should_have_valid_tls_fingerprint_fields_for_gzip(self, cycle_client):
        """Should have valid TLS fingerprint fields for /gzip."""
        options = get_default_options()
        response = cycle_client.get(f"{TEST_SERVER_URL}/gzip", **options)

        assert response.status_code == 200

        raw_body = response.body if isinstance(response.body, bytes) else response.text.encode()
        body = decompress_gzip(raw_body)

        # Must have all required TLS fields
        assert_tls_fields_present(body)

        # Compression flag should be true
        assert body.get("gzipped") is True

        # JA3 should be a non-empty string
        assert isinstance(body.get("ja3"), str)
        assert len(body["ja3"]) > 50

        # JA3 hash should be MD5 format (32 hex chars)
        assert re.match(r"^[a-f0-9]{32}$", body["ja3_hash"])

    def test_should_have_valid_tls_fingerprint_fields_for_deflate(self, cycle_client):
        """Should have valid TLS fingerprint fields for /deflate."""
        options = get_default_options()
        response = cycle_client.get(f"{TEST_SERVER_URL}/deflate", **options)

        assert response.status_code == 200

        raw_body = response.body if isinstance(response.body, bytes) else response.text.encode()
        body = decompress_deflate(raw_body)

        assert_tls_fields_present(body)
        assert body.get("deflated") is True
        assert isinstance(body.get("ja3"), str)
        assert len(body["ja3"]) > 50
        assert re.match(r"^[a-f0-9]{32}$", body["ja3_hash"])

    def test_should_have_valid_tls_fingerprint_fields_for_brotli(self, cycle_client):
        """Should have valid TLS fingerprint fields for /brotli."""
        options = get_default_options()
        response = cycle_client.get(f"{TEST_SERVER_URL}/brotli", **options)

        assert response.status_code == 200

        raw_body = response.body if isinstance(response.body, bytes) else response.text.encode()
        body = decompress_brotli(raw_body)

        assert_tls_fields_present(body)
        assert body.get("brotli") is True
        assert isinstance(body.get("ja3"), str)
        assert len(body["ja3"]) > 50
        assert re.match(r"^[a-f0-9]{32}$", body["ja3_hash"])
