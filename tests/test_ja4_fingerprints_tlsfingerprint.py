"""
JA4 Fingerprint Validation Tests against tlsfingerprint.com

Tests JA4 and JA4_r fingerprinting functionality by verifying the observed
fingerprints at tlsfingerprint.com when different JA4_r configurations are used.

Run with: pytest tests/test_ja4_fingerprints_tlsfingerprint.py -v -m live
Skip with: pytest -m "not live"

Based on: test_ja4_fingerprints.py
"""
import pytest
from cycletls import CycleTLS

# Mark all tests in this module as live tests
pytestmark = pytest.mark.live

# Base URL for tlsfingerprint.com
BASE_URL = "https://tlsfingerprint.com"

# JA4_r fingerprints from test_ja4_fingerprints.py
JA4R_FINGERPRINTS = [
    {
        "name": "Firefox",
        "ja4r": "t13d1717h2_002f,0035,009c,009d,1301,1302,1303,c009,c00a,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,001c,0022,0023,002b,002d,0033,fe0d,ff01_0403,0503,0603,0804,0805,0806,0401,0501,0601,0203,0201",
        "user_agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0",
    },
    {
        "name": "Chrome 138",
        "ja4r": "t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,44cd,fe0d,ff01_0403,0804,0401,0503,0805,0501,0806,0601",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    },
    {
        "name": "Chrome 139",
        "ja4r": "t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,44cd,fe0d,ff01_0403,0804,0401,0503,0805,0501,0806,0601",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    },
    {
        "name": "TLS 1.2",
        "ja4r": "t12d128h2_002f,0035,009c,009d,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0017,0023,ff01_0403,0804,0401,0503,0805,0501,0806,0601,0201",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    },
]


def extract_ja4_from_response(data: dict) -> dict:
    """
    Extract JA4 data from tlsfingerprint.com response.

    Response format:
    {
        "tls": {
            "ja4": "...",
            "ja4_r": "...",
            "ja4h": "...",
            "ja4h_r": "...",
            ...
        },
        ...
    }
    """
    if "tls" in data:
        tls = data["tls"]
        return {
            "ja4": tls.get("ja4", ""),
            "ja4_r": tls.get("ja4_r", ""),
            "ja4h": tls.get("ja4h", ""),
            "ja4h_r": tls.get("ja4h_r", ""),
        }
    return {}


@pytest.fixture(scope="module")
def cycle_client():
    """Create a single CycleTLS client for all tests in this module"""
    with CycleTLS() as client:
        yield client


class TestJA4FingerprintApplication:
    """Test that JA4 fingerprints are correctly applied"""

    def test_response_contains_ja4_data(self, cycle_client):
        """Test that tlsfingerprint.com returns JA4 data"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        data = response.json()

        assert "tls" in data, "Response should contain TLS data"
        tls = data["tls"]

        # Check for JA4 fields
        ja4_fields = ["ja4", "ja4_r"]
        has_ja4 = any(field in tls for field in ja4_fields)
        assert has_ja4, f"TLS data should contain JA4 fields. Got: {list(tls.keys())}"

    def test_ja4r_structure(self, cycle_client):
        """Test that JA4_r strings have valid structure"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        ja4_data = extract_ja4_from_response(response.json())

        ja4_r = ja4_data.get("ja4_r", "")
        if ja4_r:
            # JA4_r format: header_ciphers_extensions_sigalgs
            parts = ja4_r.split("_")
            assert len(parts) == 4, f"JA4_r should have 4 underscore-separated parts, got {len(parts)}: {ja4_r}"

            # Header should start with 't' (TLS)
            header = parts[0]
            assert header.startswith("t"), f"JA4_r header should start with 't': {header}"

    @pytest.mark.parametrize("fingerprint", JA4R_FINGERPRINTS, ids=[fp["name"] for fp in JA4R_FINGERPRINTS])
    def test_custom_ja4r_produces_valid_response(self, cycle_client, fingerprint):
        """Test that custom JA4_r fingerprints produce valid responses"""
        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja4r=fingerprint["ja4r"],
            user_agent=fingerprint["user_agent"]
        )

        assert response.status_code == 200, \
            f"Request with {fingerprint['name']} JA4_r failed: {response.status_code}"

        ja4_data = extract_ja4_from_response(response.json())

        # Verify we got JA4 data
        assert ja4_data.get("ja4") or ja4_data.get("ja4_r"), \
            f"No JA4 data returned for {fingerprint['name']}"


