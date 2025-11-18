"""
Comprehensive integration tests for CycleTLS Python library.

Based on CycleTLS TypeScript integration tests, these tests verify:
- Basic GET requests
- User-agent and JA3 fingerprint settings
- HTTP methods (POST, PUT, PATCH, DELETE)
- Custom headers
- Cookies handling
- Response headers parsing
- HTML responses
- Status code validation

All tests use httpbin.org or ja3er.com as test endpoints.
"""

import pytest
import json
from test_utils import (
    assert_valid_response,
    assert_valid_json_response,
    extract_json_field,
)


class TestBasicRequests:
    """Test basic HTTP GET requests."""

    def test_basic_get_request(self, cycletls_client, httpbin_url):
        """Test basic GET request to httpbin."""
        response = cycletls_client.get(f"{httpbin_url}/ip")
        assert_valid_response(response, expected_status=200)

        # Verify response contains valid JSON
        data = assert_valid_json_response(response)
        assert 'origin' in data, "Response should contain 'origin' field with IP address"

    def test_get_with_ja3er(self, cycletls_client):
        """Test GET request to ja3er.com to verify JA3 fingerprinting."""
        response = cycletls_client.get("https://ja3er.com/json")
        assert_valid_response(response, expected_status=200)

        # Verify JA3 data is present
        data = assert_valid_json_response(response)
        assert 'ja3_hash' in data or 'ja3' in data, "Response should contain JA3 information"

    def test_html_response(self, cycletls_client, httpbin_url):
        """Test handling of HTML responses."""
        response = cycletls_client.get(f"{httpbin_url}/html")
        assert_valid_response(response, expected_status=200)

        # Verify HTML content
        assert response.body, "Response body should not be empty"
        assert isinstance(response.body, str), "Response body should be string"
        assert '<!DOCTYPE html>' in response.body or '<html' in response.body, \
            "Response should contain HTML"

    def test_example_com(self, cycletls_client):
        """Test request to example.com (tests TLS extension 43)."""
        response = cycletls_client.get("https://example.com")
        assert_valid_response(response, expected_status=200)

        # Verify HTML content
        assert response.body, "Response body should not be empty"
        assert 'Example Domain' in response.body or 'example' in response.body.lower(), \
            "Response should contain example.com content"


class TestUserAgent:
    """Test user-agent configuration."""

    def test_custom_user_agent(self, cycletls_client, httpbin_url):
        """Test setting custom user-agent."""
        custom_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36'

        response = cycletls_client.get(
            f"{httpbin_url}/user-agent",
            user_agent=custom_ua
        )
        assert_valid_response(response, expected_status=200)

        # Verify user-agent was set correctly
        data = assert_valid_json_response(response)
        assert 'user-agent' in data, "Response should contain user-agent field"
        assert data['user-agent'] == custom_ua, \
            f"User-agent should be '{custom_ua}', got '{data.get('user-agent')}'"

    def test_user_agent_with_ja3(self, cycletls_client, firefox_ja3):
        """Test user-agent with JA3 fingerprint on ja3er.com."""
        custom_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36'

        response = cycletls_client.get(
            "https://ja3er.com/json",
            user_agent=custom_ua,
            ja3=firefox_ja3
        )
        assert_valid_response(response, expected_status=200)

        # Verify response contains JA3 data
        data = assert_valid_json_response(response)
        assert 'ja3_hash' in data or 'ja3' in data, "Response should contain JA3 information"


class TestHTTPMethods:
    """Test various HTTP methods (POST, PUT, PATCH, DELETE)."""

    def test_post_request(self, cycletls_client, httpbin_url):
        """Test POST request with JSON body."""
        payload = {"field": "POST-VAL"}

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            json_data=payload
        )
        assert_valid_response(response, expected_status=200)

        # Verify the POST data was received
        data = assert_valid_json_response(response)
        assert 'data' in data or 'json' in data, "Response should contain posted data"

        # Check if data was parsed as JSON
        if 'json' in data:
            assert data['json'] == payload, f"Posted JSON should match, got {data.get('json')}"
        elif 'data' in data:
            # If returned as string, verify it contains our value
            assert 'POST-VAL' in data['data'], f"Posted data should contain 'POST-VAL', got {data.get('data')}"

    def test_put_request(self, cycletls_client, httpbin_url):
        """Test PUT request with JSON body."""
        payload = {"field": "PUT-VAL"}

        response = cycletls_client.put(
            f"{httpbin_url}/put",
            json_data=payload
        )
        assert_valid_response(response, expected_status=200)

        # Verify the PUT data was received
        data = assert_valid_json_response(response)
        assert 'data' in data or 'json' in data, "Response should contain PUT data"

        # Check if data was parsed as JSON
        if 'json' in data:
            assert data['json'] == payload, f"PUT JSON should match, got {data.get('json')}"
        elif 'data' in data:
            assert 'PUT-VAL' in data['data'], f"PUT data should contain 'PUT-VAL', got {data.get('data')}"

    def test_patch_request(self, cycletls_client, httpbin_url):
        """Test PATCH request with JSON body."""
        payload = {"field": "PATCH-VAL"}

        response = cycletls_client.patch(
            f"{httpbin_url}/patch",
            json_data=payload
        )
        assert_valid_response(response, expected_status=200)

        # Verify the PATCH data was received
        data = assert_valid_json_response(response)
        assert 'data' in data or 'json' in data, "Response should contain PATCH data"

        # Check if data was parsed as JSON
        if 'json' in data:
            assert data['json'] == payload, f"PATCH JSON should match, got {data.get('json')}"
        elif 'data' in data:
            assert 'PATCH-VAL' in data['data'], f"PATCH data should contain 'PATCH-VAL', got {data.get('data')}"

    def test_delete_request(self, cycletls_client, httpbin_url):
        """Test DELETE request with JSON body."""
        payload = {"field": "DELETE-VAL"}

        response = cycletls_client.delete(
            f"{httpbin_url}/delete",
            json_data=payload
        )
        assert_valid_response(response, expected_status=200)

        # Verify the DELETE request was processed
        data = assert_valid_json_response(response)
        # DELETE may or may not include the body in response
        assert 'url' in data or 'args' in data, "Response should contain request information"


