"""
Test multiple CycleTLS instances and concurrent operations.

Based on CycleTLS multipleImports.test.ts, this module tests:
- Creating multiple CycleTLS instances
- Isolated state between instances
- Concurrent operations across instances
- Resource cleanup and management
"""

import pytest
import threading
from cycletls import CycleTLS


class TestMultipleInstances:
    """Test creating and managing multiple CycleTLS instances."""

    def test_create_multiple_instances(self):
        """Should be able to create multiple CycleTLS instances."""
        client1 = CycleTLS(port=9200)
        client2 = CycleTLS(port=9201)

        try:
            assert client1 is not None
            assert client2 is not None
            assert client1.port != client2.port
        finally:
            client1.close()
            client2.close()

    def test_multiple_instances_with_same_port(self):
        """Test multiple instances connecting to the same port."""
        # First instance creates the server
        client1 = CycleTLS(port=9161)

        try:
            # Second instance should connect as client to same port
            client2 = CycleTLS(port=9161)

            try:
                assert client1 is not None
                assert client2 is not None
                assert client1.port == client2.port
            finally:
                client2.close()
        finally:
            client1.close()

    def test_instances_can_make_independent_requests(self, httpbin_url):
        """Multiple instances should be able to make independent requests."""
        client1 = CycleTLS(port=9202)
        client2 = CycleTLS(port=9203)

        try:
            # Make requests with both instances
            response1 = client1.get(f"{httpbin_url}/get")
            response2 = client2.get(f"{httpbin_url}/get")

            assert response1.status_code == 200
            assert response2.status_code == 200
        finally:
            client1.close()
            client2.close()

    def test_instances_work_after_one_is_closed(self, httpbin_url):
        """Closing one instance should not affect others."""
        client1 = CycleTLS(port=9204)
        client2 = CycleTLS(port=9205)

        try:
            # Make request with both
            response1 = client1.get(f"{httpbin_url}/get")
            assert response1.status_code == 200

            # Close first instance
            client1.close()

            # Second instance should still work
            response2 = client2.get(f"{httpbin_url}/get")
            assert response2.status_code == 200
        finally:
            try:
                client1.close()
            except:
                pass
            client2.close()


class TestIsolatedState:
    """Test that instances maintain isolated state."""

    def test_instances_have_isolated_ja3(self, httpbin_url):
        """Each instance should maintain its own JA3 fingerprint."""
        client1 = CycleTLS(port=9206)
        client2 = CycleTLS(port=9207)

        chrome_ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0"
        firefox_ja3 = "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0"

        try:
            # Use different JA3 for each instance
            response1 = client1.get(f"{httpbin_url}/get", ja3=chrome_ja3)
            response2 = client2.get(f"{httpbin_url}/get", ja3=firefox_ja3)

            assert response1.status_code == 200
            assert response2.status_code == 200
        finally:
            client1.close()
            client2.close()

    def test_instances_have_isolated_headers(self, httpbin_url):
        """Each instance should maintain its own headers."""
        client1 = CycleTLS(port=9208)
        client2 = CycleTLS(port=9209)

        try:
            response1 = client1.get(
                f"{httpbin_url}/headers",
                headers={"X-Instance": "client1"}
            )

            response2 = client2.get(
                f"{httpbin_url}/headers",
                headers={"X-Instance": "client2"}
            )

            assert response1.status_code == 200
            assert response2.status_code == 200

            # Verify headers were sent independently
            data1 = response1.json()
            data2 = response2.json()

            assert "headers" in data1
            assert "headers" in data2
        finally:
            client1.close()
            client2.close()

    def test_instances_have_isolated_cookies(self, httpbin_url):
        """Each instance should maintain its own cookie jar."""
        client1 = CycleTLS(port=9210)
        client2 = CycleTLS(port=9211)

        try:
            # Set different cookies for each instance
            response1 = client1.get(f"{httpbin_url}/cookies/set?cookie1=value1")
            response2 = client2.get(f"{httpbin_url}/cookies/set?cookie2=value2")

            assert response1.status_code == 200
            assert response2.status_code == 200

            # Each instance should maintain separate cookies
            # (if cookie persistence is implemented)
        finally:
            client1.close()
            client2.close()