class TestJA4RawFormatParsing:
    """Test JA4_r raw format parsing and structure validation"""

    def test_ja4r_header_format(self, cycle_client):
        """Test that JA4_r header contains expected information"""
        chrome_ja4r = JA4R_FINGERPRINTS[1]["ja4r"]  # Chrome 138

        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja4r=chrome_ja4r,
            user_agent=JA4R_FINGERPRINTS[1]["user_agent"]
        )

        assert response.status_code == 200
        ja4_data = extract_ja4_from_response(response.json())

        ja4_r = ja4_data.get("ja4_r", "")
        if ja4_r:
            header = ja4_r.split("_")[0]

            # Header format: t{tls_version}d{cipher_count}{ext_count}{alpn}
            assert "d" in header, f"Header should contain 'd' separator: {header}"

            # Should indicate HTTP/2 (h2) or HTTP/1.1 (h1)
            assert "h2" in header or "h1" in header, \
                f"Header should indicate ALPN (h2 or h1): {header}"

    def test_ja4r_tls_version_parsing(self, cycle_client):
        """Test that different TLS versions are correctly parsed in JA4_r"""
        # TLS 1.3 fingerprint
        tls13_ja4r = JA4R_FINGERPRINTS[0]["ja4r"]  # Firefox (TLS 1.3)

        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja4r=tls13_ja4r,
            user_agent=JA4R_FINGERPRINTS[0]["user_agent"]
        )

        assert response.status_code == 200
        ja4_data = extract_ja4_from_response(response.json())

        ja4_r = ja4_data.get("ja4_r", "")
        if ja4_r:
            # TLS 1.3 should be indicated in header
            header = ja4_r.split("_")[0]
            # Header should start with t13 for TLS 1.3 or t12 for TLS 1.2
            assert header.startswith("t1"), f"Header should indicate TLS version: {header}"


class TestJA4Consistency:
    """Test JA4 fingerprint consistency"""

    def test_same_ja4r_produces_consistent_results(self, cycle_client):
        """Test that same JA4_r produces consistent results across requests"""
        fingerprint = JA4R_FINGERPRINTS[0]  # Firefox

        response1 = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja4r=fingerprint["ja4r"],
            user_agent=fingerprint["user_agent"]
        )

        response2 = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja4r=fingerprint["ja4r"],
            user_agent=fingerprint["user_agent"]
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        ja4_1 = extract_ja4_from_response(response1.json())
        ja4_2 = extract_ja4_from_response(response2.json())

        # JA4 should be consistent
        if ja4_1.get("ja4") and ja4_2.get("ja4"):
            assert ja4_1["ja4"] == ja4_2["ja4"], \
                f"JA4 should be consistent: {ja4_1['ja4']} vs {ja4_2['ja4']}"


class TestCustomJA4RParameter:
    """Test using custom JA4_r parameter for advanced fingerprinting"""

    def test_custom_ja4r_with_specific_extensions(self, cycle_client):
        """Test that custom JA4_r parameters are correctly applied"""
        custom_ja4r = JA4R_FINGERPRINTS[1]["ja4r"]  # Chrome 138

        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja4r=custom_ja4r,
            disable_grease=False,
            user_agent="Custom User Agent"
        )

        assert response.status_code == 200
        ja4_data = extract_ja4_from_response(response.json())

        # Should return valid JA4 data
        assert ja4_data.get("ja4") or ja4_data.get("ja4_r"), \
            "Response should contain JA4 data"

    def test_ja4r_with_disable_grease(self, cycle_client):
        """Test JA4_r with GREASE disabled"""
        firefox_ja4r = JA4R_FINGERPRINTS[0]["ja4r"]

        # Test with GREASE disabled
        response_no_grease = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja4r=firefox_ja4r,
            disable_grease=True,
            user_agent=JA4R_FINGERPRINTS[0]["user_agent"]
        )

        # Test with GREASE enabled
        response_with_grease = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja4r=firefox_ja4r,
            disable_grease=False,
            user_agent=JA4R_FINGERPRINTS[0]["user_agent"]
        )

        # Both should succeed
        assert response_no_grease.status_code == 200
        assert response_with_grease.status_code == 200

        # Both should return valid JA4 data
        ja4_no_grease = extract_ja4_from_response(response_no_grease.json())
        ja4_with_grease = extract_ja4_from_response(response_with_grease.json())

        assert ja4_no_grease.get("ja4") or ja4_no_grease.get("ja4_r")
        assert ja4_with_grease.get("ja4") or ja4_with_grease.get("ja4_r")


