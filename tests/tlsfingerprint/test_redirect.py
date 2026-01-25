"""
Redirect tests against tlsfingerprint.com.

Tests redirect following behavior and status code handling.

Mirrors TypeScript tests in tests/tlsfingerprint/redirect.test.ts
"""

from urllib.parse import quote
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


class TestTLSFingerprintRedirectFollowing:
    """Redirect Following tests."""

    def test_should_follow_redirect_3_chain_and_end_at_get(self, cycle_client):
        """Should follow /redirect/3 chain and end at /get."""
        options = get_default_options()
        response = cycle_client.get(f"{TEST_SERVER_URL}/redirect/3", **options)

        assert response.status_code == 200

        body = response.json()

        # Verify TLS fields present after redirect chain
        assert_tls_fields_present(body)

        # After following 3 redirects, we end up at /get which returns EchoResponse
        assert body.get("method") == "GET"

    def test_should_follow_redirect_1_single_redirect(self, cycle_client):
        """Should follow /redirect/1 single redirect."""
        options = get_default_options()
        response = cycle_client.get(f"{TEST_SERVER_URL}/redirect/1", **options)

        assert response.status_code == 200

        body = response.json()

        assert_tls_fields_present(body)

    def test_should_follow_redirect_5_multiple_redirects(self, cycle_client):
        """Should follow /redirect/5 multiple redirects."""
        options = get_default_options()
        response = cycle_client.get(f"{TEST_SERVER_URL}/redirect/5", **options)

        assert response.status_code == 200

        body = response.json()

        assert_tls_fields_present(body)


class TestTLSFingerprintRedirectToEndpoint:
    """Redirect-To Endpoint tests."""

    def test_should_follow_redirect_to_internal_url(self, cycle_client):
        """Should follow redirect-to internal URL."""
        options = get_default_options()
        target_url = quote(f"{TEST_SERVER_URL}/get", safe="")
        response = cycle_client.get(
            f"{TEST_SERVER_URL}/redirect-to?url={target_url}",
            **options,
        )

        assert response.status_code == 200

        body = response.json()

        assert_tls_fields_present(body)

        # Verify url field is present in response
        assert "url" in body


class TestTLSFingerprintDisableRedirect:
    """Disable Redirect tests."""

    def test_should_return_302_when_redirects_are_disabled(self, cycle_client):
        """Should return 302 when redirects are disabled."""
        options = get_default_options()
        response = cycle_client.get(
            f"{TEST_SERVER_URL}/redirect/1",
            disable_redirect=True,
            **options,
        )

        assert response.status_code == 302

    def test_should_return_redirect_location_header_when_disabled(self, cycle_client):
        """Should return redirect location header when disabled."""
        options = get_default_options()
        response = cycle_client.get(
            f"{TEST_SERVER_URL}/redirect/1",
            disable_redirect=True,
            **options,
        )

        assert response.status_code == 302
        assert response.headers is not None

        # Location header should be present
        headers = response.headers
        location = headers.get("Location") or headers.get("location")
        assert location is not None


class TestTLSFingerprintStatusCodes:
    """Status Codes tests."""

    def test_should_return_201_created_status(self, cycle_client):
        """Should return 201 Created status."""
        options = get_default_options()
        response = cycle_client.get(f"{TEST_SERVER_URL}/status/201", **options)

        assert response.status_code == 201

        body = response.json()

        assert_tls_fields_present(body)

        # Verify status_code in response body matches
        assert body.get("status_code") == 201

    def test_should_return_400_bad_request_status(self, cycle_client):
        """Should return 400 Bad Request status."""
        options = get_default_options()
        response = cycle_client.get(f"{TEST_SERVER_URL}/status/400", **options)

        assert response.status_code == 400

        body = response.json()

        assert_tls_fields_present(body)
        assert body.get("status_code") == 400

    def test_should_return_404_not_found_status(self, cycle_client):
        """Should return 404 Not Found status."""
        options = get_default_options()
        response = cycle_client.get(f"{TEST_SERVER_URL}/status/404", **options)

        assert response.status_code == 404

        body = response.json()

        assert_tls_fields_present(body)
        assert body.get("status_code") == 404

    def test_should_return_500_internal_server_error_status(self, cycle_client):
        """Should return 500 Internal Server Error status."""
        options = get_default_options()
        response = cycle_client.get(f"{TEST_SERVER_URL}/status/500", **options)

        assert response.status_code == 500

        body = response.json()

        assert_tls_fields_present(body)
        assert body.get("status_code") == 500

    def test_should_return_204_no_content_status(self, cycle_client):
        """Should return 204 No Content status."""
        options = get_default_options()
        response = cycle_client.get(f"{TEST_SERVER_URL}/status/204", **options)

        assert response.status_code == 204

        # 204 has no body, just verify the status


@pytest.mark.skip(reason="/absolute-redirect endpoint not available on tlsfingerprint.com")
class TestTLSFingerprintAbsoluteRedirect:
    """Absolute Redirect tests."""

    def test_should_follow_absolute_redirect_endpoint(self, cycle_client):
        """Should follow absolute-redirect endpoint."""
        options = get_default_options()
        response = cycle_client.get(
            f"{TEST_SERVER_URL}/absolute-redirect/2",
            **options,
        )

        assert response.status_code == 200

        body = response.json()

        assert_tls_fields_present(body)


@pytest.mark.skip(reason="/relative-redirect endpoint not available on tlsfingerprint.com")
class TestTLSFingerprintRelativeRedirect:
    """Relative Redirect tests."""

    def test_should_follow_relative_redirect_endpoint(self, cycle_client):
        """Should follow relative-redirect endpoint."""
        options = get_default_options()
        response = cycle_client.get(
            f"{TEST_SERVER_URL}/relative-redirect/2",
            **options,
        )

        assert response.status_code == 200

        body = response.json()

        assert_tls_fields_present(body)
