"""
JA3 Fingerprint Validation Tests

Tests various browser JA3 fingerprints against ja3er.com/json to verify
that CycleTLS correctly implements TLS fingerprinting for different browsers.

Based on: /Users/dannydasilva/Documents/personal/CycleTLS/cycletls/tests/integration/main_ja3_test.go
"""
import pytest
from cycletls import CycleTLS


# Test data structure matching the Go implementation
JA3_FINGERPRINTS = [
    # Chrome 58
    {
        "name": "Chrome 58",
        "ja3_hash": "bc6c386f480ee97b9d9e52d472b772d8",
        "ja3": "771,49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53-10,65281-0-23-35-13-5-18-16-11-10,29-23-24,0",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    },
    # Chrome 62
    {
        "name": "Chrome 62",
        "ja3_hash": "bc6c386f480ee97b9d9e52d472b772d8",
        "ja3": "771,49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53-10,65281-0-23-35-13-5-18-16-11-10,29-23-24,0",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3165.0 Safari/537.36",
    },
    # Chrome 70
    {
        "name": "Chrome 70",
        "ja3_hash": "b4918ee98d0f0deb4e48563ca749ef10",
        "ja3": "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53-10,65281-0-23-35-13-5-18-16-11-51-45-43-10-27-21,29-23-24,0",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36",
    },
    # Chrome 72
    {
        "name": "Chrome 72",
        "ja3_hash": "66918128f1b9b03303d77c6f2eefd128",
        "ja3": "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53-10,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.96 Safari/537.36",
    },
    # Chrome 83
    {
        "name": "Chrome 83",
        "ja3_hash": "b32309a26951912be7dba376398abc3b",
        "ja3": "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36",
    },
    # Firefox 55
    {
        "name": "Firefox 55",
        "ja3_hash": "0ffee3ba8e615ad22535e7f771690a28",
        "ja3": "771,49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-13,29-23-24-25,0",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:55.0) Gecko/20100101 Firefox/55.0",
    },
    # Firefox 56
    {
        "name": "Firefox 56",
        "ja3_hash": "0ffee3ba8e615ad22535e7f771690a28",
        "ja3": "771,49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-13,29-23-24-25,0",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0",
    },
    # Firefox 63
    {
        "name": "Firefox 63",
        "ja3_hash": "b20b44b18b853ef29ab773e921b03422",
        "ja3": "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:63.0) Gecko/20100101 Firefox/63.0",
    },
    # Firefox 65
    {
        "name": "Firefox 65",
        "ja3_hash": "b20b44b18b853ef29ab773e921b03422",
        "ja3": "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0",
    },
    # iOS 11 Safari
    {
        "name": "iOS 11 Safari",
        "ja3_hash": "a69708a64f853c3bcc214c2c5faf84f3",
        "ja3": "771,49196-49195-49188-49187-49162-49161-52393-49200-49199-49192-49191-49172-49171-52392-157-156-61-60-53-47,65281-0-23-13-5-13172-18-16-11-10,29-23-24-25,0",
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A356 Safari/604.1",
    },
    # iOS 12 Safari
    {
        "name": "iOS 12 Safari",
        "ja3_hash": "5c118da645babe52f060d0754256a73c",
        "ja3": "771,49196-49195-49188-49187-49162-49161-52393-49200-49199-49192-49191-49172-49171-52392-157-156-61-60-53-47-49160-49170-10,65281-0-23-13-5-13172-18-16-11-10,29-23-24-25,0",
        "user_agent": "Mozilla/5.0 (iPod; CPU iPhone OS 12_0 like macOS) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/12.0 Mobile/14A5335d Safari/602.1.50",
    },
    # iOS 17 Safari
    {
        "name": "iOS 17 Safari",
        "ja3_hash": "683732371e44e9583f7fa850fe09e602",
        "ja3": "771,4865-4866-4867-49196-49195-52393-49200-49199-52392-49162-157-156-53-47-49160-49170-10,0-23-65281-10-11-16-5-13-18-51-45-43-27-21,29-23-24-25,0",
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.1 Mobile/15E148 Safari/604.1",
    },
    # macOS Safari (via Firefox 92 on macOS Catalina)
    {
        "name": "macOS Safari",
        "ja3_hash": "aa7744226c695c0b2e440419848cf700",
        "ja3": "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-156-157-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:92.0) Gecko/20100101 Firefox/92.0",
    },
]