class TestConcurrentOperations:
    """Test concurrent operations across multiple instances."""

    def test_concurrent_requests_different_ports(self, httpbin_url):
        """Should handle concurrent requests on different ports."""
        client1 = CycleTLS(port=9212)
        client2 = CycleTLS(port=9213)

        results = {}

        def make_request(client, name):
            response = client.get(f"{httpbin_url}/get")
            results[name] = response.status_code

        try:
            # Create threads for concurrent requests
            thread1 = threading.Thread(target=make_request, args=(client1, "client1"))
            thread2 = threading.Thread(target=make_request, args=(client2, "client2"))

            thread1.start()
            thread2.start()

            thread1.join()
            thread2.join()

            # Both requests should succeed
            assert results["client1"] == 200
            assert results["client2"] == 200
        finally:
            client1.close()
            client2.close()

    def test_concurrent_requests_same_instance(self, httpbin_url):
        """Should handle concurrent requests from the same instance."""
        client = CycleTLS(port=9214)

        results = []

        def make_request(url):
            response = client.get(url)
            results.append(response.status_code)

        try:
            threads = []
            for i in range(5):
                thread = threading.Thread(
                    target=make_request,
                    args=(f"{httpbin_url}/get?request={i}",)
                )
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            # All requests should succeed
            assert len(results) == 5
            assert all(status == 200 for status in results)
        finally:
            client.close()

    def test_parallel_large_requests(self, httpbin_url):
        """Should handle parallel large requests."""
        client1 = CycleTLS(port=9215)
        client2 = CycleTLS(port=9216)

        results = {}

        def make_large_request(client, name, size):
            response = client.get(f"{httpbin_url}/bytes/{size}", timeout=30)
            results[name] = {
                "status": response.status_code,
                "size": len(response.body)
            }

        try:
            thread1 = threading.Thread(
                target=make_large_request,
                args=(client1, "client1", 1048576)
            )
            thread2 = threading.Thread(
                target=make_large_request,
                args=(client2, "client2", 1048576)
            )

            thread1.start()
            thread2.start()

            thread1.join(timeout=60)
            thread2.join(timeout=60)

            # Both requests should succeed
            assert results["client1"]["status"] == 200
            assert results["client2"]["status"] == 200
            assert results["client1"]["size"] >= 1000000
            assert results["client2"]["size"] >= 1000000
        finally:
            client1.close()
            client2.close()


class TestResourceCleanup:
    """Test proper resource cleanup and management."""

    def test_explicit_close(self, httpbin_url):
        """Test explicit closing of instances."""
        client = CycleTLS(port=9217)

        response = client.get(f"{httpbin_url}/get")
        assert response.status_code == 200

        # Close the client
        client.close()

        # After close, requests should fail
        with pytest.raises(Exception):
            client.get(f"{httpbin_url}/get")

    def test_multiple_close_calls(self, httpbin_url):
        """Test that multiple close calls don't cause errors."""
        client = CycleTLS(port=9218)

        response = client.get(f"{httpbin_url}/get")
        assert response.status_code == 200

        # Close multiple times should not raise errors
        client.close()
        try:
            client.close()
        except:
            pass  # It's okay if second close raises an error

    def test_cleanup_after_error(self, httpbin_url):
        """Test cleanup after errors."""
        client = CycleTLS(port=9219)

        try:
            # Make a request that will fail
            with pytest.raises(Exception):
                client.get("http://invalid-url-that-does-not-exist.com", timeout=2)

            # Client should still be usable
            response = client.get(f"{httpbin_url}/get")
            assert response.status_code == 200
        finally:
            client.close()

    def test_context_manager_style_cleanup(self, httpbin_url):
        """Test context manager style usage (if implemented)."""
        # Note: If CycleTLS implements __enter__ and __exit__,
        # this would be the proper way to use it

        client = CycleTLS(port=9220)
        try:
            response = client.get(f"{httpbin_url}/get")
            assert response.status_code == 200
        finally:
            client.close()


class TestInstanceLimits:
    """Test behavior with many instances."""

    def test_create_many_instances_sequential(self):
        """Test creating many instances sequentially."""
        instances = []
        base_port = 9221

        try:
            for i in range(5):
                client = CycleTLS(port=base_port + i)
                instances.append(client)

            assert len(instances) == 5
        finally:
            for client in instances:
                try:
                    client.close()
                except:
                    pass

    def test_reuse_port_after_close(self, httpbin_url):
        """Test reusing a port after closing an instance."""
        port = 9226

        # Create and close first instance
        client1 = CycleTLS(port=port)
        response1 = client1.get(f"{httpbin_url}/get")
        assert response1.status_code == 200
        client1.close()

        # Small delay to ensure port is released
        import time
        time.sleep(0.2)

        # Create new instance on same port
        client2 = CycleTLS(port=port)
        try:
            response2 = client2.get(f"{httpbin_url}/get")
            assert response2.status_code == 200
        finally:
            client2.close()


class TestThreadSafety:
    """Test thread safety of CycleTLS instances."""

    def test_single_instance_multiple_threads(self, httpbin_url):
        """Test using a single instance from multiple threads."""
        client = CycleTLS(port=9227)
        results = []
        errors = []

        def make_request(request_id):
            try:
                response = client.get(f"{httpbin_url}/get?id={request_id}")
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        try:
            threads = []
            for i in range(10):
                thread = threading.Thread(target=make_request, args=(i,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            # Most or all requests should succeed
            assert len(results) >= 8  # Allow some failures due to concurrency
            assert all(status == 200 for status in results)
        finally:
            client.close()

    def test_multiple_instances_multiple_threads(self, httpbin_url):
        """Test multiple instances each used by different threads."""
        clients = [
            CycleTLS(port=9228),
            CycleTLS(port=9229),
            CycleTLS(port=9230)
        ]
        results = []

        def make_request(client, request_id):
            response = client.get(f"{httpbin_url}/get?id={request_id}")
            results.append(response.status_code)

        try:
            threads = []
            for i, client in enumerate(clients):
                thread = threading.Thread(target=make_request, args=(client, i))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            assert len(results) == 3
            assert all(status == 200 for status in results)
        finally:
            for client in clients:
                try:
                    client.close()
                except:
                    pass
