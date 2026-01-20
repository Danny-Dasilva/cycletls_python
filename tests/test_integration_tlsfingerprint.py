"""
Integration Tests against tlsfingerprint.com

Tests HTTP methods, headers, response parsing, and other integration
functionality against the live tlsfingerprint.com service.

Run with: pytest tests/test_integration_tlsfingerprint.py -v -m live
Skip with: pytest -m "not live"

Based on: test_integration.py
"""
import pytest
from cycletls import CycleTLS

# Mark all tests in this module as live tests
pytestmark = pytest.mark.live

# Base URL for tlsfingerprint.com
BASE_URL = "https://tlsfingerprint.com"


@pytest.fixture(scope="module")
def cycle_client():
    """Create a single CycleTLS client for all tests in this module"""
    with CycleTLS() as client:
        yield client


class TestBasicRequests:
    """Test basic HTTP request functionality"""

    def test_basic_get_request(self, cycle_client):
        """Test basic GET request"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        assert response.body, "Response body should not be empty"

    def test_get_api_clean(self, cycle_client):
        """Test GET to /api/clean endpoint"""
        response = cycle_client.get(f"{BASE_URL}/api/clean")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict), "Response should be JSON object"

    def test_get_api_tls(self, cycle_client):
        """Test GET to /api/tls endpoint"""
        response = cycle_client.get(f"{BASE_URL}/api/tls")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict), "Response should be JSON object"


class TestHTTPMethods:
    """Test various HTTP methods"""

    def test_get_method(self, cycle_client):
        """Test GET request method"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        data = response.json()
        assert data.get("method") == "GET", f"Method should be GET, got {data.get('method')}"

    def test_post_method(self, cycle_client):
        """Test POST request method"""
        response = cycle_client.post(
            f"{BASE_URL}/api/all",
            data='{"test": "data"}'
        )

        # POST may return 200 or 405 depending on endpoint support
        assert response.status_code in [200, 405], \
            f"POST should return 200 or 405, got {response.status_code}"

    def test_head_method(self, cycle_client):
        """Test HEAD request method"""
        response = cycle_client.head(f"{BASE_URL}/api/all")

        # HEAD should return 200 or 405
        assert response.status_code in [200, 405], \
            f"HEAD should return 200 or 405, got {response.status_code}"


class TestCustomHeaders:
    """Test custom header functionality"""

    def test_custom_user_agent(self, cycle_client):
        """Test custom user-agent is sent"""
        custom_ua = "CycleTLS-Python-Test/1.0"

        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            user_agent=custom_ua
        )

        assert response.status_code == 200
        data = response.json()

        # Check if user-agent is echoed back
        assert data.get("user_agent") == custom_ua, \
            f"User-agent should be {custom_ua}, got {data.get('user_agent')}"

    def test_custom_headers(self, cycle_client):
        """Test custom headers are sent"""
        headers = {
            "X-Custom-Header": "test-value",
            "Accept-Language": "en-US"
        }

        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            headers=headers
        )

        assert response.status_code == 200

    def test_header_order(self, cycle_client):
        """Test header order preservation"""
        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            header_order=["accept", "accept-language", "accept-encoding"]
        )

        assert response.status_code == 200


class TestResponseParsing:
    """Test response parsing functionality"""

    def test_json_response(self, cycle_client):
        """Test JSON response parsing"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200

        # Test .json() method
        data = response.json()
        assert isinstance(data, dict), "Parsed JSON should be dict"

    def test_text_response(self, cycle_client):
        """Test text response access"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        assert response.body, "Response body should not be empty"
        assert isinstance(response.body, str), "Body should be string"

    def test_response_headers(self, cycle_client):
        """Test response headers access"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        assert hasattr(response, 'headers'), "Response should have headers"

        # Headers should be dict-like
        assert hasattr(response.headers, 'items'), "Headers should be dict-like"

        # Check for Content-Type
        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        assert 'content-type' in headers_lower, "Content-Type should be present"


class TestTimeouts:
    """Test timeout functionality"""

    def test_request_with_timeout(self, cycle_client):
        """Test request with explicit timeout"""
        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            timeout=30000  # 30 seconds
        )

        assert response.status_code == 200

    def test_request_default_timeout(self, cycle_client):
        """Test request with default timeout"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200


