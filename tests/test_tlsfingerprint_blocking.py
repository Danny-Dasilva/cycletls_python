"""
TLS Fingerprint Blocking Tests against tls.peet.ws

These tests are marked as 'blocking' and will cause CI to fail if they fail.
They verify core TLS fingerprinting functionality including:
- JA3 fingerprint application
- JA4/JA4_r fingerprint application
- HTTP/2 fingerprint application
- Fingerprint consistency and exact matching

Test endpoints:
- tls.peet.ws - Primary TLS fingerprint verification service (reliable)
- tlsfingerprint.com - Secondary verification service

Run blocking tests only:
    pytest -m blocking tests/test_tlsfingerprint_blocking.py -v

Run all except blocking:
    pytest -m "not blocking" -v

Based on CycleTLS TypeScript tests:
- tests/ja4-fingerprint.test.js
- tests/http2-fingerprint.test.js
- tests/tlsfingerprint/basic.test.ts
"""
import pytest
from cycletls import CycleTLS

# Mark all tests in this module as blocking (CI-critical)
pytestmark = [pytest.mark.blocking, pytest.mark.live]

# Primary test URL - tls.peet.ws is most reliable
PEET_WS_URL = "https://tls.peet.ws"


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture(scope="function")
def cycle_client():
    """
    Create a new CycleTLS client for each test function.

    Using function scope to avoid connection state issues between tests
    when different fingerprints are applied.
    """
    with CycleTLS() as client:
        yield client


# ==============================================================================
# JA3 Fingerprint Tests
# ==============================================================================


class TestJA3FingerprintBlocking:
    """
    Blocking tests for JA3 fingerprint verification.

    JA3 is a TLS fingerprinting method that creates a hash from:
    - TLS version
    - Cipher suites
    - Extensions
    - Elliptic curves
    - Elliptic curve point formats

    Format: TLSVersion,Ciphers,Extensions,EllipticCurves,EllipticCurvePointFormats
    Example: 771,4865-4866-4867-49195-49199-...,0-23-65281-10-11-...,29-23-24,0
    """

    # Chrome 120 JA3 fingerprint
    CHROME_120_JA3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"
    CHROME_120_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    # Firefox 121 JA3 fingerprint
    FIREFOX_121_JA3 = "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-156-157-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0"
    FIREFOX_121_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"

    def test_ja3_request_returns_tls_data(self, cycle_client):
        """
        [BLOCKING] Verify that TLS fingerprint endpoints return JA3 data.

        This is a core functionality test - if this fails, JA3 fingerprinting
        is fundamentally broken.
        """
        response = cycle_client.get(
            f"{PEET_WS_URL}/api/clean",
            ja3=self.CHROME_120_JA3,
            user_agent=self.CHROME_120_UA,
            enable_connection_reuse=False,
        )

        assert response.status_code == 200, f"Request failed with status {response.status_code}"

        data = response.json()
        assert "ja3" in data, f"Response missing 'ja3' field. Keys: {list(data.keys())}"
        assert "ja3_hash" in data, f"Response missing 'ja3_hash' field. Keys: {list(data.keys())}"

    def test_ja3_chrome_fingerprint_applied(self, cycle_client):
        """
        [BLOCKING] Verify Chrome JA3 fingerprint is correctly applied.

        The observed JA3 string should exactly match our input when using
        tls.peet.ws/api/clean which echoes back the exact JA3.
        """
        response = cycle_client.get(
            f"{PEET_WS_URL}/api/clean",
            ja3=self.CHROME_120_JA3,
            user_agent=self.CHROME_120_UA,
            enable_connection_reuse=False,
        )

        assert response.status_code == 200
        data = response.json()

        # The observed JA3 should match our input
        observed_ja3 = data.get("ja3", "")
        assert observed_ja3 == self.CHROME_120_JA3, (
            f"JA3 mismatch:\n"
            f"Expected: {self.CHROME_120_JA3}\n"
            f"Observed: {observed_ja3}"
        )

    def test_ja3_firefox_fingerprint_applied(self, cycle_client):
        """
        [BLOCKING] Verify Firefox JA3 fingerprint is correctly applied.
        """
        response = cycle_client.get(
            f"{PEET_WS_URL}/api/clean",
            ja3=self.FIREFOX_121_JA3,
            user_agent=self.FIREFOX_121_UA,
            enable_connection_reuse=False,
        )

        assert response.status_code == 200
        data = response.json()

        observed_ja3 = data.get("ja3", "")
        assert observed_ja3 == self.FIREFOX_121_JA3, (
            f"JA3 mismatch:\n"
            f"Expected: {self.FIREFOX_121_JA3}\n"
            f"Observed: {observed_ja3}"
        )

    def test_ja3_hash_format_valid(self, cycle_client):
        """
        [BLOCKING] Verify JA3 hash is valid MD5 format (32 hex characters).
        """
        response = cycle_client.get(
            f"{PEET_WS_URL}/api/clean",
            ja3=self.CHROME_120_JA3,
            user_agent=self.CHROME_120_UA,
            enable_connection_reuse=False,
        )

        assert response.status_code == 200
        data = response.json()

        ja3_hash = data.get("ja3_hash", "")
        assert len(ja3_hash) == 32, f"JA3 hash should be 32 chars (MD5), got {len(ja3_hash)}"
        assert all(c in "0123456789abcdef" for c in ja3_hash.lower()), (
            f"JA3 hash should be hexadecimal: {ja3_hash}"
        )


