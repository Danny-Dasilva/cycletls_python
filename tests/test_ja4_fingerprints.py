"""
JA4 Fingerprint Tests

Tests for JA4 fingerprinting functionality including JA4_r raw format parsing,
custom JA4_r parameters, and comparison with JA3 fingerprints.

Based on: /Users/dannydasilva/Documents/personal/CycleTLS/tests/ja4-fingerprint.test.js
"""
import os

import pytest

# Structural JA4_r matchers live in tests/conftest.py so they can be reused by
# test_tlsfingerprint_blocking.py. See conftest for full rationale on why we
# match structure rather than exact strings (production tls.peet.ws strips
# leading zeros in the cipher_count/ext_count header field).
from conftest import (
    assert_ja4r_equivalent as _assert_ja4r_equivalent,
)
from conftest import (
    parse_ja4r as _parse_ja4r,
)

from cycletls import CycleTLS

_TLSFP_URL = os.environ.get("TLSFP_URL", "https://tls.peet.ws")

pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def cycle_client():
    """Create a single CycleTLS client for all tests in this module with connection reuse disabled."""
    with CycleTLS() as client:
        _orig = client.request
        def _no_reuse(method, url, **kwargs):
            kwargs.setdefault("enable_connection_reuse", False)
            return _orig(method, url, **kwargs)
        client.request = _no_reuse
        yield client