class TestRedirects:
    """Test redirect functionality"""

    def test_follows_redirects_default(self, cycle_client):
        """Test that redirects are followed by default"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        # Should reach final destination
        assert response.status_code == 200

    def test_disable_redirect(self, cycle_client):
        """Test disabling redirect following"""
        response = cycle_client.get(
            f"{BASE_URL}/api/all",
            disable_redirect=True
        )

        # Should get 200 or 3xx
        assert response.status_code in [200, 301, 302, 303, 307, 308], \
            f"Expected 200 or redirect status, got {response.status_code}"


class TestConnectionManagement:
    """Test connection management functionality"""

    def test_multiple_requests_same_client(self, cycle_client):
        """Test multiple requests reuse connection"""
        for i in range(3):
            response = cycle_client.get(f"{BASE_URL}/api/clean")
            assert response.status_code == 200, f"Request {i+1} failed"

    def test_rapid_requests(self, cycle_client):
        """Test rapid sequential requests"""
        responses = []
        for _ in range(5):
            response = cycle_client.get(f"{BASE_URL}/api/clean")
            responses.append(response)

        # All should succeed
        for i, resp in enumerate(responses):
            assert resp.status_code == 200, f"Request {i+1} failed"


class TestClientArchitecture:
    """Test client instantiation and architecture"""

    def test_single_client(self, cycle_client):
        """Test single client instance"""
        response = cycle_client.get(f"{BASE_URL}/api/all")
        assert response.status_code == 200

    def test_multiple_clients(self):
        """Test multiple client instances"""
        with CycleTLS() as client1, CycleTLS() as client2:
            response1 = client1.get(f"{BASE_URL}/api/clean")
            response2 = client2.get(f"{BASE_URL}/api/clean")

            assert response1.status_code == 200
            assert response2.status_code == 200


class TestAPIEndpoints:
    """Test all tlsfingerprint.com API endpoints"""

    def test_api_all(self, cycle_client):
        """Test /api/all endpoint returns comprehensive data"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        data = response.json()

        # Should contain multiple data sections
        expected_keys = ["tls", "http2"]
        for key in expected_keys:
            assert key in data, f"Response should contain '{key}'"

    def test_api_clean(self, cycle_client):
        """Test /api/clean endpoint returns fingerprint data"""
        response = cycle_client.get(f"{BASE_URL}/api/clean")

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0, "Response should contain fingerprint data"

    def test_api_tls(self, cycle_client):
        """Test /api/tls endpoint returns TLS data"""
        response = cycle_client.get(f"{BASE_URL}/api/tls")

        assert response.status_code == 200
        data = response.json()

        # Should focus on TLS data
        has_tls = any(key in str(data).lower() for key in ["ja3", "ja4", "cipher", "tls"])
        assert has_tls, "Response should contain TLS-related data"


class TestResponseMetadata:
    """Test response metadata from tlsfingerprint.com"""

    def test_ip_returned(self, cycle_client):
        """Test that client IP is returned"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        data = response.json()

        assert "ip" in data, "Response should contain client IP"

    def test_http_version_returned(self, cycle_client):
        """Test that HTTP version is returned"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        data = response.json()

        assert "http_version" in data, "Response should contain HTTP version"

    def test_method_returned(self, cycle_client):
        """Test that request method is returned"""
        response = cycle_client.get(f"{BASE_URL}/api/all")

        assert response.status_code == 200
        data = response.json()

        assert "method" in data, "Response should contain request method"
        assert data["method"] == "GET", "Method should be GET"