# ==============================================================================
# JA4 Fingerprint Tests
# ==============================================================================


class TestJA4FingerprintBlocking:
    """
    Blocking tests for JA4/JA4_r fingerprint verification.

    JA4_r is the raw JA4 format containing:
    - Header: t<TLS_version>d<cipher_count><extension_count><ALPN>
    - Cipher suites (hex, sorted)
    - Extensions (hex, sorted)
    - Signature algorithms (hex)

    Format: t13d1516h2_ciphers_extensions_sig_algs
    """

    # Chrome JA4_r fingerprint (Chrome 138+)
    CHROME_JA4R = "t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,44cd,fe0d,ff01_0403,0804,0401,0503,0805,0501,0806,0601"
    CHROME_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"

    # Firefox JA4_r fingerprint (Firefox 141)
    FIREFOX_JA4R = "t13d1717h2_002f,0035,009c,009d,1301,1302,1303,c009,c00a,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,001c,0022,0023,002b,002d,0033,fe0d,ff01_0403,0503,0603,0804,0805,0806,0401,0501,0601,0203,0201"
    FIREFOX_UA = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0"

    # TLS 1.2 JA4_r fingerprint
    TLS12_JA4R = "t12d128h2_002f,0035,009c,009d,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0017,0023,ff01_0403,0804,0401,0503,0805,0501,0806,0601,0201"
    TLS12_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    def test_ja4r_request_returns_tls_data(self, cycle_client):
        """
        [BLOCKING] Verify that TLS fingerprint endpoints return JA4 data.
        """
        response = cycle_client.get(
            f"{PEET_WS_URL}/api/all",
            ja4r=self.CHROME_JA4R,
            user_agent=self.CHROME_UA,
            enable_connection_reuse=False,
        )

        assert response.status_code == 200, f"Request failed with status {response.status_code}"

        data = response.json()
        assert "tls" in data, f"Response missing 'tls' field. Keys: {list(data.keys())}"
        assert "ja4_r" in data["tls"], f"TLS data missing 'ja4_r' field. Keys: {list(data['tls'].keys())}"

    def test_ja4r_chrome_fingerprint_exact_match(self, cycle_client):
        """
        [BLOCKING] Verify Chrome JA4_r fingerprint exactly matches expected value.

        This is a critical test - exact matching proves the fingerprint is being
        correctly applied including all cipher suites, extensions, and sig algs.
        """
        response = cycle_client.get(
            f"{PEET_WS_URL}/api/all",
            ja4r=self.CHROME_JA4R,
            disable_grease=False,
            user_agent=self.CHROME_UA,
            enable_connection_reuse=False,
        )

        assert response.status_code == 200
        data = response.json()

        observed_ja4r = data["tls"]["ja4_r"]
        assert observed_ja4r == self.CHROME_JA4R, (
            f"JA4_r mismatch:\n"
            f"Expected: {self.CHROME_JA4R}\n"
            f"Observed: {observed_ja4r}"
        )

    def test_ja4r_firefox_fingerprint_exact_match(self, cycle_client):
        """
        [BLOCKING] Verify Firefox JA4_r fingerprint exactly matches expected value.

        Firefox fingerprint includes unique extensions like:
        - 0022 (Delegated Credentials)
        - fe0d (ECH)
        """
        response = cycle_client.get(
            f"{PEET_WS_URL}/api/all",
            ja4r=self.FIREFOX_JA4R,
            disable_grease=False,
            user_agent=self.FIREFOX_UA,
            enable_connection_reuse=False,
        )

        assert response.status_code == 200
        data = response.json()

        observed_ja4r = data["tls"]["ja4_r"]
        assert observed_ja4r == self.FIREFOX_JA4R, (
            f"JA4_r mismatch:\n"
            f"Expected: {self.FIREFOX_JA4R}\n"
            f"Observed: {observed_ja4r}"
        )

    def test_ja4r_tls12_fingerprint_exact_match(self, cycle_client):
        """
        [BLOCKING] Verify TLS 1.2 JA4_r fingerprint exactly matches expected value.

        This tests backward compatibility with TLS 1.2 fingerprints which have:
        - t12 header (vs t13 for TLS 1.3)
        - Different cipher/extension counts
        """
        response = cycle_client.get(
            f"{PEET_WS_URL}/api/all",
            ja4r=self.TLS12_JA4R,
            disable_grease=False,
            user_agent=self.TLS12_UA,
            enable_connection_reuse=False,
        )

        assert response.status_code == 200
        data = response.json()

        observed_ja4r = data["tls"]["ja4_r"]
        assert observed_ja4r == self.TLS12_JA4R, (
            f"JA4_r mismatch:\n"
            f"Expected: {self.TLS12_JA4R}\n"
            f"Observed: {observed_ja4r}"
        )

    def test_ja4r_header_format_chrome(self, cycle_client):
        """
        [BLOCKING] Verify Chrome JA4_r header has correct format.

        Header format: t<tls_version>d<cipher_count><ext_count><alpn>
        Chrome 138+: t13d1516h2 = TLS 1.3, 15 ciphers, 16 extensions, HTTP/2
        """
        response = cycle_client.get(
            f"{PEET_WS_URL}/api/all",
            ja4r=self.CHROME_JA4R,
            user_agent=self.CHROME_UA,
            enable_connection_reuse=False,
        )

        assert response.status_code == 200
        data = response.json()

        ja4r = data["tls"]["ja4_r"]
        assert ja4r.startswith("t13d1516h2"), (
            f"Chrome JA4_r should start with 't13d1516h2', got: {ja4r[:12]}"
        )

    def test_ja4r_header_format_firefox(self, cycle_client):
        """
        [BLOCKING] Verify Firefox JA4_r header has correct format.

        Firefox 141: t13d1717h2 = TLS 1.3, 17 ciphers, 17 extensions, HTTP/2
        """
        response = cycle_client.get(
            f"{PEET_WS_URL}/api/all",
            ja4r=self.FIREFOX_JA4R,
            user_agent=self.FIREFOX_UA,
            enable_connection_reuse=False,
        )

        assert response.status_code == 200
        data = response.json()

        ja4r = data["tls"]["ja4_r"]
        assert ja4r.startswith("t13d1717h2"), (
            f"Firefox JA4_r should start with 't13d1717h2', got: {ja4r[:12]}"
        )

    def test_ja4r_http2_negotiation(self, cycle_client):
        """
        [BLOCKING] Verify HTTP/2 is correctly negotiated when using JA4_r fingerprints.

        The 'h2' in the JA4_r header indicates HTTP/2 ALPN should be negotiated.
        """
        response = cycle_client.get(
            f"{PEET_WS_URL}/api/all",
            ja4r=self.CHROME_JA4R,
            user_agent=self.CHROME_UA,
            enable_connection_reuse=False,
        )

        assert response.status_code == 200
        data = response.json()

        http_version = data.get("http_version", "")
        assert http_version == "h2", (
            f"Expected HTTP/2 ('h2') negotiation, got: {http_version}"
        )


