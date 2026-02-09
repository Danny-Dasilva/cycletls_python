"""
Tests for CycleTLS module-level Simple API.

Tests the module-level convenience functions (cycletls.get(), cycletls.post(), etc.)
and configuration management (set_default(), get_default(), reset_defaults()).
"""

import pytest
import cycletls
from cycletls import HTTPError

pytestmark = pytest.mark.live


class TestModuleLevelFunctions:
    """Test suite for module-level convenience functions"""

    def setup_method(self):
        """Reset defaults before each test"""
        cycletls.reset_defaults()

    def teardown_method(self):
        """Clean up after each test"""
        cycletls.reset_defaults()
        cycletls.close_global_session()

    def test_module_get_request(self, httpbin_url):
        """Test cycletls.get() function"""
        response = cycletls.get(f"{httpbin_url}/get")

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == f"{httpbin_url}/get"

    def test_module_get_with_params(self, httpbin_url):
        """Test cycletls.get() with query parameters"""
        params = {"param1": "value1", "param2": "value2"}

        response = cycletls.get(f"{httpbin_url}/get", params=params)

        assert response.status_code == 200
        data = response.json()
        assert data["args"]["param1"] == "value1"
        assert data["args"]["param2"] == "value2"

    def test_module_get_with_headers(self, httpbin_url):
        """Test cycletls.get() with custom headers"""
        headers = {"X-Custom-Header": "test-value"}

        response = cycletls.get(f"{httpbin_url}/get", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["headers"]["X-Custom-Header"] == "test-value"

    def test_module_post_request(self, httpbin_url):
        """Test cycletls.post() function"""
        response = cycletls.post(f"{httpbin_url}/post")

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == f"{httpbin_url}/post"

    def test_module_post_with_json(self, httpbin_url):
        """Test cycletls.post() with JSON data"""
        payload = {"key1": "value1", "key2": "value2", "nested": {"data": "test"}}

        response = cycletls.post(f"{httpbin_url}/post", json_data=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["json"]["key1"] == "value1"
        assert data["json"]["key2"] == "value2"
        assert data["json"]["nested"]["data"] == "test"
        assert data["headers"]["Content-Type"] == "application/json"

    def test_module_post_with_form_data(self, httpbin_url):
        """Test cycletls.post() with form data"""
        form_data = {"field1": "value1", "field2": "value2"}

        response = cycletls.post(f"{httpbin_url}/post", data=form_data)

        assert response.status_code == 200
        data = response.json()
        assert data["form"]["field1"] == "value1"
        assert data["form"]["field2"] == "value2"

    def test_module_post_with_raw_bytes(self, httpbin_url):
        """Test cycletls.post() with raw bytes"""
        raw_data = b"raw binary data"

        response = cycletls.post(f"{httpbin_url}/post", data=raw_data)

        assert response.status_code == 200
        data = response.json()
        assert "raw binary data" in data["data"]

    def test_module_put_request(self, httpbin_url):
        """Test cycletls.put() function"""
        payload = {"key": "updated"}

        response = cycletls.put(f"{httpbin_url}/put", json_data=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["json"]["key"] == "updated"

    def test_module_patch_request(self, httpbin_url):
        """Test cycletls.patch() function"""
        payload = {"field": "patched"}

        response = cycletls.patch(f"{httpbin_url}/patch", json_data=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["json"]["field"] == "patched"

    def test_module_delete_request(self, httpbin_url):
        """Test cycletls.delete() function"""
        response = cycletls.delete(f"{httpbin_url}/delete")

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == f"{httpbin_url}/delete"

    def test_module_head_request(self, httpbin_url):
        """Test cycletls.head() function"""
        response = cycletls.head(f"{httpbin_url}/get")

        assert response.status_code == 200
        assert len(response.content) == 0  # HEAD has no body

    def test_module_options_request(self, httpbin_url):
        """Test cycletls.options() function"""
        response = cycletls.options(f"{httpbin_url}/get")

        assert response.status_code == 200
        assert "Allow" in response.headers or "allow" in response.headers

    def test_module_request_function(self, httpbin_url):
        """Test cycletls.request() generic function"""
        response = cycletls.request("GET", f"{httpbin_url}/get")

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == f"{httpbin_url}/get"


class TestConfigurationManagement:
    """Test suite for configuration management functions"""

    def setup_method(self):
        """Reset defaults before each test"""
        cycletls.reset_defaults()

    def teardown_method(self):
        """Clean up after each test"""
        cycletls.reset_defaults()
        cycletls.close_global_session()

    def test_set_default_timeout(self, httpbin_url):
        """Test setting default timeout"""
        cycletls.set_default(timeout=15)

        # Verify it was set
        assert cycletls.get_default("timeout") == 15

        # Verify it's used in requests
        response = cycletls.get(f"{httpbin_url}/get")
        assert response.status_code == 200

    def test_set_default_user_agent(self, httpbin_url):
        """Test setting default user agent"""
        custom_ua = "CustomBot/1.0"
        cycletls.set_default(user_agent=custom_ua)

        response = cycletls.get(f"{httpbin_url}/get")

        assert response.status_code == 200
        data = response.json()
        assert data["headers"]["User-Agent"] == custom_ua

    def test_set_default_headers(self, httpbin_url):
        """Test that per-request headers override defaults"""
        cycletls.set_default(user_agent="DefaultAgent/1.0")

        # Override with per-request header
        response = cycletls.get(
            f"{httpbin_url}/get", headers={"User-Agent": "OverrideAgent/2.0"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["headers"]["User-Agent"] == "OverrideAgent/2.0"

    def test_get_default_returns_none_if_not_set(self):
        """Test get_default() returns None for unset values"""
        assert cycletls.get_default("timeout") is None
        assert cycletls.get_default("proxy") is None

    def test_get_default_with_set_value(self):
        """Test get_default() returns correct value"""
        cycletls.set_default(timeout=20)
        assert cycletls.get_default("timeout") == 20

    def test_reset_defaults(self):
        """Test reset_defaults() clears all configuration"""
        cycletls.set_default(timeout=10, user_agent="TestAgent/1.0")

        # Verify values are set
        assert cycletls.get_default("timeout") == 10
        assert cycletls.get_default("user_agent") == "TestAgent/1.0"

        # Reset
        cycletls.reset_defaults()

        # Verify values are cleared
        assert cycletls.get_default("timeout") is None
        assert cycletls.get_default("user_agent") is None

    def test_module_attribute_access(self):
        """Test reading defaults via module attributes"""
        cycletls.set_default(timeout=25)

        # Access via module attribute
        assert cycletls.default_timeout == 25

    def test_module_attribute_access_unset(self):
        """Test reading unset defaults via module attributes"""
        # Should return None for unset values
        assert cycletls.default_timeout is None

    def test_invalid_config_key_raises_error(self):
        """Test that invalid configuration keys raise ValueError"""
        with pytest.raises(ValueError, match="Unknown configuration option"):
            cycletls.set_default(invalid_key="value")

    def test_invalid_config_value_raises_error(self):
        """Test that invalid configuration values raise ValueError"""
        with pytest.raises(ValueError, match="Invalid value"):
            cycletls.set_default(timeout="not_a_number")

    def test_set_multiple_defaults(self, httpbin_url):
        """Test setting multiple defaults at once"""
        cycletls.set_default(
            timeout=30, user_agent="MultiBot/1.0", enable_connection_reuse=True
        )

        assert cycletls.get_default("timeout") == 30
        assert cycletls.get_default("user_agent") == "MultiBot/1.0"
        assert cycletls.get_default("enable_connection_reuse") is True

        # Verify they're used in requests
        response = cycletls.get(f"{httpbin_url}/get")
        assert response.status_code == 200
        data = response.json()
        assert data["headers"]["User-Agent"] == "MultiBot/1.0"

    def test_per_request_overrides_defaults(self, httpbin_url):
        """Test that per-request options override defaults"""
        cycletls.set_default(timeout=10, user_agent="DefaultAgent/1.0")

        # Override timeout and user agent per-request
        response = cycletls.get(
            f"{httpbin_url}/get", timeout=5, user_agent="CustomAgent/2.0"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["headers"]["User-Agent"] == "CustomAgent/2.0"


class TestGlobalSession:
    """Test suite for global session management"""

    def teardown_method(self):
        """Clean up after each test"""
        cycletls.reset_defaults()
        cycletls.close_global_session()

    def test_close_global_session(self, httpbin_url):
        """Test manually closing the global session"""
        # Make a request (creates global session)
        response1 = cycletls.get(f"{httpbin_url}/get")
        assert response1.status_code == 200

        # Close the session
        cycletls.close_global_session()

        # Make another request (creates new session)
        response2 = cycletls.get(f"{httpbin_url}/get")
        assert response2.status_code == 200

    def test_global_session_reused_across_requests(self, httpbin_url):
        """Test that global session is reused for multiple requests"""
        # Enable connection reuse to verify same session is used
        cycletls.set_default(enable_connection_reuse=True)

        response1 = cycletls.get(f"{httpbin_url}/get")
        response2 = cycletls.get(f"{httpbin_url}/get")
        response3 = cycletls.get(f"{httpbin_url}/get")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200


class TestTLSFingerprintingWithModuleAPI:
    """Test TLS fingerprinting with module-level API"""

    def setup_method(self):
        """Reset defaults before each test"""
        cycletls.reset_defaults()

    def teardown_method(self):
        """Clean up after each test"""
        cycletls.reset_defaults()
        cycletls.close_global_session()

    def test_ja3_fingerprint_as_default(self, chrome_ja3):
        """Test using JA3 fingerprint as default"""
        cycletls.set_default(ja3=chrome_ja3)

        response = cycletls.get("https://tls.peet.ws/api/clean")

        assert response.status_code == 200
        data = response.json()
        assert "ja3_hash" in data

    def test_ja3_fingerprint_per_request(self, firefox_ja3):
        """Test using JA3 fingerprint per-request"""
        response = cycletls.get("https://tls.peet.ws/api/clean", ja3=firefox_ja3)

        assert response.status_code == 200
        data = response.json()
        assert "ja3_hash" in data


class TestErrorHandling:
    """Test error handling with module-level API"""

    def teardown_method(self):
        """Clean up after each test"""
        cycletls.reset_defaults()
        cycletls.close_global_session()

    def test_http_error_with_raise_for_status(self, httpbin_url):
        """Test HTTPError is raised for 404"""
        response = cycletls.get(f"{httpbin_url}/status/404")

        assert response.status_code == 404

        with pytest.raises(HTTPError) as exc_info:
            response.raise_for_status()

        assert exc_info.value.response.status_code == 404

    def test_response_properties(self, httpbin_url):
        """Test response object properties"""
        response = cycletls.get(f"{httpbin_url}/get")

        assert response.status_code == 200
        assert response.ok is True
        assert response.is_error is False
        assert response.text is not None
        assert response.content is not None
        assert len(response.headers) > 0


class TestCookies:
    """Test cookie handling with module-level API"""

    def teardown_method(self):
        """Clean up after each test"""
        cycletls.reset_defaults()
        cycletls.close_global_session()

    def test_send_cookies_as_dict(self, httpbin_url):
        """Test sending cookies as a dictionary"""
        cookies = {"session_id": "abc123", "user_token": "xyz789"}

        response = cycletls.get(f"{httpbin_url}/cookies", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert data["cookies"]["session_id"] == "abc123"
        assert data["cookies"]["user_token"] == "xyz789"

    def test_response_cookies(self, httpbin_url):
        """Test receiving cookies from response"""
        response = cycletls.get(f"{httpbin_url}/cookies/set?test_cookie=test_value")

        assert response.status_code == 200
        # Check if cookie was set
        if "test_cookie" in response.cookies:
            assert response.cookies["test_cookie"] == "test_value"


class TestThreadSafety:
    """Test thread safety of module-level API"""

    def teardown_method(self):
        """Clean up after each test"""
        cycletls.reset_defaults()
        cycletls.close_global_session()

    def test_concurrent_requests(self, httpbin_url):
        """Test that concurrent requests work correctly"""
        import threading

        results = []

        def make_request(path):
            response = cycletls.get(f"{httpbin_url}{path}")
            results.append(response.status_code)

        threads = [
            threading.Thread(target=make_request, args=("/get",)) for _ in range(5)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All requests should succeed
        assert len(results) == 5
        assert all(status == 200 for status in results)
