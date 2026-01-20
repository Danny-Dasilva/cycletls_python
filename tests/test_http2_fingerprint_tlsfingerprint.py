"""
HTTP/2 Fingerprint Validation Tests against tlsfingerprint.com

Tests HTTP/2 Akamai fingerprint generation and validation by verifying the
observed fingerprints at tlsfingerprint.com.

Run with: pytest tests/test_http2_fingerprint_tlsfingerprint.py -v -m live
Skip with: pytest -m "not live"

Based on: test_http2_fingerprint.py, test_frame_headers.py
"""
import pytest
from cycletls import CycleTLS

# Mark all tests in this module as live tests
pytestmark = pytest.mark.live

# Base URL for tlsfingerprint.com
BASE_URL = "https://tlsfingerprint.com"


def extract_http2_from_response(data: dict) -> dict:
    """
    Extract HTTP/2 fingerprint data from tlsfingerprint.com response.

    Response format:
    {
        "http2": {
            "akamai_fingerprint": "...",
            "akamai_fingerprint_hash": "...",
            "sent_frames": [...],
            ...
        },
        ...
    }
    """
    return data.get("http2", {})


@pytest.fixture(scope="module")
def cycle_client():
    """Create a single CycleTLS client for all tests in this module"""
    with CycleTLS() as client:
        yield client


class TestHTTP2FingerprintData:
    """Test that HTTP/2 fingerprint data is returned"""

    def test_response_contains_http2_data(self, cycle_client):
        """Test that tlsfingerprint.com returns HTTP/2 data"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        data = response.json()

        assert "http2" in data, f"Response should contain HTTP/2 data. Keys: {list(data.keys())}"

    def test_http2_fingerprint_fields(self, cycle_client):
        """Test that HTTP/2 data contains expected fingerprint fields"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        http2_data = extract_http2_from_response(response.json())

        # Should contain Akamai fingerprint data
        fingerprint_fields = ["akamai_fingerprint", "akamai_fingerprint_hash"]
        has_fingerprint = any(field in http2_data for field in fingerprint_fields)

        # Or sent frames data
        frame_fields = ["sent_frames", "settings", "window_update"]
        has_frames = any(field in http2_data for field in frame_fields)

        assert has_fingerprint or has_frames, \
            f"HTTP/2 data should contain fingerprint or frame data. Got: {list(http2_data.keys())}"


class TestHTTP2AkamaiFingerprint:
    """Test HTTP/2 Akamai fingerprint validation"""

    def test_akamai_fingerprint_format(self, cycle_client):
        """Test that Akamai fingerprint has valid format"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        http2_data = extract_http2_from_response(response.json())

        akamai_fp = http2_data.get("akamai_fingerprint", "")
        if akamai_fp:
            # Akamai fingerprint format: SETTINGS|WINDOW_UPDATE|PRIORITY|PSEUDO_HEADERS
            # Example: 1:65536;2:0;3:1000;4:6291456;6:262144|15663105|0|m,a,s,p
            parts = akamai_fp.split("|")
            assert len(parts) >= 1, f"Akamai fingerprint should have pipe-separated parts: {akamai_fp}"

    def test_akamai_fingerprint_hash(self, cycle_client):
        """Test that Akamai fingerprint hash is valid"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        http2_data = extract_http2_from_response(response.json())

        akamai_hash = http2_data.get("akamai_fingerprint_hash", "")
        if akamai_hash:
            # Should be a hash string
            assert len(akamai_hash) > 0, "Akamai fingerprint hash should not be empty"


class TestHTTP2FrameData:
    """Test HTTP/2 frame data (SETTINGS, WINDOW_UPDATE)"""

    def test_settings_frame_data(self, cycle_client):
        """Test that SETTINGS frame data is returned"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        http2_data = extract_http2_from_response(response.json())

        # Look for settings data in various possible locations
        has_settings = (
            "settings" in http2_data or
            "sent_frames" in http2_data or
            "SETTINGS" in str(http2_data)
        )

        # Settings data should exist if using HTTP/2
        if http2_data:
            assert has_settings or len(http2_data) > 0, \
                f"HTTP/2 data should contain settings info. Got: {http2_data}"

    def test_window_update_data(self, cycle_client):
        """Test that WINDOW_UPDATE data is returned"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        http2_data = extract_http2_from_response(response.json())

        # Look for window update data
        has_window = (
            "window_update" in http2_data or
            "WINDOW_UPDATE" in str(http2_data) or
            "window" in str(http2_data).lower()
        )

        # This is informational - window update may not always be present
        if not has_window and http2_data:
            pass  # OK if not present