# ==============================================================================
# HTTP/2 Fingerprint Tests
# ==============================================================================


class TestHTTP2FingerprintBlocking:
    """
    Blocking tests for HTTP/2 Akamai fingerprint verification.

    HTTP/2 fingerprint format:
    SETTINGS|WINDOW_UPDATE|PRIORITY|PSEUDO_HEADER_ORDER

    SETTINGS format: setting_id:value;setting_id:value;...
    - 1: HEADER_TABLE_SIZE
    - 2: ENABLE_PUSH
    - 4: INITIAL_WINDOW_SIZE
    - 5: MAX_FRAME_SIZE
    - 6: MAX_HEADER_LIST_SIZE

    Pseudo-header order: m,a,s,p (method, authority, scheme, path)
    """

    # Chrome HTTP/2 fingerprint
    CHROME_HTTP2 = "1:65536;2:0;4:6291456;6:262144|15663105|0|m,a,s,p"
    CHROME_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"

    # Firefox HTTP/2 fingerprint
    FIREFOX_HTTP2 = "1:65536;2:0;4:131072;5:16384|12517377|0|m,p,a,s"
    FIREFOX_UA = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0"

    def test_http2_request_returns_fingerprint_data(self, cycle_client):
        """
        [BLOCKING] Verify that HTTP/2 fingerprint data is returned.
        """
        response = cycle_client.get(
            f"{PEET_WS_URL}/api/all",
            http2_fingerprint=self.CHROME_HTTP2,
            user_agent=self.CHROME_UA,
            enable_connection_reuse=False,
        )

        assert response.status_code == 200, f"Request failed with status {response.status_code}"

        data = response.json()
        assert "http2" in data, f"Response missing 'http2' field. Keys: {list(data.keys())}"

    def test_http2_chrome_fingerprint_applied(self, cycle_client):
        """
        [BLOCKING] Verify Chrome HTTP/2 fingerprint is correctly applied.

        The Akamai fingerprint should be present and non-empty.
        """
        response = cycle_client.get(
            f"{PEET_WS_URL}/api/all",
            http2_fingerprint=self.CHROME_HTTP2,
            user_agent=self.CHROME_UA,
            enable_connection_reuse=False,
        )

        assert response.status_code == 200
        data = response.json()

        assert "http2" in data, "Response should contain http2 data"
        http2_data = data["http2"]

        # Should have Akamai fingerprint
        assert "akamai_fingerprint" in http2_data, (
            f"HTTP/2 data should contain 'akamai_fingerprint'. Keys: {list(http2_data.keys())}"
        )

        akamai_fp = http2_data["akamai_fingerprint"]
        assert akamai_fp, "Akamai fingerprint should not be empty"

    def test_http2_firefox_fingerprint_applied(self, cycle_client):
        """
        [BLOCKING] Verify Firefox HTTP/2 fingerprint is correctly applied.
        """
        response = cycle_client.get(
            f"{PEET_WS_URL}/api/all",
            http2_fingerprint=self.FIREFOX_HTTP2,
            user_agent=self.FIREFOX_UA,
            enable_connection_reuse=False,
        )

        assert response.status_code == 200
        data = response.json()

        assert "http2" in data, "Response should contain http2 data"
        http2_data = data["http2"]

        assert "akamai_fingerprint" in http2_data, (
            f"HTTP/2 data should contain 'akamai_fingerprint'. Keys: {list(http2_data.keys())}"
        )

    def test_http2_version_negotiated(self, cycle_client):
        """
        [BLOCKING] Verify HTTP/2 is negotiated when using HTTP/2 fingerprint.
        """
        response = cycle_client.get(
            f"{PEET_WS_URL}/api/all",
            http2_fingerprint=self.CHROME_HTTP2,
            user_agent=self.CHROME_UA,
            enable_connection_reuse=False,
        )

        assert response.status_code == 200
        data = response.json()

        http_version = data.get("http_version", "")
        assert http_version == "h2", f"Expected HTTP/2, got: {http_version}"


