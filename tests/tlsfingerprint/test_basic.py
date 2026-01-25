"""
Basic TLS fingerprint tests against tlsfingerprint.com.

Tests basic HTTP methods (GET, POST, PUT, PATCH, DELETE) and
validates that TLS fingerprint fields are present in responses.

Mirrors TypeScript tests in tests/tlsfingerprint/basic.test.ts
"""

import pytest
from .conftest import (
    TEST_SERVER_URL,
    get_default_options,
    assert_tls_fields_present,
    is_service_available,
)


# Check service availability at module level
pytestmark = pytest.mark.skipif(
    not is_service_available(),
    reason="tlsfingerprint.com is unavailable (received 521 or timeout)"
)


class TestTLSFingerprintBasicGETRequests:
    """GET Requests tests."""

    def test_should_make_get_request_and_return_tls_fingerprint_fields(self, cycle_client):
        """Should make a GET request and return TLS fingerprint fields."""
        options = get_default_options()
        response = cycle_client.get(f"{TEST_SERVER_URL}/get?foo=bar", **options)

        assert response.status_code == 200

        body = response.json()

        # Verify TLS fingerprint fields are present
        assert_tls_fields_present(body)

        # Verify query args are present
        assert "args" in body
        assert body["args"].get("foo") == "bar"

    def test_should_include_ja3_hash_in_response(self, cycle_client):
        """Should include ja3 hash in response."""
        options = get_default_options()
        response = cycle_client.get(f"{TEST_SERVER_URL}/get", **options)

        assert response.status_code == 200

        body = response.json()

        assert "ja3" in body
        assert len(body["ja3"]) > 0
        assert "ja3_hash" in body
        assert len(body["ja3_hash"]) > 0

    def test_should_include_ja4_fingerprint_in_response(self, cycle_client):
        """Should include ja4 fingerprint in response."""
        options = get_default_options()
        response = cycle_client.get(f"{TEST_SERVER_URL}/get", **options)

        assert response.status_code == 200

        body = response.json()

        assert "ja4" in body
        assert len(body["ja4"]) > 0

    def test_should_include_peetprint_in_response(self, cycle_client):
        """Should include peetprint in response."""
        options = get_default_options()
        response = cycle_client.get(f"{TEST_SERVER_URL}/get", **options)

        assert response.status_code == 200

        body = response.json()

        assert "peetprint" in body
        assert len(body["peetprint"]) > 0
        assert "peetprint_hash" in body
        assert len(body["peetprint_hash"]) > 0


class TestTLSFingerprintBasicPOSTRequests:
    """POST Requests tests."""

    def test_should_make_post_request_with_json_body(self, cycle_client):
        """Should make a POST request with JSON body."""
        options = get_default_options()
        response = cycle_client.post(
            f"{TEST_SERVER_URL}/post",
            json_data={"message": "hello"},
            **options,
        )

        assert response.status_code == 200

        body = response.json()

        assert_tls_fields_present(body)

        # Note: tlsfingerprint.com may redirect to tls.peet.ws which can lose the body
        # The important thing is that the POST was made with TLS fingerprint fields present
        # Verify the method is captured as POST
        assert body.get("method") == "POST"


class TestTLSFingerprintBasicPUTRequests:
    """PUT Requests tests."""

    def test_should_make_put_request_with_json_body(self, cycle_client):
        """Should make a PUT request with JSON body."""
        options = get_default_options()
        response = cycle_client.put(
            f"{TEST_SERVER_URL}/put",
            json_data={"update": "data"},
            **options,
        )

        assert response.status_code == 200

        body = response.json()

        assert_tls_fields_present(body)


class TestTLSFingerprintBasicPATCHRequests:
    """PATCH Requests tests."""

    def test_should_make_patch_request_with_json_body(self, cycle_client):
        """Should make a PATCH request with JSON body."""
        options = get_default_options()
        response = cycle_client.patch(
            f"{TEST_SERVER_URL}/patch",
            json_data={"patch": "value"},
            **options,
        )

        assert response.status_code == 200

        body = response.json()

        assert_tls_fields_present(body)


class TestTLSFingerprintBasicDELETERequests:
    """DELETE Requests tests."""

    def test_should_make_delete_request(self, cycle_client):
        """Should make a DELETE request."""
        options = get_default_options()
        response = cycle_client.delete(f"{TEST_SERVER_URL}/delete", **options)

        assert response.status_code == 200

        body = response.json()

        assert_tls_fields_present(body)


class TestTLSFingerprintBasicAnythingEndpoint:
    """Anything Endpoint tests."""

    def test_should_echo_request_to_anything_endpoint(self, cycle_client):
        """Should echo request to /anything endpoint."""
        options = get_default_options()
        response = cycle_client.get(f"{TEST_SERVER_URL}/anything", **options)

        assert response.status_code == 200

        body = response.json()

        assert_tls_fields_present(body)

        # Verify method is captured
        assert body.get("method") == "GET"

    def test_should_capture_post_method_in_anything_endpoint(self, cycle_client):
        """Should capture POST method in /anything endpoint."""
        options = get_default_options()
        response = cycle_client.post(
            f"{TEST_SERVER_URL}/anything",
            json_data={"test": "data"},
            **options,
        )

        assert response.status_code == 200

        body = response.json()

        assert_tls_fields_present(body)
        assert body.get("method") == "POST"


class TestTLSFingerprintBasicHeadersEndpoint:
    """Headers Endpoint tests."""

    def test_should_echo_custom_headers(self, cycle_client):
        """Should echo custom headers."""
        options = get_default_options()
        response = cycle_client.get(
            f"{TEST_SERVER_URL}/headers",
            headers={
                "X-Custom-Header": "TestValue123",
                "Accept": "application/json",
            },
            **options,
        )

        assert response.status_code == 200

        body = response.json()

        assert_tls_fields_present(body)

        # Headers should be echoed back
        headers = body.get("headers", {})
        assert headers is not None

        # Header names may be normalized (case-insensitive)
        custom_header = headers.get("X-Custom-Header") or headers.get("x-custom-header")
        assert custom_header == "TestValue123"
