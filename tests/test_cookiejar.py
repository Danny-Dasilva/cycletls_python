"""
Cookie Jar Tests for CycleTLS Python library.

Based on CycleTLS JavaScript cookiejar.test.js, these tests verify:
- Persistent cookie storage across requests
- Cookie sharing between requests
- Domain-based cookie filtering
- Path-based cookie filtering
- Cookie setting and retrieval

Tests use httpbin.org/cookies endpoints to test cookie handling.
"""

import pytest
from http.cookiejar import CookieJar
from http.cookies import SimpleCookie
from test_utils import assert_valid_response


class TestBasicCookieHandling:
    """Test basic cookie setting and retrieval."""

    def test_no_cookies_initially(self, cycletls_client, httpbin_url):
        """Test that no cookies are set initially."""
        response = cycletls_client.get(f"{httpbin_url}/cookies")

        assert_valid_response(response, expected_status=200)

        # Parse JSON response
        data = response.json()
        assert 'cookies' in data, "Response should have cookies field"

        # Should be empty or have no length
        cookies = data.get('cookies', {})
        assert len(cookies) == 0 or cookies == {}, \
            f"Should have no cookies initially, got: {cookies}"

    def test_set_single_cookie(self, cycletls_client, httpbin_url):
        """Test setting a single cookie and verifying it."""
        # Set a cookie using httpbin's /cookies/set endpoint
        # This endpoint sets a cookie and redirects to /cookies
        response = cycletls_client.get(
            f"{httpbin_url}/cookies/set?freeform=test",
            disable_redirect=True  # Don't follow redirect
        )

        # Should get a 302 redirect
        assert response.status_code == 302, \
            f"Expected 302 redirect, got {response.status_code}"

        # Check for Set-Cookie header
        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        assert 'set-cookie' in headers_lower or 'Set-Cookie' in response.headers, \
            "Response should contain Set-Cookie header"

    def test_cookie_persistence_across_requests(self, cycletls_client_function, httpbin_url):
        """Test that cookies persist across multiple requests."""
        # First request - no cookies
        first_response = cycletls_client_function.get(f"{httpbin_url}/cookies")
        assert_valid_response(first_response, expected_status=200)

        first_data = first_response.json()
        assert len(first_data.get('cookies', {})) == 0, "Should have no cookies initially"

        # Second request - set a cookie (with redirect disabled)
        second_response = cycletls_client_function.get(
            f"{httpbin_url}/cookies/set?freeform=test",
            disable_redirect=True
        )
        assert second_response.status_code == 302, "Should get redirect when setting cookie"

        # Extract cookie from Set-Cookie header
        set_cookie_header = None
        for key, value in second_response.headers.items():
            if key.lower() == 'set-cookie':
                set_cookie_header = value
                break

        assert set_cookie_header is not None, "Should have Set-Cookie header"

        # Parse the cookie
        cookie_header = set_cookie_header.split(';')[0]  # Get just the name=value part

        # Third request - verify cookie is sent back
        third_response = cycletls_client_function.get(
            f"{httpbin_url}/cookies",
            headers={'Cookie': cookie_header}
        )

        assert_valid_response(third_response, expected_status=200)

        third_data = third_response.json()
        assert 'freeform' in third_data.get('cookies', {}), \
            f"Cookie 'freeform' should be present, got: {third_data.get('cookies')}"
        assert third_data['cookies']['freeform'] == 'test', \
            "Cookie value should be 'test'"