# ==============================================================================
# Combined Fingerprint Tests
# ==============================================================================


class TestCombinedFingerprintsBlocking:
    """
    Blocking tests for combined TLS + HTTP/2 fingerprinting.

    These tests verify that both JA3/JA4 and HTTP/2 fingerprints can be
    applied simultaneously and produce the expected results.
    """

    CHROME_JA3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"
    CHROME_JA4R = "t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,44cd,fe0d,ff01_0403,0804,0401,0503,0805,0501,0806,0601"
    CHROME_HTTP2 = "1:65536;2:0;4:6291456;6:262144|15663105|0|m,a,s,p"
    CHROME_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"

    def test_combined_ja4r_and_http2_fingerprint(self, cycle_client):
        """
        [BLOCKING] Verify JA4_r and HTTP/2 fingerprints can be applied together.

        This tests the most realistic browser impersonation scenario where
        both TLS and HTTP/2 fingerprints are customized.
        """
        response = cycle_client.get(
            f"{PEET_WS_URL}/api/all",
            ja4r=self.CHROME_JA4R,
            http2_fingerprint=self.CHROME_HTTP2,
            user_agent=self.CHROME_UA,
            enable_connection_reuse=False,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify TLS fingerprint
        assert "tls" in data, "Response should contain TLS data"
        assert "ja4_r" in data["tls"], "TLS data should contain ja4_r"
        assert data["tls"]["ja4_r"] == self.CHROME_JA4R, "JA4_r should match"

        # Verify HTTP/2 fingerprint
        assert "http2" in data, "Response should contain HTTP/2 data"
        assert "akamai_fingerprint" in data["http2"], "HTTP/2 should have akamai_fingerprint"

    def test_combined_ja3_and_http2_fingerprint(self, cycle_client):
        """
        [BLOCKING] Verify JA3 and HTTP/2 fingerprints can be applied together.
        """
        response = cycle_client.get(
            f"{PEET_WS_URL}/api/all",
            ja3=self.CHROME_JA3,
            http2_fingerprint=self.CHROME_HTTP2,
            user_agent=self.CHROME_UA,
            enable_connection_reuse=False,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify TLS data present
        assert "tls" in data, "Response should contain TLS data"

        # Verify HTTP/2 data present
        assert "http2" in data, "Response should contain HTTP/2 data"


# ==============================================================================
# Fingerprint Consistency Tests
# ==============================================================================


class TestFingerprintConsistencyBlocking:
    """
    Blocking tests for fingerprint consistency across requests.

    These tests verify that fingerprints produce consistent results when
    the same parameters are used multiple times.
    """

    CHROME_JA4R = "t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,44cd,fe0d,ff01_0403,0804,0401,0503,0805,0501,0806,0601"
    CHROME_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"

    def test_ja4r_consistency_across_requests(self, cycle_client):
        """
        [BLOCKING] Verify JA4_r fingerprint is consistent across multiple requests.

        Inconsistent fingerprints would be detected by anti-bot systems.
        """
        responses = []
        for _ in range(3):
            response = cycle_client.get(
                f"{PEET_WS_URL}/api/all",
                ja4r=self.CHROME_JA4R,
                user_agent=self.CHROME_UA,
                enable_connection_reuse=False,
            )
            responses.append(response)

        # All requests should succeed
        for i, resp in enumerate(responses):
            assert resp.status_code == 200, f"Request {i+1} failed with status {resp.status_code}"

        # All JA4_r values should match
        ja4r_values = [resp.json()["tls"]["ja4_r"] for resp in responses]
        assert all(v == ja4r_values[0] for v in ja4r_values), (
            f"JA4_r values should be consistent across requests:\n"
            + "\n".join(f"Request {i+1}: {v}" for i, v in enumerate(ja4r_values))
        )

        # All should match expected value
        assert ja4r_values[0] == self.CHROME_JA4R, (
            f"JA4_r should match expected value:\n"
            f"Expected: {self.CHROME_JA4R}\n"
            f"Observed: {ja4r_values[0]}"
        )


# ==============================================================================
# JA4_r Structure Validation Tests
# ==============================================================================


class TestJA4RStructureBlocking:
    """
    Blocking tests for JA4_r string structure validation.

    These tests verify the internal structure of JA4_r fingerprints is correct.
    """

    CHROME_JA4R = "t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,44cd,fe0d,ff01_0403,0804,0401,0503,0805,0501,0806,0601"
    CHROME_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"

    def test_ja4r_has_four_parts(self, cycle_client):
        """
        [BLOCKING] Verify JA4_r has exactly 4 underscore-separated parts.

        Format: header_ciphers_extensions_sig_algs
        """
        response = cycle_client.get(
            f"{PEET_WS_URL}/api/all",
            ja4r=self.CHROME_JA4R,
            user_agent=self.CHROME_UA,
            enable_connection_reuse=False,
        )

        assert response.status_code == 200
        ja4r = response.json()["tls"]["ja4_r"]

        parts = ja4r.split("_")
        assert len(parts) == 4, (
            f"JA4_r should have 4 underscore-separated parts, got {len(parts)}: {ja4r}"
        )

    def test_ja4r_header_starts_with_t(self, cycle_client):
        """
        [BLOCKING] Verify JA4_r header starts with 't' (TLS indicator).
        """
        response = cycle_client.get(
            f"{PEET_WS_URL}/api/all",
            ja4r=self.CHROME_JA4R,
            user_agent=self.CHROME_UA,
            enable_connection_reuse=False,
        )

        assert response.status_code == 200
        ja4r = response.json()["tls"]["ja4_r"]

        header = ja4r.split("_")[0]
        assert header.startswith("t"), f"JA4_r header should start with 't': {header}"

    def test_ja4r_contains_alpn_indicator(self, cycle_client):
        """
        [BLOCKING] Verify JA4_r header contains ALPN indicator (h1 or h2).
        """
        response = cycle_client.get(
            f"{PEET_WS_URL}/api/all",
            ja4r=self.CHROME_JA4R,
            user_agent=self.CHROME_UA,
            enable_connection_reuse=False,
        )

        assert response.status_code == 200
        ja4r = response.json()["tls"]["ja4_r"]

        header = ja4r.split("_")[0]
        assert "h1" in header or "h2" in header, (
            f"JA4_r header should contain ALPN indicator (h1 or h2): {header}"
        )

    def test_ja4r_ciphers_are_hex(self, cycle_client):
        """
        [BLOCKING] Verify JA4_r cipher suite values are valid hex.
        """
        response = cycle_client.get(
            f"{PEET_WS_URL}/api/all",
            ja4r=self.CHROME_JA4R,
            user_agent=self.CHROME_UA,
            enable_connection_reuse=False,
        )

        assert response.status_code == 200
        ja4r = response.json()["tls"]["ja4_r"]

        ciphers = ja4r.split("_")[1].split(",")
        for cipher in ciphers:
            assert all(c in "0123456789abcdef" for c in cipher.lower()), (
                f"Cipher suite should be hex: {cipher}"
            )
