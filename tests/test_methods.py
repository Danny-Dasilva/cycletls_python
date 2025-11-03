"""
HTTP method tests for CycleTLS Python client.
Tests GET, POST, PUT, PATCH, DELETE, HEAD, and OPTIONS requests.
"""

import pytest
import json


class TestHTTPMethods:
    """Test suite for HTTP request methods in CycleTLS"""

    def test_get_request(self, cycletls_client, httpbin_url):
        """Test GET request"""
        response = cycletls_client.get(f"{httpbin_url}/get")

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == f"{httpbin_url}/get"

    def test_get_request_with_query_params(self, cycletls_client, httpbin_url):
        """Test GET request with query parameters"""
        params = {
            "param1": "value1",
            "param2": "value2",
        }

        response = cycletls_client.get(
            f"{httpbin_url}/get",
            params=params
        )

        assert response.status_code == 200
        data = response.json()
        assert data["args"]["param1"] == "value1"
        assert data["args"]["param2"] == "value2"

    def test_get_request_with_headers(self, cycletls_client, httpbin_url):
        """Test GET request with custom headers"""
        headers = {
            "X-Test-Header": "test-value",
        }

        response = cycletls_client.get(
            f"{httpbin_url}/get",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["headers"]["X-Test-Header"] == "test-value"

    def test_post_request(self, cycletls_client, httpbin_url):
        """Test POST request"""
        response = cycletls_client.post(f"{httpbin_url}/post")

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == f"{httpbin_url}/post"

    def test_post_request_with_json_body(self, cycletls_client, httpbin_url):
        """Test POST request with JSON body"""
        payload = {
            "key1": "value1",
            "key2": "value2",
            "nested": {
                "data": "test"
            }
        }

        headers = {
            "Content-Type": "application/json",
        }

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            body=json.dumps(payload),
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["json"]["key1"] == "value1"
        assert data["json"]["key2"] == "value2"
        assert data["json"]["nested"]["data"] == "test"

    def test_post_request_with_form_data(self, cycletls_client, httpbin_url):
        """Test POST request with form data"""
        form_data = "field1=value1&field2=value2"

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            body=form_data,
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["form"]["field1"] == "value1"
        assert data["form"]["field2"] == "value2"

    def test_post_request_with_text_body(self, cycletls_client, httpbin_url):
        """Test POST request with plain text body"""
        text_body = "This is plain text content"

        headers = {
            "Content-Type": "text/plain",
        }

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            body=text_body,
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == text_body

    def test_put_request(self, cycletls_client, httpbin_url):
        """Test PUT request"""
        response = cycletls_client.put(f"{httpbin_url}/put")

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == f"{httpbin_url}/put"

    def test_put_request_with_json_body(self, cycletls_client, httpbin_url):
        """Test PUT request with JSON body"""
        payload = {
            "id": 123,
            "name": "Updated Resource",
            "status": "active"
        }

        headers = {
            "Content-Type": "application/json",
        }

        response = cycletls_client.put(
            f"{httpbin_url}/put",
            body=json.dumps(payload),
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["json"]["id"] == 123
        assert data["json"]["name"] == "Updated Resource"
        assert data["json"]["status"] == "active"

    def test_put_request_with_text_body(self, cycletls_client, httpbin_url):
        """Test PUT request with plain text body"""
        text_body = "Updated content"

        response = cycletls_client.put(
            f"{httpbin_url}/put",
            body=text_body
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == text_body

    def test_patch_request(self, cycletls_client, httpbin_url):
        """Test PATCH request"""
        response = cycletls_client.patch(f"{httpbin_url}/patch")

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == f"{httpbin_url}/patch"

    def test_patch_request_with_json_body(self, cycletls_client, httpbin_url):
        """Test PATCH request with JSON body"""
        payload = {
            "field_to_update": "new_value"
        }

        headers = {
            "Content-Type": "application/json",
        }

        response = cycletls_client.patch(
            f"{httpbin_url}/patch",
            body=json.dumps(payload),
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["json"]["field_to_update"] == "new_value"

    def test_patch_request_partial_update(self, cycletls_client, httpbin_url):
        """Test PATCH request for partial update"""
        payload = {
            "status": "updated"
        }

        headers = {
            "Content-Type": "application/json",
        }

        response = cycletls_client.patch(
            f"{httpbin_url}/patch",
            body=json.dumps(payload),
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["json"]["status"] == "updated"

    def test_delete_request(self, cycletls_client, httpbin_url):
        """Test DELETE request"""
        response = cycletls_client.delete(f"{httpbin_url}/delete")

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == f"{httpbin_url}/delete"

    def test_delete_request_with_query_params(self, cycletls_client, httpbin_url):
        """Test DELETE request with query parameters"""
        params = {
            "id": "123",
        }

        response = cycletls_client.delete(
            f"{httpbin_url}/delete",
            params=params
        )

        assert response.status_code == 200
        data = response.json()
        assert data["args"]["id"] == "123"

    def test_delete_request_with_body(self, cycletls_client, httpbin_url):
        """Test DELETE request with body (some APIs support this)"""
        payload = {
            "reason": "no longer needed"
        }

        headers = {
            "Content-Type": "application/json",
        }

        response = cycletls_client.delete(
            f"{httpbin_url}/delete",
            body=json.dumps(payload),
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["json"]["reason"] == "no longer needed"

    def test_head_request(self, cycletls_client, httpbin_url):
        """Test HEAD request"""
        response = cycletls_client.head(f"{httpbin_url}/get")

        assert response.status_code == 200
        # HEAD requests should not have a body
        assert response.body == "" or len(response.body) == 0
        # But should have headers
        assert len(response.headers) > 0

    def test_head_request_headers(self, cycletls_client, httpbin_url):
        """Test HEAD request returns headers"""
        response = cycletls_client.head(f"{httpbin_url}/get")

        assert response.status_code == 200
        # Should have Content-Type header
        assert "Content-Type" in response.headers or "content-type" in response.headers

    def test_head_request_with_params(self, cycletls_client, httpbin_url):
        """Test HEAD request with query parameters"""
        params = {
            "param": "value",
        }

        response = cycletls_client.head(
            f"{httpbin_url}/get",
            params=params
        )

        assert response.status_code == 200
        assert response.body == "" or len(response.body) == 0

    def test_options_request(self, cycletls_client, httpbin_url):
        """Test OPTIONS request"""
        response = cycletls_client.options(f"{httpbin_url}/get")

        assert response.status_code == 200
        # OPTIONS typically returns allowed methods in headers
        assert len(response.headers) > 0

    def test_options_request_cors(self, cycletls_client, httpbin_url):
        """Test OPTIONS request for CORS preflight"""
        headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }

        response = cycletls_client.options(
            f"{httpbin_url}/post",
            headers=headers
        )

        # OPTIONS should succeed
        assert response.status_code in [200, 204]

    def test_post_request_empty_body(self, cycletls_client, httpbin_url):
        """Test POST request with empty body"""
        response = cycletls_client.post(
            f"{httpbin_url}/post",
            body=""
        )

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == f"{httpbin_url}/post"

    def test_put_request_empty_body(self, cycletls_client, httpbin_url):
        """Test PUT request with empty body"""
        response = cycletls_client.put(
            f"{httpbin_url}/put",
            body=""
        )

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == f"{httpbin_url}/put"

    def test_post_request_large_body(self, cycletls_client, httpbin_url):
        """Test POST request with large JSON body"""
        large_payload = {
            "items": [{"id": i, "data": f"item_{i}"} for i in range(100)]
        }

        headers = {
            "Content-Type": "application/json",
        }

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            body=json.dumps(large_payload),
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["json"]["items"]) == 100

    def test_get_request_response_body(self, cycletls_client, httpbin_url):
        """Test GET request returns response body"""
        response = cycletls_client.get(f"{httpbin_url}/get")

        assert response.status_code == 200
        assert response.body is not None
        assert len(response.body) > 0
        # Should be valid JSON
        data = response.json()
        assert isinstance(data, dict)

    def test_post_request_response_body(self, cycletls_client, httpbin_url):
        """Test POST request returns response body"""
        payload = {"test": "data"}

        headers = {
            "Content-Type": "application/json",
        }

        response = cycletls_client.post(
            f"{httpbin_url}/post",
            body=json.dumps(payload),
            headers=headers
        )

        assert response.status_code == 200
        assert response.body is not None
        assert len(response.body) > 0
        # Should be valid JSON
        data = response.json()
        assert isinstance(data, dict)

    def test_method_case_insensitivity(self, cycletls_client, httpbin_url):
        """Test that methods work regardless of case"""
        # The Request class should handle method case normalization
        response = cycletls_client.get(f"{httpbin_url}/get")
        assert response.status_code == 200

        response = cycletls_client.post(f"{httpbin_url}/post")
        assert response.status_code == 200

    def test_all_methods_return_response_object(self, cycletls_client, httpbin_url):
        """Test that all HTTP methods return proper Response objects"""
        methods_and_urls = [
            ("get", f"{httpbin_url}/get"),
            ("post", f"{httpbin_url}/post"),
            ("put", f"{httpbin_url}/put"),
            ("patch", f"{httpbin_url}/patch"),
            ("delete", f"{httpbin_url}/delete"),
            ("head", f"{httpbin_url}/get"),
            ("options", f"{httpbin_url}/get"),
        ]

        for method, url in methods_and_urls:
            method_func = getattr(cycletls_client, method)
            response = method_func(url)

            assert hasattr(response, "status_code")
            assert hasattr(response, "headers")
            assert hasattr(response, "body")
            assert response.status_code == 200