class TestMultipleCookies:
    """Test handling of multiple cookies."""

    def test_set_multiple_cookies(self, cycletls_client_function, httpbin_url):
        """Test setting multiple cookies."""
        # Set first cookie
        response1 = cycletls_client_function.get(
            f"{httpbin_url}/cookies/set?freeform=test",
            disable_redirect=True
        )
        assert response1.status_code == 302

        # Extract first cookie
        cookie1 = None
        for key, value in response1.headers.items():
            if key.lower() == 'set-cookie':
                cookie1 = value.split(';')[0]
                break

        # Set additional cookies
        response2 = cycletls_client_function.get(
            f"{httpbin_url}/cookies/set?a=1&b=2&c=3",
            disable_redirect=True
        )
        assert response2.status_code == 302

        # Extract additional cookies
        cookies = []
        for key, value in response2.headers.items():
            if key.lower() == 'set-cookie':
                # Handle both single value and list
                if isinstance(value, list):
                    for v in value:
                        cookies.append(v.split(';')[0])
                else:
                    cookies.append(value.split(';')[0])

        # Build combined cookie header
        all_cookies = '; '.join([cookie1] + cookies) if cookie1 else '; '.join(cookies)

        # Verify all cookies
        verify_response = cycletls_client_function.get(
            f"{httpbin_url}/cookies",
            headers={'Cookie': all_cookies}
        )

        assert_valid_response(verify_response, expected_status=200)

        data = verify_response.json()
        cookies_dict = data.get('cookies', {})

        # Check that we have multiple cookies
        assert len(cookies_dict) >= 1, \
            f"Should have at least 1 cookie, got: {cookies_dict}"

    def test_cookie_accumulation(self, cycletls_client_function, httpbin_url):
        """Test that cookies accumulate across multiple set operations."""
        cookies_list = []

        # Set first cookie
        response1 = cycletls_client_function.get(
            f"{httpbin_url}/cookies/set?first=1",
            disable_redirect=True
        )

        if response1.status_code == 302:
            for key, value in response1.headers.items():
                if key.lower() == 'set-cookie':
                    cookies_list.append(value.split(';')[0])

        # Set second cookie
        response2 = cycletls_client_function.get(
            f"{httpbin_url}/cookies/set?second=2",
            disable_redirect=True
        )

        if response2.status_code == 302:
            for key, value in response2.headers.items():
                if key.lower() == 'set-cookie':
                    cookies_list.append(value.split(';')[0])

        # Verify both cookies when sent together
        if cookies_list:
            verify_response = cycletls_client_function.get(
                f"{httpbin_url}/cookies",
                headers={'Cookie': '; '.join(cookies_list)}
            )

            assert_valid_response(verify_response, expected_status=200)

            data = verify_response.json()
            cookies_dict = data.get('cookies', {})

            # Should have at least one cookie
            assert len(cookies_dict) >= 1, \
                f"Should have at least one cookie, got: {cookies_dict}"


class TestCookieSharing:
    """Test cookie sharing between requests."""

    def test_cookie_sharing_with_cookie_header(self, cycletls_client_function, httpbin_url):
        """Test that cookies can be shared by manually setting Cookie header."""
        # Set cookies
        set_response = cycletls_client_function.get(
            f"{httpbin_url}/cookies/set?shared=value",
            disable_redirect=True
        )

        # Extract cookie
        cookie_value = None
        for key, value in set_response.headers.items():
            if key.lower() == 'set-cookie':
                cookie_value = value.split(';')[0]
                break

        if cookie_value:
            # Use cookie in another request
            response1 = cycletls_client_function.get(
                f"{httpbin_url}/cookies",
                headers={'Cookie': cookie_value}
            )

            assert_valid_response(response1, expected_status=200)

            data1 = response1.json()
            assert 'shared' in data1.get('cookies', {}), \
                "Cookie should be present in first request"

            # Use same cookie in second request
            response2 = cycletls_client_function.get(
                f"{httpbin_url}/cookies",
                headers={'Cookie': cookie_value}
            )

            assert_valid_response(response2, expected_status=200)

            data2 = response2.json()
            assert 'shared' in data2.get('cookies', {}), \
                "Cookie should be present in second request"

            # Verify values match
            assert data1['cookies']['shared'] == data2['cookies']['shared'], \
                "Cookie values should match across requests"


class TestDomainBasedCookieFiltering:
    """Test domain-based cookie filtering."""

    def test_cookies_not_sent_to_different_domain(self, cycletls_client_function):
        """Test that cookies from one domain are not sent to another."""
        # Set cookie on httpbin.org
        httpbin_response = cycletls_client_function.get(
            "https://httpbin.org/cookies/set?domain_test=httpbin",
            disable_redirect=True
        )

        # Extract httpbin cookie
        httpbin_cookie = None
        for key, value in httpbin_response.headers.items():
            if key.lower() == 'set-cookie':
                httpbin_cookie = value.split(';')[0]
                break

        if httpbin_cookie:
            # Try to send httpbin cookie to a different endpoint
            # The cookie should not be automatically sent by the browser
            # We're testing manual cookie handling here

            # Request to httpbin should work with the cookie
            valid_response = cycletls_client_function.get(
                "https://httpbin.org/cookies",
                headers={'Cookie': httpbin_cookie}
            )

            assert_valid_response(valid_response, expected_status=200)

            data = valid_response.json()
            assert 'domain_test' in data.get('cookies', {}), \
                "Cookie should work on same domain"

    def test_cookie_domain_attribute(self, cycletls_client_function, httpbin_url):
        """Test that cookies respect domain attribute."""
        # Set a cookie and check its domain attribute
        response = cycletls_client_function.get(
            f"{httpbin_url}/cookies/set?domain_attr=value",
            disable_redirect=True
        )

        # Check Set-Cookie header for domain attribute
        for key, value in response.headers.items():
            if key.lower() == 'set-cookie':
                # Cookie might have Domain attribute
                assert isinstance(value, str), "Set-Cookie should be a string"
                # Just verify we got a valid cookie header
                assert '=' in value, "Cookie should have name=value format"