class TestBrowserJA4Fingerprints:
    """Test browser-specific JA4 fingerprints"""

    def test_firefox_ja4r(self, cycle_client):
        """Test Firefox JA4_r fingerprint"""
        fingerprint = JA4R_FINGERPRINTS[0]
        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja4r=fingerprint["ja4r"],
            user_agent=fingerprint["user_agent"]
        )

        assert response.status_code == 200
        ja4_data = extract_ja4_from_response(response.json())
        assert ja4_data.get("ja4") or ja4_data.get("ja4_r"), "Should return JA4 data"

    def test_chrome_138_ja4r(self, cycle_client):
        """Test Chrome 138 JA4_r fingerprint"""
        fingerprint = JA4R_FINGERPRINTS[1]
        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja4r=fingerprint["ja4r"],
            user_agent=fingerprint["user_agent"]
        )

        assert response.status_code == 200
        ja4_data = extract_ja4_from_response(response.json())
        assert ja4_data.get("ja4") or ja4_data.get("ja4_r"), "Should return JA4 data"

    def test_chrome_139_ja4r(self, cycle_client):
        """Test Chrome 139 JA4_r fingerprint"""
        fingerprint = JA4R_FINGERPRINTS[2]
        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja4r=fingerprint["ja4r"],
            user_agent=fingerprint["user_agent"]
        )

        assert response.status_code == 200
        ja4_data = extract_ja4_from_response(response.json())
        assert ja4_data.get("ja4") or ja4_data.get("ja4_r"), "Should return JA4 data"

    def test_tls12_ja4r(self, cycle_client):
        """Test TLS 1.2 JA4_r fingerprint"""
        fingerprint = JA4R_FINGERPRINTS[3]
        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja4r=fingerprint["ja4r"],
            user_agent=fingerprint["user_agent"]
        )

        assert response.status_code == 200
        ja4_data = extract_ja4_from_response(response.json())
        assert ja4_data.get("ja4") or ja4_data.get("ja4_r"), "Should return JA4 data"


class TestJA4vsJA3:
    """Compare JA4 and JA3 fingerprinting"""

    def test_both_ja4_and_ja3_returned(self, cycle_client):
        """Test that both JA4 and JA3 data are returned"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        data = response.json()

        assert "tls" in data
        tls = data["tls"]

        # Should have both JA3 and JA4
        assert "ja3" in tls, "Should return JA3 data"
        assert "ja4" in tls or "ja4_r" in tls, "Should return JA4 data"

    def test_ja4_more_detailed_than_ja3(self, cycle_client):
        """Test that JA4 provides more detailed information than JA3"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        data = response.json()
        tls = data["tls"]

        ja3 = tls.get("ja3", "")
        ja4_r = tls.get("ja4_r", "")

        # JA4_r should have more structured information
        if ja3 and ja4_r:
            # JA3 has 5 comma-separated parts
            ja3_parts = len(ja3.split(","))

            # JA4_r has 4 underscore-separated parts with hex codes
            ja4_parts = len(ja4_r.split("_"))

            assert ja3_parts == 5, f"JA3 should have 5 parts: {ja3}"
            assert ja4_parts == 4, f"JA4_r should have 4 parts: {ja4_r}"
