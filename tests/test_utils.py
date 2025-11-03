"""
Test utility functions and helpers.
"""

import json
from typing import Dict, Any


def assert_valid_response(response, expected_status=200):
    """
    Assert that a response is valid and has the expected status code.

    Args:
        response: CycleTLS Response object
        expected_status: Expected HTTP status code (default: 200)
    """
    assert response is not None, "Response should not be None"
    assert hasattr(response, 'status_code'), "Response should have status_code"
    assert hasattr(response, 'body'), "Response should have body"
    assert hasattr(response, 'headers'), "Response should have headers"
    assert response.status_code == expected_status, f"Expected status {expected_status}, got {response.status_code}"


def assert_valid_json_response(response, expected_status=200):
    """
    Assert that a response is valid JSON.

    Args:
        response: CycleTLS Response object
        expected_status: Expected HTTP status code (default: 200)

    Returns:
        dict: Parsed JSON data
    """
    assert_valid_response(response, expected_status)
    assert response.body, "Response body should not be empty"

    try:
        data = json.loads(response.body)
        assert isinstance(data, (dict, list)), "JSON should be dict or list"
        return data
    except json.JSONDecodeError as e:
        pytest.fail(f"Response body is not valid JSON: {e}")


def assert_ja3_match(response, expected_ja3=None):
    """
    Assert that the JA3 fingerprint in the response matches expected.

    Args:
        response: CycleTLS Response object
        expected_ja3: Expected JA3 string (optional)
    """
    data = assert_valid_json_response(response)

    assert 'ja3' in data or 'ja3_hash' in data, "Response should contain JA3 information"

    if expected_ja3:
        actual_ja3 = data.get('ja3', '')
        assert actual_ja3 == expected_ja3, f"Expected JA3 {expected_ja3}, got {actual_ja3}"


def assert_headers_present(response, required_headers):
    """
    Assert that required headers are present in the response.

    Args:
        response: CycleTLS Response object
        required_headers: List of required header names (case-insensitive)
    """
    assert_valid_response(response)

    headers_lower = {k.lower(): v for k, v in response.headers.items()}

    for header in required_headers:
        header_lower = header.lower()
        assert header_lower in headers_lower, f"Required header '{header}' not found in response"


def assert_cookie_present(response, cookie_name):
    """
    Assert that a cookie with the given name is present in the response.

    Args:
        response: CycleTLS Response object
        cookie_name: Name of the cookie to check
    """
    if hasattr(response, 'cookies') and response.cookies:
        cookie_names = [c.name for c in response.cookies]
        assert cookie_name in cookie_names, f"Cookie '{cookie_name}' not found in response"
    else:
        # Check Set-Cookie header as fallback
        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        set_cookie = headers_lower.get('set-cookie', '')
        assert cookie_name in set_cookie, f"Cookie '{cookie_name}' not found in Set-Cookie header"


def extract_json_field(response, field_name):
    """
    Extract a field from JSON response.

    Args:
        response: CycleTLS Response object
        field_name: Name of the field to extract

    Returns:
        Field value or None if not found
    """
    data = assert_valid_json_response(response)
    return data.get(field_name)


def is_binary_data(data):
    """
    Check if data appears to be binary (not text).

    Args:
        data: bytes or str to check

    Returns:
        bool: True if data appears to be binary
    """
    if isinstance(data, str):
        return False

    if isinstance(data, bytes):
        # Check for null bytes or high ratio of non-printable characters
        null_count = data.count(b'\x00')
        if null_count > 0:
            return True

        # Check ratio of printable vs non-printable
        printable = sum(1 for b in data if 32 <= b <= 126 or b in (9, 10, 13))
        ratio = printable / len(data) if len(data) > 0 else 1
        return ratio < 0.8

    return False


class MockServer:
    """Mock server for testing purposes."""

    def __init__(self):
        self.requests = []

    def record_request(self, method, url, headers, body):
        """Record a request."""
        self.requests.append({
            'method': method,
            'url': url,
            'headers': headers,
            'body': body
        })

    def get_last_request(self):
        """Get the last recorded request."""
        return self.requests[-1] if self.requests else None

    def clear(self):
        """Clear all recorded requests."""
        self.requests = []
