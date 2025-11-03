import pytest
from cycletls import CycleTLS


@pytest.fixture
def client():
    """Create a CycleTLS client instance"""
    cycle = CycleTLS()
    yield cycle
    cycle.close()


def test_basic_timeout(client):
    """Test basic timeout functionality with default timeout"""
    # This should succeed with default timeout (6 seconds)
    result = client.get("https://httpbin.org/delay/1")
    assert result.status_code == 200


def test_custom_timeout_success(client):
    """Test that request completes within custom timeout"""
    # 5 second timeout should be enough for 2 second delay
    result = client.get("https://httpbin.org/delay/2", timeout=5)
    assert result.status_code == 200


def test_custom_timeout_failure(client):
    """Test that request fails when timeout is too short"""
    # 1 second timeout should fail for 3 second delay
    with pytest.raises(Exception) as exc_info:
        client.get("https://httpbin.org/delay/3", timeout=1)

    # The error should be related to timeout
    error_msg = str(exc_info.value).lower()
    assert any(word in error_msg for word in ['timeout', 'deadline', 'context'])


def test_short_timeout(client):
    """Test with very short timeout value"""
    # 500ms timeout should fail for 2 second delay
    with pytest.raises(Exception) as exc_info:
        client.get("https://httpbin.org/delay/2", timeout=0.5)

    error_msg = str(exc_info.value).lower()
    assert any(word in error_msg for word in ['timeout', 'deadline', 'context'])


def test_long_timeout(client):
    """Test with longer custom timeout value"""
    # 10 second timeout should be plenty for 1 second delay
    result = client.get("https://httpbin.org/delay/1", timeout=10)
    assert result.status_code == 200


def test_timeout_zero_delay(client):
    """Test timeout with instant response (no delay)"""
    # Even with a short timeout, instant response should work
    result = client.get("https://httpbin.org/delay/0", timeout=1)
    assert result.status_code == 200


def test_timeout_with_post(client):
    """Test timeout works with POST requests"""
    # Test POST request with timeout
    result = client.post(
        "https://httpbin.org/delay/1",
        body='{"test": "data"}',
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    assert result.status_code == 200


def test_timeout_error_handling(client):
    """Test that timeout errors are properly raised and contain useful info"""
    try:
        # This should timeout
        client.get("https://httpbin.org/delay/5", timeout=1)
        pytest.fail("Expected timeout error was not raised")
    except Exception as e:
        # Verify we get a meaningful error message
        error_msg = str(e).lower()
        assert len(error_msg) > 0
        # Should contain some timeout-related keyword
        assert any(word in error_msg for word in ['timeout', 'deadline', 'context', 'exceeded'])


def test_default_timeout_value():
    """Test that default timeout value is set correctly"""
    from cycletls.schema import Request

    # Default timeout should be 6 seconds as per schema.py
    req = Request(url="https://example.com", method="GET")
    assert req.timeout == 6


@pytest.mark.parametrize("delay,timeout,should_succeed", [
    (1, 3, True),   # 1s delay, 3s timeout - should succeed
    (2, 5, True),   # 2s delay, 5s timeout - should succeed
    (3, 1, False),  # 3s delay, 1s timeout - should fail
    (5, 2, False),  # 5s delay, 2s timeout - should fail
])
def test_timeout_parametrized(client, delay, timeout, should_succeed):
    """Parametrized test for various timeout scenarios"""
    url = f"https://httpbin.org/delay/{delay}"

    if should_succeed:
        result = client.get(url, timeout=timeout)
        assert result.status_code == 200
    else:
        with pytest.raises(Exception) as exc_info:
            client.get(url, timeout=timeout)
        error_msg = str(exc_info.value).lower()
        assert any(word in error_msg for word in ['timeout', 'deadline', 'context'])