@pytest.fixture(scope="module")
def cycle_client():
    """Create a single CycleTLS client for all tests in this module"""
    client = CycleTLS()
    yield client
    client.close()


class TestJA3Fingerprints:
    """Test suite for JA3 fingerprint validation"""

    @pytest.mark.parametrize("fingerprint", JA3_FINGERPRINTS, ids=[fp["name"] for fp in JA3_FINGERPRINTS])
    def test_ja3_fingerprint(self, cycle_client, fingerprint):
        """
        Test that CycleTLS correctly implements JA3 fingerprints.

        Verifies that the JA3 hash and JA3 string returned by ja3er.com
        match the expected values for each browser fingerprint.
        """
        response = cycle_client.get(
            "https://ja3er.com/json",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )

        # Verify successful response
        assert response.status_code == 200, f"Expected status 200 for {fingerprint['name']}, got {response.status_code}"

        # Parse JSON response
        response_data = response.json()

        # Verify JA3 hash matches
        assert response_data.get("ja3_hash") == fingerprint["ja3_hash"], \
            f"JA3 hash mismatch for {fingerprint['name']}: expected {fingerprint['ja3_hash']}, got {response_data.get('ja3_hash')}"

        # Verify JA3 string matches
        assert response_data.get("ja3") == fingerprint["ja3"], \
            f"JA3 string mismatch for {fingerprint['name']}: expected {fingerprint['ja3']}, got {response_data.get('ja3')}"