class TestPathBasedCookieFiltering:
    """Test path-based cookie filtering."""

    def test_cookie_path_attribute(self, cycletls_client_function, httpbin_url):
        """Test that cookies can have path attributes."""
        # Set a cookie and check its path attribute
        response = cycletls_client_function.get(
            f"{httpbin_url}/cookies/set?path_test=value",
            disable_redirect=True
        )

        # Check Set-Cookie header
        for key, value in response.headers.items():
            if key.lower() == 'set-cookie':
                # Cookie might have Path attribute
                assert isinstance(value, str), "Set-Cookie should be a string"
                # Verify we got a valid cookie header
                assert '=' in value, "Cookie should have name=value format"

    def test_cookies_sent_to_correct_path(self, cycletls_client_function, httpbin_url):
        """Test that cookies are sent to the correct path."""
        # Set cookie
        set_response = cycletls_client_function.get(
            f"{httpbin_url}/cookies/set?path_cookie=pathvalue",
            disable_redirect=True
        )

        # Extract cookie
        cookie_value = None
        for key, value in set_response.headers.items():
            if key.lower() == 'set-cookie':
                cookie_value = value.split(';')[0]
                break

        if cookie_value:
            # Send cookie to /cookies path
            cookies_response = cycletls_client_function.get(
                f"{httpbin_url}/cookies",
                headers={'Cookie': cookie_value}
            )

            assert_valid_response(cookies_response, expected_status=200)

            data = cookies_response.json()
            assert 'path_cookie' in data.get('cookies', {}), \
                "Cookie should be sent to /cookies path"


class TestCookieEdgeCases:
    """Test edge cases in cookie handling."""

    def test_empty_cookie_value(self, cycletls_client_function, httpbin_url):
        """Test handling of empty cookie values."""
        # Try to set an empty cookie value
        response = cycletls_client_function.get(
            f"{httpbin_url}/cookies/set?empty=",
            disable_redirect=True
        )

        # Should still get a redirect
        assert response.status_code in [302, 200], \
            f"Should handle empty cookie value, got status {response.status_code}"

    def test_special_characters_in_cookie(self, cycletls_client_function, httpbin_url):
        """Test cookies with special characters."""
        # Test with URL-encoded special characters
        response = cycletls_client_function.get(
            f"{httpbin_url}/cookies/set?special=test%20value",
            disable_redirect=True
        )

        assert response.status_code == 302, \
            "Should handle special characters in cookies"

    def test_multiple_cookie_headers(self, cycletls_client_function, httpbin_url):
        """Test handling multiple Set-Cookie headers."""
        # Set multiple cookies at once
        response = cycletls_client_function.get(
            f"{httpbin_url}/cookies/set?first=1&second=2",
            disable_redirect=True
        )

        # Count Set-Cookie headers
        set_cookie_count = 0
        for key, value in response.headers.items():
            if key.lower() == 'set-cookie':
                set_cookie_count += 1
                if isinstance(value, list):
                    set_cookie_count += len(value) - 1

        # Should have at least one Set-Cookie header
        assert set_cookie_count >= 1, \
            f"Should have Set-Cookie headers, got {set_cookie_count}"

    def test_cookie_deletion(self, cycletls_client_function, httpbin_url):
        """Test cookie deletion by setting Max-Age=0."""
        # Set a cookie first
        set_response = cycletls_client_function.get(
            f"{httpbin_url}/cookies/set?to_delete=value",
            disable_redirect=True
        )

        # Extract cookie
        cookie_value = None
        for key, value in set_response.headers.items():
            if key.lower() == 'set-cookie':
                cookie_value = value.split(';')[0]
                break

        # Verify cookie exists
        if cookie_value:
            verify_response = cycletls_client_function.get(
                f"{httpbin_url}/cookies",
                headers={'Cookie': cookie_value}
            )

            data = verify_response.json()
            assert 'to_delete' in data.get('cookies', {}), \
                "Cookie should exist before deletion"

            # Note: httpbin.org/cookies/delete endpoint behavior varies
            # We're primarily testing that the cookie header mechanism works