class TestJA4Fingerprints:
    """Test suite for JA4 fingerprint validation"""

    def test_firefox_ja4r_exact_match(self, cycle_client):
        """
        Test Firefox JA4_r fingerprint exact match.

        Validates that custom JA4_r fingerprint is correctly applied and returned,
        including preservation of special extensions like ECH (fe0d) and
        Delegated Credentials (0022).
        """
        firefox_ja4r = "t13d1717h2_002f,0035,009c,009d,1301,1302,1303,c009,c00a,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,001c,0022,0023,002b,002d,0033,fe0d,ff01_0403,0503,0603,0804,0805,0806,0401,0501,0601,0203,0201"

        response = cycle_client.get(
            f"{_TLSFP_URL}/api/all",
            ja4r=firefox_ja4r,
            disable_grease=False,
            user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0'
        )

        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

        result = response.json()

        # Validate JA4_r response and HTTP/2 negotiation
        assert "tls" in result, "Response should contain 'tls' field"
        assert "ja4_r" in result["tls"], "TLS data should contain 'ja4_r' field"
        assert result.get("http_version") == "h2", f"Expected HTTP/2, got {result.get('http_version')}"

        # Check for ECH extension (fe0d) preservation
        assert "fe0d" in result["tls"]["ja4_r"], "JA4_r should contain ECH extension (fe0d)"

        # Check for Delegated Credentials (0022)
        assert "0022" in result["tls"]["ja4_r"], "JA4_r should contain Delegated Credentials (0022)"

        # Validate structure: TLS 1.3, h2 ALPN, 17 ciphers + 17 extensions.
        # Accept both unpadded ("t13d1717h2") and zero-padded ("t13d1717h2"
        # which already happens to coincide here) header forms.
        parsed = _parse_ja4r(result["tls"]["ja4_r"])
        assert parsed["tls_version"] == "13"
        assert parsed["alpn"] == "h2"
        assert parsed["header_cipher_count"] == 17
        assert parsed["header_ext_count"] == 17

        # Verify the cipher / extension / signature-algorithm bodies match
        # exactly. Header padding is allowed to differ between servers.
        _assert_ja4r_equivalent(result["tls"]["ja4_r"], firefox_ja4r)

    def test_chrome_ja4r_exact_match(self, cycle_client):
        """
        Test Chrome JA4_r fingerprint exact match.

        Validates Chrome's JA4_r fingerprint including ALPS (44cd) and
        ECH (fe0d) extensions.
        """
        chrome_ja4r = "t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,44cd,fe0d,ff01_0403,0804,0401,0503,0805,0501,0806,0601"

        response = cycle_client.get(
            f"{_TLSFP_URL}/api/all",
            ja4r=chrome_ja4r,
            disable_grease=False,
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        )

        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

        result = response.json()

        # Validate JA4_r response and HTTP/2 negotiation
        assert "tls" in result, "Response should contain 'tls' field"
        assert "ja4_r" in result["tls"], "TLS data should contain 'ja4_r' field"
        assert result.get("http_version") == "h2", f"Expected HTTP/2, got {result.get('http_version')}"

        # Check for ALPS extension (44cd)
        assert "44cd" in result["tls"]["ja4_r"], "JA4_r should contain ALPS extension (44cd)"

        # Check for ECH extension (fe0d)
        assert "fe0d" in result["tls"]["ja4_r"], "JA4_r should contain ECH extension (fe0d)"

        # Validate structure: TLS 1.3, h2 ALPN, 15 ciphers + 16 extensions.
        parsed = _parse_ja4r(result["tls"]["ja4_r"])
        assert parsed["tls_version"] == "13"
        assert parsed["alpn"] == "h2"
        assert parsed["header_cipher_count"] == 15
        assert parsed["header_ext_count"] == 16

        # Verify body match (ALPN is auto-handled with h2). Header padding
        # may differ across servers but ciphers/extensions/sigalgs are stable.
        _assert_ja4r_equivalent(result["tls"]["ja4_r"], chrome_ja4r)

    def test_chrome_138_ja4r_exact_match(self, cycle_client):
        """
        Test Chrome 138 JA4_r exact match.

        Validates Chrome 138's specific JA4_r fingerprint.
        """
        chrome138_ja4r = "t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,44cd,fe0d,ff01_0403,0804,0401,0503,0805,0501,0806,0601"

        response = cycle_client.get(
            f"{_TLSFP_URL}/api/all",
            ja4r=chrome138_ja4r,
            disable_grease=False,
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        )

        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

        result = response.json()

        # Validate JA4_r response and HTTP/2 negotiation
        assert "tls" in result, "Response should contain 'tls' field"
        assert "ja4_r" in result["tls"], "TLS data should contain 'ja4_r' field"
        assert result.get("http_version") == "h2", f"Expected HTTP/2, got {result.get('http_version')}"

        # Check for ALPS extension (44cd)
        assert "44cd" in result["tls"]["ja4_r"], "JA4_r should contain ALPS extension (44cd)"

        # Check for ECH extension (fe0d)
        assert "fe0d" in result["tls"]["ja4_r"], "JA4_r should contain ECH extension (fe0d)"

        # Validate structure: TLS 1.3, h2 ALPN, 15 ciphers + 16 extensions.
        parsed = _parse_ja4r(result["tls"]["ja4_r"])
        assert parsed["tls_version"] == "13"
        assert parsed["alpn"] == "h2"
        assert parsed["header_cipher_count"] == 15
        assert parsed["header_ext_count"] == 16

        # Body equivalence: cipher / extension / sigalg lists match exactly.
        _assert_ja4r_equivalent(result["tls"]["ja4_r"], chrome138_ja4r)

    def test_chrome_139_ja4r_exact_match(self, cycle_client):
        """
        Test Chrome 139 JA4_r exact match.

        Validates Chrome 139's specific JA4_r fingerprint.
        """
        chrome139_ja4r = "t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,44cd,fe0d,ff01_0403,0804,0401,0503,0805,0501,0806,0601"

        response = cycle_client.get(
            f"{_TLSFP_URL}/api/all",
            ja4r=chrome139_ja4r,
            disable_grease=False,
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
        )

        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

        result = response.json()

        # Validate JA4_r response and HTTP/2 negotiation
        assert "tls" in result, "Response should contain 'tls' field"
        assert "ja4_r" in result["tls"], "TLS data should contain 'ja4_r' field"
        assert result.get("http_version") == "h2", f"Expected HTTP/2, got {result.get('http_version')}"

        # Check for ALPS extension (44cd)
        assert "44cd" in result["tls"]["ja4_r"], "JA4_r should contain ALPS extension (44cd)"

        # Check for ECH extension (fe0d)
        assert "fe0d" in result["tls"]["ja4_r"], "JA4_r should contain ECH extension (fe0d)"

        # Validate structure: TLS 1.3, h2 ALPN, 15 ciphers + 16 extensions.
        parsed = _parse_ja4r(result["tls"]["ja4_r"])
        assert parsed["tls_version"] == "13"
        assert parsed["alpn"] == "h2"
        assert parsed["header_cipher_count"] == 15
        assert parsed["header_ext_count"] == 16

        # Body equivalence: cipher / extension / sigalg lists match exactly.
        _assert_ja4r_equivalent(result["tls"]["ja4_r"], chrome139_ja4r)

    def test_tls12_ja4r_exact_match(self, cycle_client):
        """
        Test TLS 1.2 JA4_r fingerprint exact match.

        Validates that TLS 1.2 fingerprints are correctly handled with
        proper format (t12d128h2 with 8 extensions).
        """
        tls12_ja4r = "t12d128h2_002f,0035,009c,009d,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0017,0023,ff01_0403,0804,0401,0503,0805,0501,0806,0601,0201"

        response = cycle_client.get(
            f"{_TLSFP_URL}/api/all",
            ja4r=tls12_ja4r,
            disable_grease=False,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )

        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

        result = response.json()

        # Validate TLS 1.2 negotiation and JA4_r
        assert "tls" in result, "Response should contain 'tls' field"
        assert "ja4_r" in result["tls"], "TLS data should contain 'ja4_r' field"
        assert result.get("http_version") == "h2", f"Expected HTTP/2, got {result.get('http_version')}"

        # Validate structure: TLS 1.2, h2 ALPN, 12 ciphers + 8 extensions.
        # Production tls.peet.ws emits the unpadded "t12d128h2" form, while
        # local tlsfingerprint.com Docker emits the spec-compliant
        # zero-padded "t12d1208h2" form. Both are accepted.
        parsed = _parse_ja4r(result["tls"]["ja4_r"])
        assert parsed["tls_version"] == "12", (
            f"Expected TLS 1.2, got version {parsed['tls_version']!r} "
            f"in {result['tls']['ja4_r']!r}"
        )
        assert parsed["alpn"] == "h2"
        assert parsed["header_cipher_count"] == 12
        assert parsed["header_ext_count"] == 8

        # Body equivalence: cipher / extension / sigalg lists match exactly.
        _assert_ja4r_equivalent(result["tls"]["ja4_r"], tls12_ja4r)


