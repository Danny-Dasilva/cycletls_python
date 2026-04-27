"""
pytest configuration and shared fixtures for CycleTLS tests.
"""

import os
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

    Connection reuse is disabled by default so that tlsfingerprint.com-style servers
    (which close connections after every response) don't leave a stale cached
    connection in the global Go transport pool for the next test.
    """
    client = CycleTLS()
    _orig = client.request
    def _no_reuse(method, url, **kwargs):
        kwargs.setdefault("enable_connection_reuse", False)
        return _orig(method, url, **kwargs)
    client.request = _no_reuse
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
