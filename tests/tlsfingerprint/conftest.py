"""
Test helpers for tlsfingerprint.com integration tests.

Mirrors the TypeScript helpers in tests/tlsfingerprint/helpers.ts

IMPORTANT: These tests require tlsfingerprint.com to be available.
The service sometimes returns 521 errors behind Cloudflare protection.
"""

import gzip
import zlib
import pytest
import urllib.request
import urllib.error
import ssl
from typing import Optional, Dict, Any, TypedDict
from cycletls import CycleTLS

try:
    import brotli
    HAS_BROTLI = True
except ImportError:
    HAS_BROTLI = False


# ==============================================================================
# Test Configuration
# ==============================================================================

# Target server for all tests
TEST_SERVER_URL = "https://tlsfingerprint.com"

# Cache for service availability check
_service_available: Optional[bool] = None


# ==============================================================================
# Service Availability
# ==============================================================================


def is_service_available() -> bool:
    """
    Check if tlsfingerprint.com is available.
    Returns true if service returns 200, false otherwise (e.g., 521 Cloudflare error).
    """
    global _service_available
    if _service_available is not None:
        return _service_available

    try:
        # Create SSL context that doesn't verify certificates (for self-signed certs)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(f"{TEST_SERVER_URL}/get", method="GET")
        with urllib.request.urlopen(req, timeout=5, context=ctx) as response:
            _service_available = response.status == 200
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, Exception):
        _service_available = False

    return _service_available


# ==============================================================================
# Default Options
# ==============================================================================

# Common JA3 fingerprint for all tests (Chrome 120)
DEFAULT_JA3 = (
    "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,"
    "0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0"
)

# Default User-Agent (Chrome 120 on Windows)
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def get_default_options() -> Dict[str, Any]:
    """Get default request options for tests."""
    return {
        "ja3": DEFAULT_JA3,
        "user_agent": DEFAULT_USER_AGENT,
        # tlsfingerprint.com uses a self-signed certificate
        "insecure_skip_verify": True,
        # Disable connection reuse for fingerprint tests to avoid connection issues
        "enable_connection_reuse": False,
    }


# ==============================================================================
# Response Type Definitions
# ==============================================================================


class TLSFingerprintResponse(TypedDict, total=False):
    """Common TLS fingerprint fields present in all responses from tlsfingerprint.com."""
    ja3: str
    ja3_hash: str
    ja4: str
    ja4_r: str
    akamai: str
    akamai_hash: str
    peetprint: str
    peetprint_hash: str
    http_version: str


class EchoResponse(TLSFingerprintResponse, total=False):
    """Echo response (httpbin-style) from /get, /post, /put, etc."""
    args: Dict[str, Any]
    headers: Dict[str, str]
    origin: str
    url: str
    method: str
    data: str
    form: Dict[str, Any]
    files: Dict[str, Any]
    json: Any


class CompressionResponse(TLSFingerprintResponse, total=False):
    """Compression response from /gzip, /deflate, /brotli."""
    gzipped: bool
    deflated: bool
    brotli: bool


class CookiesResponse(TLSFingerprintResponse, total=False):
    """Cookies response from /cookies."""
    cookies: Dict[str, str]


class RedirectResponse(TLSFingerprintResponse, total=False):
    """Redirect response from /redirect/N."""
    redirect_count: int
    location: str


class StatusResponse(TLSFingerprintResponse, total=False):
    """Status response from /status/N."""
    status_code: int


class DelayResponse(EchoResponse, total=False):
    """Delay response from /delay/N."""
    delay: int


# ==============================================================================
# Required TLS Fields
# ==============================================================================

REQUIRED_TLS_FIELDS = [
    "ja3",
    "ja3_hash",
    "ja4",
    "peetprint",
    "peetprint_hash",
]


def assert_tls_fields_present(body: Dict[str, Any]) -> None:
    """
    Assert that all required TLS fingerprint fields are present and non-empty.

    Args:
        body: Parsed JSON response body

    Raises:
        AssertionError: If any required field is missing or empty
    """
    for field in REQUIRED_TLS_FIELDS:
        value = body.get(field)
        assert value is not None and value != "", f"Missing or empty required TLS field: {field}"