class TestJA4RawFormatParsing:
    """Test JA4_r raw format parsing and structure validation"""

    def test_ja4r_structure_validation(self, cycle_client):
        """
        Test that JA4_r strings have the expected structure.

        JA4_r format: <TLS_version>d<cipher_count><extension_count><ALPN>_<ciphers>_<extensions>_<signature_algorithms>
        Example: t13d1516h2_002f,0035,..._0005,000a,..._0403,0804,...
        """
        chrome_ja4r = "t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,44cd,fe0d,ff01_0403,0804,0401,0503,0805,0501,0806,0601"

        response = cycle_client.get(
            f"{_TLSFP_URL}/api/all",
            ja4r=chrome_ja4r,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        assert response.status_code == 200
        result = response.json()

        ja4_r = result["tls"]["ja4_r"]

        # Verify JA4_r contains 4 underscore-separated parts
        parts = ja4_r.split("_")
        assert len(parts) == 4, f"JA4_r should have 4 underscore-separated parts, got {len(parts)}"

        # Verify header format
        header = parts[0]
        assert header.startswith("t"), "JA4_r header should start with 't' (TLS)"
        assert "d" in header, "JA4_r header should contain 'd' separator"
        assert "h2" in header or "h1" in header, "JA4_r header should specify ALPN (h2 or h1)"

        # Verify ciphers are comma-separated
        ciphers = parts[1].split(",")
        assert len(ciphers) > 0, "JA4_r should contain at least one cipher"

        # Verify extensions are comma-separated
        extensions = parts[2].split(",")
        assert len(extensions) > 0, "JA4_r should contain at least one extension"

        # Verify signature algorithms are comma-separated
        sig_algs = parts[3].split(",")
        assert len(sig_algs) > 0, "JA4_r should contain at least one signature algorithm"

    def test_ja4r_tls_version_parsing(self, cycle_client):
        """Test that different TLS versions are correctly parsed in JA4_r"""
        # TLS 1.3
        tls13_ja4r = "t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,44cd,fe0d,ff01_0403,0804,0401,0503,0805,0501,0806,0601"

        response = cycle_client.get(
            f"{_TLSFP_URL}/api/all",
            ja4r=tls13_ja4r,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            enable_connection_reuse=False  # Disable connection reuse when switching fingerprints
        )

        assert response.status_code == 200
        result = response.json()
        assert result["tls"]["ja4_r"].startswith("t13"), "TLS 1.3 JA4_r should start with 't13'"

        # TLS 1.2
        tls12_ja4r = "t12d128h2_002f,0035,009c,009d,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0017,0023,ff01_0403,0804,0401,0503,0805,0501,0806,0601,0201"

        response = cycle_client.get(
            f"{_TLSFP_URL}/api/all",
            ja4r=tls12_ja4r,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            enable_connection_reuse=False  # Disable connection reuse when switching fingerprints
        )

        assert response.status_code == 200
        result = response.json()
        assert result["tls"]["ja4_r"].startswith("t12"), "TLS 1.2 JA4_r should start with 't12'"


class TestJA4vsJA3Comparison:
    """Compare JA4 and JA3 fingerprinting approaches"""

    def test_ja4_vs_ja3_same_browser(self, cycle_client):
        """
        Test that JA4 and JA3 can both be used for the same browser.

        JA4 is more detailed and includes raw TLS data, while JA3 provides
        a simpler hash-based approach.
        """
        # Chrome fingerprints
        chrome_ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"
        chrome_ja4r = "t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,44cd,fe0d,ff01_0403,0804,0401,0503,0805,0501,0806,0601"
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        # Test with JA3
        response_ja3 = cycle_client.get(
            f"{_TLSFP_URL}/api/clean",
            ja3=chrome_ja3,
            user_agent=user_agent
        )

        # Test with JA4R
        response_ja4 = cycle_client.get(
            f"{_TLSFP_URL}/api/all",
            ja4r=chrome_ja4r,
            user_agent=user_agent
        )

        # Both should succeed
        assert response_ja3.status_code == 200, "JA3 request should succeed"
        assert response_ja4.status_code == 200, "JA4 request should succeed"

        # Verify JA3 response
        ja3_data = response_ja3.json()
        assert "ja3_hash" in ja3_data, "JA3 response should contain ja3_hash"
        assert ja3_data["ja3"] == chrome_ja3, "JA3 string should match"

        # Verify JA4 response
        ja4_data = response_ja4.json()
        assert "tls" in ja4_data, "JA4 response should contain tls data"
        assert "ja4_r" in ja4_data["tls"], "TLS data should contain ja4_r"

    def test_ja4_provides_more_detail_than_ja3(self, cycle_client):
        """
        Test that JA4 provides more detailed fingerprinting than JA3.

        JA4_r includes raw cipher suites, extensions, and signature algorithms
        in their original hex format, while JA3 only provides numeric codes.
        """
        chrome_ja4r = "t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,44cd,fe0d,ff01_0403,0804,0401,0503,0805,0501,0806,0601"

        response = cycle_client.get(
            f"{_TLSFP_URL}/api/all",
            ja4r=chrome_ja4r,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            enable_connection_reuse=False  # Disable connection reuse to avoid stale connections
        )

        assert response.status_code == 200
        result = response.json()

        ja4_r = result["tls"]["ja4_r"]

        # JA4_r should contain specific extension codes that provide more detail
        # ALPS extension (44cd) - not present in older browsers
        assert "44cd" in ja4_r, "JA4_r should preserve ALPS extension (44cd)"

        # ECH extension (fe0d) - shows support for Encrypted Client Hello
        assert "fe0d" in ja4_r, "JA4_r should preserve ECH extension (fe0d)"

        # These details are lost in JA3's hash-based approach
        # JA4 provides more granular control and inspection capability


class TestCustomJA4RParameter:
    """Test using custom JA4_r parameter for advanced fingerprinting"""

    def test_custom_ja4r_with_specific_extensions(self, cycle_client):
        """Test that custom JA4_r parameters are correctly applied"""
        # Create a custom JA4_r with specific extensions
        custom_ja4r = "t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,44cd,fe0d,ff01_0403,0804,0401,0503,0805,0501,0806,0601"

        response = cycle_client.get(
            f"{_TLSFP_URL}/api/all",
            ja4r=custom_ja4r,
            disable_grease=False,
            user_agent='Custom User Agent'
        )

        assert response.status_code == 200
        result = response.json()

        # Verify the custom JA4_r was used (header padding may differ between
        # production tls.peet.ws and the local Docker server, so compare the
        # cipher / extension / sigalg bodies rather than the exact string).
        _assert_ja4r_equivalent(result["tls"]["ja4_r"], custom_ja4r)

    def test_ja4r_with_disable_grease(self, cycle_client):
        """Test JA4_r with GREASE disabled"""
        firefox_ja4r = "t13d1717h2_002f,0035,009c,009d,1301,1302,1303,c009,c00a,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,001c,0022,0023,002b,002d,0033,fe0d,ff01_0403,0503,0603,0804,0805,0806,0401,0501,0601,0203,0201"

        # Test with GREASE disabled - disable connection reuse when switching fingerprints
        response_no_grease = cycle_client.get(
            f"{_TLSFP_URL}/api/all",
            ja4r=firefox_ja4r,
            disable_grease=True,
            user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0',
            enable_connection_reuse=False  # Disable connection reuse when switching fingerprints
        )

        # Test with GREASE enabled - disable connection reuse when switching fingerprints
        response_with_grease = cycle_client.get(
            f"{_TLSFP_URL}/api/all",
            ja4r=firefox_ja4r,
            disable_grease=False,
            user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0',
            enable_connection_reuse=False  # Disable connection reuse when switching fingerprints
        )

        # Both should succeed
        assert response_no_grease.status_code == 200
        assert response_with_grease.status_code == 200

        # Both should return valid JA4_r data
        data_no_grease = response_no_grease.json()
        data_with_grease = response_with_grease.json()

        assert "tls" in data_no_grease
        assert "ja4_r" in data_no_grease["tls"]
        assert "tls" in data_with_grease
        assert "ja4_r" in data_with_grease["tls"]

    def test_multiple_ja4r_requests_consistency(self, cycle_client):
        """Test that multiple requests with same JA4_r produce consistent results"""
        chrome_ja4r = "t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,44cd,fe0d,ff01_0403,0804,0401,0503,0805,0501,0806,0601"

        # Make multiple requests with the same JA4_r
        # Disable connection reuse to avoid stale connections from previous tests
        response1 = cycle_client.get(
            f"{_TLSFP_URL}/api/all",
            ja4r=chrome_ja4r,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            enable_connection_reuse=False
        )

        response2 = cycle_client.get(
            f"{_TLSFP_URL}/api/all",
            ja4r=chrome_ja4r,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            enable_connection_reuse=False
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Verify consistency: the same server should produce identical
        # JA4_r strings across requests. Both responses should also be
        # structurally equivalent to the input fingerprint (header padding
        # may differ between servers but ciphers/extensions/sigalgs are stable).
        assert data1["tls"]["ja4_r"] == data2["tls"]["ja4_r"], \
            "Multiple requests with same JA4_r should return consistent results"
        _assert_ja4r_equivalent(data1["tls"]["ja4_r"], chrome_ja4r)
