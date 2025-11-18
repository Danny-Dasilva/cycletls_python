"""
pytest configuration and shared fixtures for CycleTLS tests.
"""

import pytest
import sys
import os

# Add parent directory to path to import cycletls
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cycletls import CycleTLS, AsyncCycleTLS


@pytest.fixture(scope="session")
def cycletls_client():
    """
    Session-scoped CycleTLS client fixture.
    Creates a single client instance for all tests.
    """
    client = CycleTLS()
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
    return "https://ja3er.com/json"


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