# ==============================================================================
# Decompression Helpers
# ==============================================================================


def looks_like_json(data: bytes) -> bool:
    """Check if data looks like JSON (starts with { or [)."""
    text = data.decode("utf-8", errors="ignore").strip()
    return text.startswith("{") or text.startswith("[")


def decompress_gzip(data: bytes) -> Dict[str, Any]:
    """
    Decompress gzip data and parse as JSON.
    Falls back to parsing as plain JSON if decompression fails.
    """
    import json

    # If already looks like JSON, the server didn't compress
    if looks_like_json(data):
        return json.loads(data)

    try:
        decompressed = gzip.decompress(data)
        return json.loads(decompressed)
    except Exception:
        # Maybe it wasn't compressed after all
        return json.loads(data)


def decompress_deflate(data: bytes) -> Dict[str, Any]:
    """
    Decompress deflate data and parse as JSON.
    Note: deflate can be either raw deflate or zlib-wrapped, try both.
    Falls back to parsing as plain JSON if decompression fails.
    """
    import json

    # If already looks like JSON, the server didn't compress
    if looks_like_json(data):
        return json.loads(data)

    # Try zlib-wrapped deflate first (more common)
    try:
        decompressed = zlib.decompress(data)
        return json.loads(decompressed)
    except zlib.error:
        # Try raw deflate
        try:
            decompressed = zlib.decompress(data, -zlib.MAX_WBITS)
            return json.loads(decompressed)
        except Exception:
            # Maybe it wasn't compressed after all
            return json.loads(data)


def decompress_brotli(data: bytes) -> Dict[str, Any]:
    """
    Decompress brotli data and parse as JSON.
    Falls back to parsing as plain JSON if decompression fails.
    """
    import json

    # If already looks like JSON, the server didn't compress
    if looks_like_json(data):
        return json.loads(data)

    if not HAS_BROTLI:
        # No brotli support, try parsing as JSON
        return json.loads(data)

    try:
        decompressed = brotli.decompress(data)
        return json.loads(decompressed)
    except Exception:
        # Maybe it wasn't compressed after all
        return json.loads(data)


def decompress_auto(data: bytes, content_encoding: Optional[str] = None) -> Dict[str, Any]:
    """Auto-detect compression type from Content-Encoding header and decompress."""
    import json

    encoding = (content_encoding or "").lower()

    if "gzip" in encoding:
        return decompress_gzip(data)
    elif "br" in encoding:
        return decompress_brotli(data)
    elif "deflate" in encoding:
        return decompress_deflate(data)
    else:
        # No compression or unknown, try parsing as-is
        return json.loads(data)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture(scope="session")
def service_available():
    """Check if tlsfingerprint.com is available at session start."""
    available = is_service_available()
    if not available:
        pytest.skip("tlsfingerprint.com is unavailable (received 521 or timeout)")
    return available


@pytest.fixture(scope="function")
def cycle_client():
    """
    Create a fresh CycleTLS client for each test.

    Function-scoped to ensure test isolation - each test gets a fresh client
    with no shared connection state. This prevents test pollution when
    fingerprints change between tests.

    Following the TypeScript pattern from basic.test.ts where each test
    creates a fresh client in beforeEach and closes it in afterEach.
    """
    with CycleTLS() as client:
        yield client


@pytest.fixture(scope="module")
def test_server_url():
    """Target server URL."""
    return TEST_SERVER_URL


@pytest.fixture(scope="module")
def default_options():
    """Default options fixture."""
    return get_default_options


# ==============================================================================
# Skip Decorator
# ==============================================================================


def skip_if_service_unavailable(func):
    """Decorator to skip test if service is unavailable."""
    def wrapper(*args, **kwargs):
        if not is_service_available():
            pytest.skip("tlsfingerprint.com is unavailable (received 521 or timeout)")
        return func(*args, **kwargs)
    return wrapper
