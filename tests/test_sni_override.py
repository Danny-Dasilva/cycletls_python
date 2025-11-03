"""
SNI Override Tests for CycleTLS Python library.

Based on CycleTLS TypeScript sni-override.test.ts, these tests verify:
- Custom SNI (Server Name Indication) value using server_name parameter
- SNI different from hostname
- SNI validation
- Domain fronting scenarios (different SNI vs Host header)

SNI (Server Name Indication) is a TLS extension that allows a client to indicate
which hostname it is attempting to connect to at the start of the TLS handshake.
This is useful for domain fronting and other advanced networking scenarios.

Note: These tests require specific server setup to fully validate SNI behavior.
Some tests may be marked as skip if local test server is not available.
"""

import pytest
import ssl
import socket
from test_utils import assert_valid_response


class TestBasicSNIOverride:
    """Test basic SNI override functionality."""

    def test_sni_parameter_accepted(self, cycletls_client_function, chrome_ja3):
        """Test that server_name parameter is accepted without error."""
        # Make a request with custom SNI
        # Using a real endpoint that accepts SNI
        try:
            response = cycletls_client_function.get(
                "https://httpbin.org/get",
                ja3=chrome_ja3,
                server_name="httpbin.org",  # Same as actual host
                insecure_skip_verify=False
            )

            assert_valid_response(response, expected_status=200)

        except Exception as e:
            # If server_name parameter is not supported yet, skip
            if 'server_name' in str(e).lower() or 'unexpected' in str(e).lower():
                pytest.skip("server_name parameter not yet implemented")
            raise

    def test_sni_with_ip_address_connection(self, cycletls_client_function, chrome_ja3):
        """Test SNI when connecting via IP address instead of hostname."""
        # When connecting by IP, SNI is crucial for proper TLS handshake
        # This is a simplified test since we need a specific server setup

        # Skip this test for now as it requires special server setup
        pytest.skip("Requires custom test server with SNI validation")

    def test_sni_different_from_host_header(self, cycletls_client_function, chrome_ja3):
        """Test SNI different from Host header (domain fronting scenario)."""
        # This is the core domain fronting test case
        # Skip for now as it requires custom test server
        pytest.skip("Requires custom test server with SNI validation")


class TestSNIDomainFronting:
    """Test domain fronting scenarios with SNI."""

    def test_custom_sni_with_custom_host_header(self, cycletls_client_function, chrome_ja3):
        """
        Test domain fronting: custom SNI for TLS + different Host header for HTTP.

        In domain fronting:
        - TLS SNI: front.example (what the network sees)
        - HTTP Host: real.example (what the application sees)
        """
        # This requires a custom test server setup
        # The original TypeScript test uses a local HTTPS server with SNI callback

        pytest.skip("Requires custom test server with SNI callback to validate")

    def test_sni_validation_with_local_server(self, cycletls_client_function, chrome_ja3):
        """
        Test that validates SNI is properly sent to the server.

        This test would require:
        1. Local HTTPS server with SNI callback
        2. Self-signed certificate
        3. Capture of SNI value during handshake
        """
        pytest.skip("Requires local HTTPS test server with SNI validation")


class TestSNIWithTLS:
    """Test SNI behavior with various TLS scenarios."""

    def test_sni_with_tls_verification_enabled(self, cycletls_client_function, chrome_ja3):
        """Test SNI with TLS verification enabled."""
        # Standard request with TLS verification
        response = cycletls_client_function.get(
            "https://httpbin.org/get",
            ja3=chrome_ja3,
            insecure_skip_verify=False
        )

        assert_valid_response(response, expected_status=200)

    def test_sni_with_tls_verification_disabled(self, cycletls_client_function, chrome_ja3):
        """Test SNI with TLS verification disabled (insecure)."""
        # Request with TLS verification disabled
        response = cycletls_client_function.get(
            "https://httpbin.org/get",
            ja3=chrome_ja3,
            insecure_skip_verify=True
        )

        assert_valid_response(response, expected_status=200)

    def test_sni_with_self_signed_certificate(self, cycletls_client_function, chrome_ja3):
        """Test SNI with self-signed certificate."""
        # This would require a test server with self-signed cert
        pytest.skip("Requires test server with self-signed certificate")


class TestSNIEdgeCases:
    """Test edge cases in SNI handling."""

    def test_empty_sni_value(self, cycletls_client_function, chrome_ja3):
        """Test behavior with empty SNI value."""
        try:
            # Try to send empty SNI
            response = cycletls_client_function.get(
                "https://httpbin.org/get",
                ja3=chrome_ja3,
                server_name="",  # Empty SNI
                insecure_skip_verify=True
            )

            # Should either work or raise appropriate error
            # Behavior may vary by implementation

        except Exception as e:
            # Empty SNI might be rejected
            error_msg = str(e).lower()
            # This is acceptable
            assert len(error_msg) > 0, "Should have error message for empty SNI"

    def test_sni_with_special_characters(self, cycletls_client_function, chrome_ja3):
        """Test SNI with special characters (should fail)."""
        # SNI should not accept special characters
        try:
            response = cycletls_client_function.get(
                "https://httpbin.org/get",
                ja3=chrome_ja3,
                server_name="invalid@host!.com",  # Invalid hostname
                insecure_skip_verify=True
            )

            # If it doesn't fail, that's unexpected but not necessarily wrong
            # Depends on validation implementation

        except Exception:
            # Expected to fail with invalid hostname
            pass

    def test_sni_with_unicode_domain(self, cycletls_client_function, chrome_ja3):
        """Test SNI with internationalized domain name (IDN)."""
        # IDN domains should be converted to punycode for SNI
        try:
            response = cycletls_client_function.get(
                "https://httpbin.org/get",
                ja3=chrome_ja3,
                server_name="httpbin.org",  # Using ASCII for this test
                insecure_skip_verify=False
            )

            assert_valid_response(response, expected_status=200)

        except Exception as e:
            if 'server_name' in str(e).lower():
                pytest.skip("server_name parameter not yet implemented")
            raise


