"""
pytest configuration and shared fixtures for CycleTLS tests.
"""

import os
import re
import sys

import pytest

# tlsfingerprint.com base URL — override with TLSFP_URL env var to point at a local instance.
# Default is the production endpoint (https://tls.peet.ws); CI sets TLSFP_URL to a local Docker
# container running Danny-Dasilva/tlsfingerprint.com (the source of tls.peet.ws).
_TLSFP_URL = os.environ.get("TLSFP_URL", "https://tls.peet.ws")

# Add parent directory to path to import cycletls
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cycletls import AsyncCycleTLS, CycleTLS


@pytest.fixture(scope="session")
def cycletls_client():
    """
    Session-scoped CycleTLS client fixture.
    Creates a single client instance for all tests.

    Connection reuse is disabled ONLY for requests against the local
    tlsfingerprint.com server (which closes the TLS connection after every
    response, leaving a stale cached connection in the global Go transport
    pool for the next test). Requests against httpbin.org and other public
    endpoints rely on HTTP/1.1 keep-alive working normally; force-disabling
    reuse there causes "server closed idle connection" / EOF errors on
    multi-request flows (e.g. cookie set+get, redirect chains).
    """
    client = CycleTLS()
    _orig = client.request
    def _no_reuse_for_tlsfp(method, url, **kwargs):
        if _TLSFP_URL in url:
            kwargs.setdefault("enable_connection_reuse", False)
        return _orig(method, url, **kwargs)
    client.request = _no_reuse_for_tlsfp
    yield client
    client.close()


@pytest.fixture(scope="function")
def cycletls_client_function():
    """
    Function-scoped CycleTLS client fixture.
    Creates a new client instance for each test function.
    """
    client = CycleTLS()
    yield client
    client.close()


@pytest.fixture
def test_url():
    """Base test URL for most tests."""
    return f"{_TLSFP_URL}/api/clean"


@pytest.fixture
def ja3_test_url():
    """TLS fingerprint test URL (replacement for defunct ja3er.com)."""
    return f"{_TLSFP_URL}/api/clean"


@pytest.fixture(scope="session")
def tlsfp_url():
    """tlsfingerprint.com base URL. Set TLSFP_URL env var to point at a local instance."""
    return _TLSFP_URL


@pytest.fixture
def httpbin_url():
    """HTTPBin URL for testing various HTTP features."""
    return "https://httpbin.org"


@pytest.fixture
def chrome_ja3():
    """Chrome 120 JA3 fingerprint."""
    return "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0"


@pytest.fixture
def firefox_ja3():
    """Firefox 120 JA3 fingerprint."""
    return "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0"


@pytest.fixture
def safari_ja3():
    """Safari 17 JA3 fingerprint."""
    return "771,4865-4867-4866-49196-49195-52393-49200-49199-52392-49162-49161-49172-49171-157-156-53-47-49160-49170-10,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513-21,29-23-24-25,0"


# Async fixtures

@pytest.fixture(scope="session")
async def async_cycletls_client():
    """
    Session-scoped AsyncCycleTLS client fixture.
    Creates a single async client instance for all async tests.
    """
    client = AsyncCycleTLS()
    yield client
    await client.close()


@pytest.fixture(scope="function")
async def async_cycletls_client_function():
    """
    Function-scoped AsyncCycleTLS client fixture.
    Creates a new async client instance for each test function.
    """
    client = AsyncCycleTLS()
    yield client
    await client.close()


# ==============================================================================
# JA4_r structural matchers (shared across test modules)
# ==============================================================================
#
# JA4_r header format: t<TLS_ver>d<cipher_count><ext_count><ALPN>
# Per the JA4 spec, cipher_count and ext_count are 2-digit zero-padded.
# Production tls.peet.ws emits an unpadded form (e.g. "t12d128h2" for 12+8),
# while local tlsfingerprint.com Docker emits the spec form ("t12d1208h2").
# Both are accepted: helpers validate STRUCTURE rather than exact prefixes.

_JA4R_HEADER_RE = re.compile(r"^t(?P<ver>\d{2})d(?P<counts>\d+)(?P<alpn>h2|h1|http)$")