class TestChromeFingerprints:
    """Dedicated test class for Chrome browser fingerprints"""

    def test_chrome_58(self, cycle_client):
        """Test Chrome 58 fingerprint"""
        fingerprint = next(fp for fp in JA3_FINGERPRINTS if fp["name"] == "Chrome 58")
        response = cycle_client.get(
            "https://ja3er.com/json",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ja3_hash"] == fingerprint["ja3_hash"]
        assert data["ja3"] == fingerprint["ja3"]

    def test_chrome_62(self, cycle_client):
        """Test Chrome 62 fingerprint"""
        fingerprint = next(fp for fp in JA3_FINGERPRINTS if fp["name"] == "Chrome 62")
        response = cycle_client.get(
            "https://ja3er.com/json",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ja3_hash"] == fingerprint["ja3_hash"]
        assert data["ja3"] == fingerprint["ja3"]

    def test_chrome_70(self, cycle_client):
        """Test Chrome 70 fingerprint"""
        fingerprint = next(fp for fp in JA3_FINGERPRINTS if fp["name"] == "Chrome 70")
        response = cycle_client.get(
            "https://ja3er.com/json",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ja3_hash"] == fingerprint["ja3_hash"]
        assert data["ja3"] == fingerprint["ja3"]

    def test_chrome_72(self, cycle_client):
        """Test Chrome 72 fingerprint"""
        fingerprint = next(fp for fp in JA3_FINGERPRINTS if fp["name"] == "Chrome 72")
        response = cycle_client.get(
            "https://ja3er.com/json",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ja3_hash"] == fingerprint["ja3_hash"]
        assert data["ja3"] == fingerprint["ja3"]

    def test_chrome_83(self, cycle_client):
        """Test Chrome 83 fingerprint"""
        fingerprint = next(fp for fp in JA3_FINGERPRINTS if fp["name"] == "Chrome 83")
        response = cycle_client.get(
            "https://ja3er.com/json",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ja3_hash"] == fingerprint["ja3_hash"]
        assert data["ja3"] == fingerprint["ja3"]


class TestFirefoxFingerprints:
    """Dedicated test class for Firefox browser fingerprints"""

    def test_firefox_55(self, cycle_client):
        """Test Firefox 55 fingerprint"""
        fingerprint = next(fp for fp in JA3_FINGERPRINTS if fp["name"] == "Firefox 55")
        response = cycle_client.get(
            "https://ja3er.com/json",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ja3_hash"] == fingerprint["ja3_hash"]
        assert data["ja3"] == fingerprint["ja3"]

    def test_firefox_56(self, cycle_client):
        """Test Firefox 56 fingerprint"""
        fingerprint = next(fp for fp in JA3_FINGERPRINTS if fp["name"] == "Firefox 56")
        response = cycle_client.get(
            "https://ja3er.com/json",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ja3_hash"] == fingerprint["ja3_hash"]
        assert data["ja3"] == fingerprint["ja3"]

    def test_firefox_63(self, cycle_client):
        """Test Firefox 63 fingerprint"""
        fingerprint = next(fp for fp in JA3_FINGERPRINTS if fp["name"] == "Firefox 63")
        response = cycle_client.get(
            "https://ja3er.com/json",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ja3_hash"] == fingerprint["ja3_hash"]
        assert data["ja3"] == fingerprint["ja3"]

    def test_firefox_65(self, cycle_client):
        """Test Firefox 65 fingerprint"""
        fingerprint = next(fp for fp in JA3_FINGERPRINTS if fp["name"] == "Firefox 65")
        response = cycle_client.get(
            "https://ja3er.com/json",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ja3_hash"] == fingerprint["ja3_hash"]
        assert data["ja3"] == fingerprint["ja3"]


class TestSafariFingerprints:
    """Dedicated test class for Safari browser fingerprints"""

    def test_ios_11_safari(self, cycle_client):
        """Test iOS 11 Safari fingerprint"""
        fingerprint = next(fp for fp in JA3_FINGERPRINTS if fp["name"] == "iOS 11 Safari")
        response = cycle_client.get(
            "https://ja3er.com/json",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ja3_hash"] == fingerprint["ja3_hash"]
        assert data["ja3"] == fingerprint["ja3"]

    def test_ios_12_safari(self, cycle_client):
        """Test iOS 12 Safari fingerprint"""
        fingerprint = next(fp for fp in JA3_FINGERPRINTS if fp["name"] == "iOS 12 Safari")
        response = cycle_client.get(
            "https://ja3er.com/json",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ja3_hash"] == fingerprint["ja3_hash"]
        assert data["ja3"] == fingerprint["ja3"]

    def test_ios_17_safari(self, cycle_client):
        """Test iOS 17 Safari fingerprint"""
        fingerprint = next(fp for fp in JA3_FINGERPRINTS if fp["name"] == "iOS 17 Safari")
        response = cycle_client.get(
            "https://ja3er.com/json",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ja3_hash"] == fingerprint["ja3_hash"]
        assert data["ja3"] == fingerprint["ja3"]

    def test_macos_safari(self, cycle_client):
        """Test macOS Safari fingerprint"""
        fingerprint = next(fp for fp in JA3_FINGERPRINTS if fp["name"] == "macOS Safari")
        response = cycle_client.get(
            "https://ja3er.com/json",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ja3_hash"] == fingerprint["ja3_hash"]
        assert data["ja3"] == fingerprint["ja3"]


class TestJA3StringValidation:
    """Test that specific JA3 strings produce expected results"""

    def test_ja3_string_structure(self, cycle_client):
        """Test that JA3 strings have the expected structure"""
        # Test with a known good fingerprint
        fingerprint = JA3_FINGERPRINTS[0]
        response = cycle_client.get(
            "https://ja3er.com/json",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )

        assert response.status_code == 200
        data = response.json()

        # Verify JA3 string contains expected components (TLSVersion,Ciphers,Extensions,EllipticCurves,EllipticCurvePointFormats)
        ja3_parts = data["ja3"].split(",")
        assert len(ja3_parts) == 5, f"JA3 should have 5 comma-separated parts, got {len(ja3_parts)}"

    def test_custom_ja3_string(self, cycle_client):
        """Test with a custom JA3 string"""
        # Use Chrome 83 fingerprint as a known working example
        custom_ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"
        expected_hash = "b32309a26951912be7dba376398abc3b"

        response = cycle_client.get(
            "https://ja3er.com/json",
            ja3=custom_ja3,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ja3"] == custom_ja3
        assert data["ja3_hash"] == expected_hash

    def test_ja3_hash_consistency(self, cycle_client):
        """Test that same JA3 string produces same hash across multiple requests"""
        fingerprint = JA3_FINGERPRINTS[0]

        # Make two requests with the same JA3
        response1 = cycle_client.get(
            "https://ja3er.com/json",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )

        response2 = cycle_client.get(
            "https://ja3er.com/json",
            ja3=fingerprint["ja3"],
            user_agent=fingerprint["user_agent"]
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Verify consistency
        assert data1["ja3_hash"] == data2["ja3_hash"]
        assert data1["ja3"] == data2["ja3"]
