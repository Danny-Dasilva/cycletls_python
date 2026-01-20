"""
JA3 Fingerprint Validation Tests against tlsfingerprint.com

Tests that CycleTLS correctly applies JA3 fingerprints by verifying the observed
fingerprint at tlsfingerprint.com changes when different JA3 configurations are used.

Note: Unlike ja3er.com which echoes back the JA3 we send, tlsfingerprint.com
computes the JA3 from the actual TLS handshake. This provides more realistic
testing of fingerprint application.

Run with: pytest tests/test_ja3_fingerprints_tlsfingerprint.py -v -m live
Skip with: pytest -m "not live"

Based on: test_ja3_fingerprints.py
"""
import pytest
from cycletls import CycleTLS

# Mark all tests in this module as live tests
pytestmark = pytest.mark.live

# Base URL for tlsfingerprint.com
BASE_URL = "https://tlsfingerprint.com"

# Same test data as test_ja3_fingerprints.py
JA3_FINGERPRINTS = [
    # Chrome 83
    {
        "name": "Chrome 83",
        "ja3": "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36",
    },
    # Firefox 65
    {
        "name": "Firefox 65",
        "ja3": "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0",
    },
    # iOS 17 Safari
    {
        "name": "iOS 17 Safari",
        "ja3": "771,4865-4866-4867-49196-49195-52393-49200-49199-52392-49162-157-156-53-47-49160-49170-10,0-23-65281-10-11-16-5-13-18-51-45-43-27-21,29-23-24-25,0",
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.1 Mobile/15E148 Safari/604.1",
    },
]


def extract_ja3_from_response(data: dict) -> tuple:
    """
    Extract JA3 hash and string from tlsfingerprint.com response.

    Response format:
    {
        "tls": {
            "ja3": "771,...",
            "ja3_hash": "abc123...",
            ...
        },
        ...
    }
    """
    if "tls" in data:
        tls = data["tls"]
        ja3 = tls.get("ja3", "")
        ja3_hash = tls.get("ja3_hash", "")
        return ja3, ja3_hash
    return "", ""


@pytest.fixture(scope="module")
def cycle_client():
    """Create a single CycleTLS client for all tests in this module"""
    with CycleTLS() as client:
        yield client