class TestHeaders:
    """Test custom headers functionality."""

    def test_custom_headers(self, cycletls_client, httpbin_url):
        """Test sending custom headers."""
        custom_headers = {
            "Authorization": "Bearer someexampletoken",
            "X-Custom-Header": "test-value"
        }

        response = cycletls_client.get(
            f"{httpbin_url}/headers",
            headers=custom_headers
        )
        assert_valid_response(response, expected_status=200)

        # Verify headers were sent
        data = assert_valid_json_response(response)
        assert 'headers' in data, "Response should contain headers information"

        headers = data['headers']
        assert 'Authorization' in headers, "Authorization header should be present"
        assert headers['Authorization'] == "Bearer someexampletoken", \
            f"Authorization header should match, got {headers.get('Authorization')}"

    def test_response_headers(self, cycletls_client, httpbin_url):
        """Test response headers parsing."""
        response = cycletls_client.get(
            f"{httpbin_url}/response-headers?ExampleResponseHeader=HeaderisPickedUpByServer"
        )
        assert_valid_response(response, expected_status=200)

        # Verify response headers exist
        assert hasattr(response, 'headers'), "Response should have headers attribute"
        assert isinstance(response.headers, dict), "Headers should be a dictionary"

        # Common headers that should be present
        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        assert 'content-type' in headers_lower, "Content-Type header should be present"

    def test_response_custom_header(self, cycletls_client, httpbin_url):
        """Test that custom response headers are captured."""
        response = cycletls_client.get(
            f"{httpbin_url}/response-headers?MyCustomHeader=CustomValue"
        )
        assert_valid_response(response, expected_status=200)

        # Verify custom header in response body (httpbin echoes it back)
        data = assert_valid_json_response(response)
        # httpbin includes the custom header in the response
        assert 'MyCustomHeader' in data or 'mycustomheader' in str(data).lower(), \
            "Custom response header should be present in response"


class TestCookies:
    """Test cookies handling."""

    def test_send_cookies(self, cycletls_client, httpbin_url):
        """Test sending cookies with request."""
        cookies = [
            {
                "name": "example1",
                "value": "aaaaaaa",
                "expires": "2026-01-02T15:04:05Z"
            },
            {
                "name": "example2",
                "value": "bbbbbbbbb",
                "expires": "2026-01-06T02:03:05Z"
            }
        ]

        response = cycletls_client.get(
            f"{httpbin_url}/cookies",
            cookies=cookies
        )
        assert_valid_response(response, expected_status=200)

        # Verify cookies were sent
        data = assert_valid_json_response(response)
        assert 'cookies' in data, "Response should contain cookies information"

        cookies_dict = data['cookies']
        assert 'example1' in cookies_dict, "Cookie 'example1' should be present"
        assert 'example2' in cookies_dict, "Cookie 'example2' should be present"
        assert cookies_dict['example1'] == 'aaaaaaa', \
            f"Cookie value should be 'aaaaaaa', got {cookies_dict.get('example1')}"
        assert cookies_dict['example2'] == 'bbbbbbbbb', \
            f"Cookie value should be 'bbbbbbbbb', got {cookies_dict.get('example2')}"

    def test_cookie_jar(self, cycletls_client, httpbin_url):
        """Test cookie jar functionality with set-cookie."""
        # First request sets a cookie
        response = cycletls_client.get(f"{httpbin_url}/cookies/set?testcookie=testvalue")

        # Should either follow redirect (200) or return redirect status
        assert response.status_code in [200, 302, 303], \
            f"Cookie set should return 200 or redirect, got {response.status_code}"