def _decode_counts(counts: str, observed_cipher_count: int) -> tuple[int, int]:
    """
    Decode the concatenated cipher_count + ext_count field from a JA4_r
    header. Returns (cipher_count, ext_count).

    Strategy: enumerate every (cc, ec) split where cc is a prefix of
    `counts`, prefer the split where cc equals the observed cipher count
    (this disambiguates unpadded production output). Otherwise fall back
    to the spec form (2-digit padded each, length 4).
    """
    candidates: list[tuple[int, int]] = []
    for split in range(1, len(counts)):
        try:
            cc = int(counts[:split])
            ec = int(counts[split:])
        except ValueError:
            continue
        candidates.append((cc, ec))

    # Prefer the candidate whose cipher count matches what we actually saw.
    for cc, ec in candidates:
        if cc == observed_cipher_count:
            return cc, ec

    # Fall back to the spec form (4-char zero-padded) if available.
    if len(counts) == 4:
        return int(counts[:2]), int(counts[2:])

    # Last resort: assume single-digit cipher count.
    if candidates:
        return candidates[0]
    raise AssertionError(f"Could not decode JA4_r counts field: {counts!r}")


def parse_ja4r(s: str) -> dict:
    """
    Parse a JA4_r string into its structural components.

    JA4_r format: t<ver>d<cipher_count><ext_count><ALPN>_<ciphers>_<extensions>_<sigalgs>

    The cipher_count and ext_count fields in the header may be either:
      - Unpadded (e.g. "128" -- 12 ciphers + 8 extensions, the format
        currently produced by the production tls.peet.ws server)
      - Zero-padded to 2 digits each (e.g. "1208" -- 12 + 08, per the JA4
        spec, the format produced by the local tlsfingerprint.com Docker
        server)

    Note: the cipher_count and ext_count *header* fields refer to the
    counts seen on the wire and may include SNI (0x0000) and ALPN (0x0010),
    while the rendered extension list excludes those. So header counts will
    NOT always equal `len(extensions)`. This helper returns the header
    counts as ints (best-effort interpretation, preferring the spec
    zero-padded form when ambiguous) and the observed list lengths
    separately.

    Returns a dict with keys:
      tls_version, alpn, header_cipher_count, header_ext_count,
      ciphers, extensions, sig_algs, header, raw.
    """
    parts = s.split("_")
    assert len(parts) == 4, f"JA4_r should have 4 underscore-separated parts, got {len(parts)}: {s}"

    header, ciphers_s, exts_s, sigs_s = parts
    m = _JA4R_HEADER_RE.match(header)
    assert m, f"JA4_r header malformed: {header!r}"

    ciphers = [c for c in ciphers_s.split(",") if c]
    extensions = [e for e in exts_s.split(",") if e]
    sig_algs = [a for a in sigs_s.split(",") if a]

    counts = m.group("counts")
    header_cc, header_ec = _decode_counts(counts, len(ciphers))

    return {
        "tls_version": m.group("ver"),
        "alpn": m.group("alpn"),
        "header_cipher_count": header_cc,
        "header_ext_count": header_ec,
        "ciphers": ciphers,
        "extensions": extensions,
        "sig_algs": sig_algs,
        "header": header,
        "raw": s,
    }


def assert_ja4r_equivalent(actual: str, expected: str) -> None:
    """
    Assert two JA4_r strings are structurally equivalent.

    Header padding for cipher_count/ext_count may differ between servers
    (production unpadded vs spec-compliant zero-padded), but the body
    (ciphers, extensions, signature algorithms) and TLS version + ALPN
    must match exactly.
    """
    a = parse_ja4r(actual)
    e = parse_ja4r(expected)
    assert a["tls_version"] == e["tls_version"], (
        f"TLS version mismatch: actual={a['tls_version']} expected={e['tls_version']}"
    )
    assert a["alpn"] == e["alpn"], f"ALPN mismatch: actual={a['alpn']} expected={e['alpn']}"
    assert a["ciphers"] == e["ciphers"], (
        f"Cipher list mismatch:\nactual:   {a['ciphers']}\nexpected: {e['ciphers']}"
    )
    assert a["extensions"] == e["extensions"], (
        f"Extension list mismatch:\nactual:   {a['extensions']}\nexpected: {e['extensions']}"
    )
    assert a["sig_algs"] == e["sig_algs"], (
        f"Signature algorithm list mismatch:\nactual:   {a['sig_algs']}\nexpected: {e['sig_algs']}"
    )