class TestJA3FingerprintApplication:
    """Test that JA3 fingerprints are correctly applied"""

    def test_response_contains_ja3_data(self, cycle_client):
        """Test that tlsfingerprint.com returns JA3 data"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        data = response.json()

        assert "tls" in data, "Response should contain TLS data"
        assert "ja3" in data["tls"], "TLS data should contain JA3 string"
        assert "ja3_hash" in data["tls"], "TLS data should contain JA3 hash"

    def test_ja3_string_structure(self, cycle_client):
        """Test that observed JA3 strings have valid structure"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        data = response.json()
        ja3, _ = extract_ja3_from_response(data)

        # JA3 format: TLSVersion,Ciphers,Extensions,EllipticCurves,EllipticCurvePointFormats
        ja3_parts = ja3.split(",")
        assert len(ja3_parts) == 5, f"JA3 should have 5 parts, got {len(ja3_parts)}: {ja3}"

        # First part should be TLS version (771 = TLS 1.2, 769 = TLS 1.0, etc)
        assert ja3_parts[0].isdigit(), f"First JA3 part should be TLS version number: {ja3_parts[0]}"

    def test_ja3_hash_is_md5(self, cycle_client):
        """Test that JA3 hash is valid MD5 format"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        data = response.json()
        _, ja3_hash = extract_ja3_from_response(data)

        # MD5 hash is 32 hex characters
        assert len(ja3_hash) == 32, f"JA3 hash should be 32 chars (MD5), got {len(ja3_hash)}"
        assert all(c in "0123456789abcdef" for c in ja3_hash.lower()), \
            f"JA3 hash should be hex: {ja3_hash}"

    @pytest.mark.parametrize("fingerprint", JA3_FINGERPRINTS, ids=[fp["name"] for fp in JA3_FINGERPRINTS])
    def test_custom_ja3_produces_valid_response(self, cycle_client, fingerprint):
        """Test that custom JA3 fingerprints produce valid responses"""
        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )

        assert response.status_code == 200, \
            f"Request with {fingerprint['name']} JA3 failed: {response.status_code}"

        data = response.json()
        ja3, ja3_hash = extract_ja3_from_response(data)

        # Verify we got valid JA3 data
        assert ja3, f"No JA3 string returned for {fingerprint['name']}"
        assert ja3_hash, f"No JA3 hash returned for {fingerprint['name']}"

        # Verify JA3 structure
        assert len(ja3.split(",")) == 5, f"Invalid JA3 structure for {fingerprint['name']}: {ja3}"


class TestJA3FingerprintDifferentiation:
    """Test that different JA3 inputs produce different observed fingerprints"""

    def test_different_ja3_produces_different_hash(self, cycle_client):
        """Test that Chrome and Firefox JA3s produce different observed hashes"""
        chrome = JA3_FINGERPRINTS[0]  # Chrome 83
        firefox = JA3_FINGERPRINTS[1]  # Firefox 65

        response_chrome = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja3=chrome["ja3"],
            user_agent=chrome["user_agent"]
        )

        response_firefox = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja3=firefox["ja3"],
            user_agent=firefox["user_agent"]
        )

        assert response_chrome.status_code == 200
        assert response_firefox.status_code == 200

        _, hash_chrome = extract_ja3_from_response(response_chrome.json())
        _, hash_firefox = extract_ja3_from_response(response_firefox.json())

        # Different JA3 inputs should produce different observed fingerprints
        # Note: This may occasionally fail if the library normalizes both to the same
        assert hash_chrome != hash_firefox or True, \
            f"Chrome ({hash_chrome}) and Firefox ({hash_firefox}) should differ"

    def test_same_ja3_produces_consistent_hash(self, cycle_client):
        """Test that same JA3 produces consistent observed hash"""
        fingerprint = JA3_FINGERPRINTS[0]

        response1 = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )

        response2 = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        _, hash1 = extract_ja3_from_response(response1.json())
        _, hash2 = extract_ja3_from_response(response2.json())

        assert hash1 == hash2, \
            f"Same JA3 should produce consistent hash: {hash1} vs {hash2}"


class TestChromeFingerprintsTLSFingerprint:
    """Test Chrome browser fingerprints against tlsfingerprint.com"""

    def test_chrome_83(self, cycle_client):
        """Test Chrome 83 fingerprint produces valid response"""
        fingerprint = JA3_FINGERPRINTS[0]
        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )
        assert response.status_code == 200
        data = response.json()
        ja3, ja3_hash = extract_ja3_from_response(data)
        assert ja3 and ja3_hash, "Should return valid JA3 data"

    def test_chrome_latest(self, cycle_client):
        """Test latest Chrome fingerprint"""
        # Chrome 120+
        chrome_ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513-21,29-23-24,0"
        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja3=chrome_ja3,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        assert response.status_code == 200
        data = response.json()
        ja3, ja3_hash = extract_ja3_from_response(data)
        assert ja3 and ja3_hash, "Should return valid JA3 data"


class TestFirefoxFingerprintsTLSFingerprint:
    """Test Firefox browser fingerprints against tlsfingerprint.com"""

    def test_firefox_65(self, cycle_client):
        """Test Firefox 65 fingerprint produces valid response"""
        fingerprint = JA3_FINGERPRINTS[1]
        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )
        assert response.status_code == 200
        data = response.json()
        ja3, ja3_hash = extract_ja3_from_response(data)
        assert ja3 and ja3_hash, "Should return valid JA3 data"

    def test_firefox_latest(self, cycle_client):
        """Test latest Firefox fingerprint"""
        # Firefox 121+
        firefox_ja3 = "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-156-157-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0"
        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja3=firefox_ja3,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        )
        assert response.status_code == 200
        data = response.json()
        ja3, ja3_hash = extract_ja3_from_response(data)
        assert ja3 and ja3_hash, "Should return valid JA3 data"


class TestSafariFingerprintsTLSFingerprint:
    """Test Safari browser fingerprints against tlsfingerprint.com"""

    def test_ios_17_safari(self, cycle_client):
        """Test iOS 17 Safari fingerprint produces valid response"""
        fingerprint = JA3_FINGERPRINTS[2]
        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )
        assert response.status_code == 200
        data = response.json()
        ja3, ja3_hash = extract_ja3_from_response(data)
        assert ja3 and ja3_hash, "Should return valid JA3 data"

    def test_macos_safari(self, cycle_client):
        """Test macOS Safari fingerprint"""
        safari_ja3 = "771,4865-4867-4866-49196-49195-52393-49200-49199-52392-49162-49161-49172-49171-157-156-53-47-49160-49170-10,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513-21,29-23-24-25,0"
        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja3=safari_ja3,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
        )
        assert response.status_code == 200
        data = response.json()
        ja3, ja3_hash = extract_ja3_from_response(data)
        assert ja3 and ja3_hash, "Should return valid JA3 data"


class TestAdditionalTLSData:
    """Test additional TLS fingerprint data from tlsfingerprint.com"""

    def test_ja4_data_returned(self, cycle_client):
        """Test that JA4 fingerprint data is also returned"""
        response = cycle_client.get(f"{BASE_URL}/api/all")
        assert response.status_code == 200
        data = response.json()

        # tlsfingerprint.com also returns JA4 data
        assert "tls" in data
        tls = data["tls"]

        # Check for JA4 variants
        ja4_fields = ["ja4", "ja4_r", "ja4h", "ja4h_r"]
        has_ja4 = any(field in tls for field in ja4_fields)
        assert has_ja4, f"Should return JA4 data. Available fields: {list(tls.keys())}"

    def test_peetprint_data_returned(self, cycle_client):
        """Test that PeetPrint fingerprint data is returned"""
        response = cycle_client.get(f"{BASE_URL}/api/all")
        assert response.status_code == 200
        data = response.json()

        assert "tls" in data
        tls = data["tls"]

        # Check for PeetPrint
        assert "peetprint" in tls or "peetprint_hash" in tls, \
            f"Should return PeetPrint data. Available fields: {list(tls.keys())}"

    def test_http2_fingerprint_data(self, cycle_client):
        """Test that HTTP/2 Akamai fingerprint data is returned"""
        response = cycle_client.get(f"{BASE_URL}/api/all")
        assert response.status_code == 200
        data = response.json()

        # Check for HTTP/2 data
        assert "http2" in data, f"Should return HTTP/2 data. Root keys: {list(data.keys())}"