class TestStatusCodes:
    """Test various HTTP status codes."""

    def test_200_ok(self, cycletls_client, httpbin_url):
        """Test successful 200 OK response."""
        response = cycletls_client.get(f"{httpbin_url}/status/200")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_404_not_found(self, cycletls_client, httpbin_url):
        """Test 404 Not Found response."""
        response = cycletls_client.get(f"{httpbin_url}/status/404")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    def test_500_server_error(self, cycletls_client, httpbin_url):
        """Test 500 Internal Server Error response."""
        response = cycletls_client.get(f"{httpbin_url}/status/500")
        assert response.status_code == 500, f"Expected 500, got {response.status_code}"

    def test_redirect_302(self, cycletls_client, httpbin_url):
        """Test 302 redirect response."""
        response = cycletls_client.get(f"{httpbin_url}/status/302")
        # Should return 302 if not following redirects, or 200 if following
        assert response.status_code in [200, 302], \
            f"Expected 200 or 302, got {response.status_code}"


class TestComplexScenarios:
    """Test complex scenarios combining multiple features."""

    def test_post_with_headers_and_cookies(self, cycletls_client, httpbin_url):
        """Test POST request with both custom headers and cookies."""
        payload = {"test": "data"}
        headers = {"Authorization": "Bearer token123"}
        cookies = [{"name": "session", "value": "abc123"}]

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            json_data=payload,
            headers=headers,
            cookies=cookies
        )
        assert_valid_response(response, expected_status=200)

        data = assert_valid_json_response(response)

        # Verify headers
        assert 'headers' in data, "Response should contain headers"
        assert 'Authorization' in data['headers'], "Authorization header should be present"

        # Verify cookies
        assert 'cookies' in data, "Response should contain cookies"
        assert 'session' in data['cookies'], "Session cookie should be present"

    def test_all_methods_return_200(self, cycletls_client, httpbin_url, firefox_ja3):
        """
        Comprehensive test matching the TypeScript integration test.
        Tests all major features: GET, POST, PUT, PATCH, DELETE, headers, cookies, etc.
        """
        test_requests = [
            # User-agent with JA3
            {
                'method': 'get',
                'url': 'https://ja3er.com/json',
                'params': {
                    'ja3': firefox_ja3,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36'
                }
            },
            # POST
            {
                'method': 'post',
                'url': f'{httpbin_url}/post',
                'params': {'body': '{"field":"POST-VAL"}'}
            },
            # PUT
            {
                'method': 'put',
                'url': f'{httpbin_url}/put',
                'params': {'body': '{"field":"PUT-VAL"}'}
            },
            # PATCH
            {
                'method': 'patch',
                'url': f'{httpbin_url}/patch',
                'params': {'body': '{"field":"PATCH-VAL"}'}
            },
            # DELETE
            {
                'method': 'delete',
                'url': f'{httpbin_url}/delete',
                'params': {'body': '{"field":"DELETE-VAL"}'}
            },
            # Headers
            {
                'method': 'get',
                'url': f'{httpbin_url}/headers',
                'params': {'headers': {'Authorization': 'Bearer someexampletoken'}}
            },
            # Cookies
            {
                'method': 'get',
                'url': f'{httpbin_url}/cookies',
                'params': {
                    'cookies': [
                        {"name": "example1", "value": "aaaaaaa", "expires": "2026-01-02T15:04:05Z"},
                        {"name": "example2", "value": "bbbbbbbbb", "expires": "2026-01-06T02:03:05Z"}
                    ]
                }
            },
            # IP
            {
                'method': 'get',
                'url': f'{httpbin_url}/ip',
                'params': {}
            },
            # Response headers
            {
                'method': 'get',
                'url': f'{httpbin_url}/response-headers?ExampleResponseHeader=HeaderisPickedUpByServer',
                'params': {}
            },
            # HTML
            {
                'method': 'get',
                'url': f'{httpbin_url}/html',
                'params': {}
            },
            # Example.com (tests TLS extension 43)
            {
                'method': 'get',
                'url': 'https://example.com',
                'params': {}
            },
        ]

        for req in test_requests:
            method = req['method']
            url = req['url']
            params = req['params']

            # Call the appropriate method
            if method == 'get':
                response = cycletls_client.get(url, **params)
            elif method == 'post':
                response = cycletls_client.post(url, **params)
            elif method == 'put':
                response = cycletls_client.put(url, **params)
            elif method == 'patch':
                response = cycletls_client.patch(url, **params)
            elif method == 'delete':
                response = cycletls_client.delete(url, **params)
            else:
                pytest.fail(f"Unknown method: {method}")

            # All requests should return 200
            assert response.status_code == 200, \
                f"Expected 200 for {method.upper()} {url}, got {response.status_code}"

            # Verify response body is not empty
            assert response.body, f"Response body should not be empty for {method.upper()} {url}"

            # For HTML responses, verify it's a string
            if '/html' in url or 'example.com' in url:
                assert isinstance(response.body, str), \
                    f"HTML response should be string for {url}"
            # For JSON endpoints, try to parse
            else:
                try:
                    data = json.loads(response.body)
                    assert isinstance(data, (dict, list)), \
                        f"JSON response should be dict or list for {url}"
                except json.JSONDecodeError:
                    # Some endpoints might return text, that's ok
                    pass