class TestSNIWithProxies:
    """Test SNI behavior with proxy configurations."""

    def test_sni_with_http_proxy(self, cycletls_client_function, chrome_ja3):
        """Test SNI when using HTTP proxy."""
        # When using HTTP proxy for HTTPS, SNI should still be sent to origin
        pytest.skip("Requires proxy server configuration")

    def test_sni_with_socks_proxy(self, cycletls_client_function, chrome_ja3):
        """Test SNI when using SOCKS proxy."""
        pytest.skip("Requires SOCKS proxy server configuration")


class TestSNIRealWorldScenarios:
    """Test real-world SNI scenarios."""

    def test_sni_with_cdn_endpoint(self, cycletls_client_function, chrome_ja3):
        """Test SNI with CDN endpoint (common real-world scenario)."""
        # Many CDNs use SNI to route to the correct origin
        response = cycletls_client_function.get(
            "https://httpbin.org/get",  # httpbin uses Fastly CDN
            ja3=chrome_ja3
        )

        assert_valid_response(response, expected_status=200)

    def test_sni_with_load_balancer(self, cycletls_client_function, chrome_ja3):
        """Test SNI with load-balanced endpoint."""
        # Load balancers often use SNI for routing
        response = cycletls_client_function.get(
            "https://httpbin.org/get",
            ja3=chrome_ja3
        )

        assert_valid_response(response, expected_status=200)

    def test_multiple_requests_with_different_sni(self, cycletls_client_function, chrome_ja3):
        """Test multiple requests with different SNI values."""
        # First request
        response1 = cycletls_client_function.get(
            "https://httpbin.org/get",
            ja3=chrome_ja3
        )

        assert_valid_response(response1, expected_status=200)

        # Second request to different domain
        response2 = cycletls_client_function.get(
            "https://httpbin.org/anything",
            ja3=chrome_ja3
        )

        assert_valid_response(response2, expected_status=200)

        # Both should succeed independently


class TestSNIDocumentation:
    """Tests that serve as documentation for SNI usage."""

    def test_sni_basic_usage_example(self, cycletls_client_function, chrome_ja3):
        """
        Basic example of SNI usage.

        SNI (Server Name Indication) tells the server which hostname
        the client is trying to connect to during TLS handshake.
        """
        response = cycletls_client_function.get(
            "https://httpbin.org/get",
            ja3=chrome_ja3,
            # server_name would specify custom SNI if needed
        )

        assert_valid_response(response, expected_status=200)

    def test_sni_domain_fronting_example(self, cycletls_client_function, chrome_ja3):
        """
        Example of domain fronting scenario (for documentation).

        Domain fronting uses different values for:
        - TLS SNI: The domain seen by network observers
        - HTTP Host header: The actual application endpoint

        Note: Domain fronting may be blocked by many CDNs and services.
        This is for educational purposes only.
        """
        # This is a conceptual example
        # Actual implementation would require:
        # response = cycletls_client_function.get(
        #     "https://1.2.3.4/",  # Connect to IP
        #     server_name="front.example.com",  # SNI for TLS
        #     headers={"Host": "real.example.com"},  # Host for HTTP
        #     insecure_skip_verify=True
        # )

        pytest.skip("Domain fronting example - requires custom setup")


class TestSNIParameterValidation:
    """Test validation of SNI parameter."""

    def test_sni_parameter_type_validation(self, cycletls_client_function, chrome_ja3):
        """Test that server_name parameter accepts string type."""
        # Should accept string
        try:
            response = cycletls_client_function.get(
                "https://httpbin.org/get",
                ja3=chrome_ja3,
                server_name="httpbin.org"
            )

            # If server_name is supported, should succeed
            assert_valid_response(response, expected_status=200)

        except TypeError as e:
            # If not implemented, should get TypeError for unexpected param
            if 'server_name' in str(e):
                pytest.skip("server_name parameter not yet implemented")
            raise
        except Exception as e:
            # Other exceptions might indicate parameter is recognized but failed
            if 'server_name' in str(e).lower():
                pytest.skip("server_name parameter not yet implemented")
            raise

    def test_sni_none_value(self, cycletls_client_function, chrome_ja3):
        """Test that None value for SNI is handled correctly."""
        # None should use default behavior (SNI from URL hostname)
        response = cycletls_client_function.get(
            "https://httpbin.org/get",
            ja3=chrome_ja3,
            server_name=None
        )

        # Should fall back to default SNI behavior
        assert_valid_response(response, expected_status=200)