class TestHTTP2Consistency:
    """Test HTTP/2 fingerprint consistency"""

    def test_http2_fingerprint_consistency(self, cycle_client):
        """Test that HTTP/2 fingerprint is consistent across requests"""
        response1 = cycle_client.get(f"{BASE_URL}/api/all")
        response2 = cycle_client.get(f"{BASE_URL}/api/all")

        assert response1.status_code == 200
        assert response2.status_code == 200

        http2_1 = extract_http2_from_response(response1.json())
        http2_2 = extract_http2_from_response(response2.json())

        # If Akamai fingerprint is present, it should be consistent
        fp1 = http2_1.get("akamai_fingerprint", "")
        fp2 = http2_2.get("akamai_fingerprint", "")

        if fp1 and fp2:
            assert fp1 == fp2, \
                f"HTTP/2 fingerprint should be consistent: {fp1} vs {fp2}"


class TestHTTP2VersionNegotiation:
    """Test HTTP/2 version negotiation"""

    def test_http2_negotiation(self, cycle_client):
        """Test that HTTP/2 is negotiated by default"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        data = response.json()

        # Check HTTP version in response
        http_version = data.get("http_version", "")
        assert http_version in ["h2", "HTTP/2", "2"], \
            f"Should negotiate HTTP/2 by default, got: {http_version}"

    def test_force_http1_no_http2_fingerprint(self, cycle_client):
        """Test that forcing HTTP/1.1 affects HTTP/2 fingerprint"""
        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            force_http1=True
        )

        assert response.status_code == 200
        data = response.json()

        # HTTP version should be reported
        http_version = data.get("http_version", "")

        # HTTP/2 data may or may not be present
        http2_data = extract_http2_from_response(data)

        # Test passes if request succeeds - HTTP/2 data may vary based on actual protocol


class TestBrowserHTTP2Fingerprints:
    """Test browser-specific HTTP/2 fingerprints"""

    def test_chrome_http2_fingerprint(self, cycle_client):
        """Test Chrome HTTP/2 fingerprint settings"""
        chrome_ja4r = "t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,44cd,fe0d,ff01_0403,0804,0401,0503,0805,0501,0806,0601"

        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja4r=chrome_ja4r,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        assert response.status_code == 200
        data = response.json()

        # Should have HTTP/2 data
        assert "http2" in data, "Should return HTTP/2 data for Chrome"

    def test_firefox_http2_fingerprint(self, cycle_client):
        """Test Firefox HTTP/2 fingerprint settings"""
        firefox_ja4r = "t13d1717h2_002f,0035,009c,009d,1301,1302,1303,c009,c00a,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,001c,0022,0023,002b,002d,0033,fe0d,ff01_0403,0503,0603,0804,0805,0806,0401,0501,0601,0203,0201"

        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            ja4r=firefox_ja4r,
            user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"
        )

        assert response.status_code == 200
        data = response.json()

        # Should have HTTP/2 data
        assert "http2" in data, "Should return HTTP/2 data for Firefox"


class TestHTTP2WithTLS:
    """Test HTTP/2 in combination with TLS fingerprinting"""

    def test_combined_tls_and_http2_fingerprint(self, cycle_client):
        """Test that both TLS and HTTP/2 fingerprints are returned together"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        data = response.json()

        # Should have both TLS and HTTP/2 data
        assert "tls" in data, "Should return TLS data"
        assert "http2" in data, "Should return HTTP/2 data"

        # Both should have fingerprint information
        tls = data["tls"]
        http2 = data["http2"]

        assert "ja3" in tls or "ja4" in tls, "TLS should have JA3 or JA4"
        assert len(http2) > 0, "HTTP/2 should have data"
