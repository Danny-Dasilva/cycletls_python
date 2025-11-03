"""
Connection Pooling Example for CycleTLS Python

This example demonstrates connection reuse and pooling functionality in CycleTLS.
Connection pooling improves performance by reusing TCP connections for multiple
requests to the same host, reducing latency and overhead.

Features demonstrated:
- Enabling/disabling connection reuse
- Performance comparison between pooling and non-pooling
- Multiple requests to the same host
- Connection reuse across different endpoints
- Connection reuse with different HTTP methods
"""

from cycletls import CycleTLS
import time


def example_with_connection_reuse():
    """Example: Multiple requests with connection reuse enabled"""
    print("\n=== Connection Reuse Enabled ===")

    try:
        client = CycleTLS()

        # JA3 fingerprint for consistent testing
        ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"

        # Measure time with connection reuse
        start_time = time.time()

        # Make multiple requests to the same host
        response1 = client.get(
            "https://httpbin.org/get",
            ja3=ja3,
            enable_connection_reuse=True
        )

        response2 = client.get(
            "https://httpbin.org/headers",
            ja3=ja3,
            enable_connection_reuse=True
        )

        response3 = client.get(
            "https://httpbin.org/user-agent",
            ja3=ja3,
            enable_connection_reuse=True
        )

        elapsed_time = time.time() - start_time

        print(f"Request 1 Status: {response1.status_code}")
        print(f"Request 2 Status: {response2.status_code}")
        print(f"Request 3 Status: {response3.status_code}")
        print(f"Total Time: {elapsed_time:.3f} seconds")
        print(f"Average Time per Request: {elapsed_time/3:.3f} seconds")

        client.close()

        return elapsed_time

    except Exception as e:
        print(f"Error: {e}")
        return None


def example_without_connection_reuse():
    """Example: Multiple requests with connection reuse disabled"""
    print("\n=== Connection Reuse Disabled ===")

    try:
        client = CycleTLS()

        # JA3 fingerprint for consistent testing
        ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"

        # Measure time without connection reuse
        start_time = time.time()

        # Make multiple requests without connection reuse
        response1 = client.get(
            "https://httpbin.org/get",
            ja3=ja3,
            enable_connection_reuse=False
        )

        response2 = client.get(
            "https://httpbin.org/headers",
            ja3=ja3,
            enable_connection_reuse=False
        )

        response3 = client.get(
            "https://httpbin.org/user-agent",
            ja3=ja3,
            enable_connection_reuse=False
        )

        elapsed_time = time.time() - start_time

        print(f"Request 1 Status: {response1.status_code}")
        print(f"Request 2 Status: {response2.status_code}")
        print(f"Request 3 Status: {response3.status_code}")
        print(f"Total Time: {elapsed_time:.3f} seconds")
        print(f"Average Time per Request: {elapsed_time/3:.3f} seconds")

        client.close()

        return elapsed_time

    except Exception as e:
        print(f"Error: {e}")
        return None


def example_connection_reuse_different_methods():
    """Example: Connection reuse across different HTTP methods"""
    print("\n=== Connection Reuse with Different HTTP Methods ===")

    try:
        client = CycleTLS()

        ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"

        # GET request
        response_get = client.get(
            "https://httpbin.org/get",
            ja3=ja3,
            enable_connection_reuse=True
        )
        print(f"GET Status: {response_get.status_code}")

        # POST request
        import json
        response_post = client.post(
            "https://httpbin.org/post",
            body=json.dumps({"test": "data"}),
            headers={"Content-Type": "application/json"},
            ja3=ja3,
            enable_connection_reuse=True
        )
        print(f"POST Status: {response_post.status_code}")

        # PUT request
        response_put = client.put(
            "https://httpbin.org/put",
            body=json.dumps({"update": "value"}),
            headers={"Content-Type": "application/json"},
            ja3=ja3,
            enable_connection_reuse=True
        )
        print(f"PUT Status: {response_put.status_code}")

        # DELETE request
        response_delete = client.delete(
            "https://httpbin.org/delete",
            ja3=ja3,
            enable_connection_reuse=True
        )
        print(f"DELETE Status: {response_delete.status_code}")

        print("\nConnection was reused across all different HTTP methods!")

        client.close()

    except Exception as e:
        print(f"Error: {e}")


def example_multiple_hosts():
    """Example: Connection reuse doesn't apply across different hosts"""
    print("\n=== Multiple Hosts (Separate Connections) ===")

    try:
        client = CycleTLS()

        ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"

        # Request to first host
        response1 = client.get(
            "https://httpbin.org/get",
            ja3=ja3,
            enable_connection_reuse=True
        )
        print(f"httpbin.org Status: {response1.status_code}")

        # Request to second host (will create new connection)
        response2 = client.get(
            "https://ja3er.com/json",
            ja3=ja3,
            enable_connection_reuse=True
        )
        print(f"ja3er.com Status: {response2.status_code}")

        # Request back to first host (will reuse existing connection)
        response3 = client.get(
            "https://httpbin.org/headers",
            ja3=ja3,
            enable_connection_reuse=True
        )
        print(f"httpbin.org (2nd request) Status: {response3.status_code}")

        print("\nConnections are pooled per host!")

        client.close()

    except Exception as e:
        print(f"Error: {e}")


def example_rapid_requests():
    """Example: Rapid sequential requests benefit from pooling"""
    print("\n=== Rapid Sequential Requests ===")

    try:
        client = CycleTLS()

        ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"

        # List of endpoints
        endpoints = [
            "/get",
            "/headers",
            "/user-agent",
            "/uuid",
            "/delay/0"
        ]

        start_time = time.time()

        # Make rapid requests with connection reuse
        for endpoint in endpoints:
            response = client.get(
                f"https://httpbin.org{endpoint}",
                ja3=ja3,
                enable_connection_reuse=True,
                timeout=10
            )
            print(f"Request to {endpoint}: {response.status_code}")

        elapsed_time = time.time() - start_time

        print(f"\nTotal Time for {len(endpoints)} requests: {elapsed_time:.3f} seconds")
        print(f"Average: {elapsed_time/len(endpoints):.3f} seconds per request")

        client.close()

    except Exception as e:
        print(f"Error: {e}")


def example_mixed_reuse_settings():
    """Example: Mixing requests with and without connection reuse"""
    print("\n=== Mixed Connection Reuse Settings ===")

    try:
        client = CycleTLS()

        ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"

        # Request 1: With reuse
        response1 = client.get(
            "https://httpbin.org/get",
            ja3=ja3,
            enable_connection_reuse=True
        )
        print(f"Request 1 (reuse=True): {response1.status_code}")

        # Request 2: Without reuse
        response2 = client.get(
            "https://httpbin.org/headers",
            ja3=ja3,
            enable_connection_reuse=False
        )
        print(f"Request 2 (reuse=False): {response2.status_code}")

        # Request 3: With reuse again
        response3 = client.get(
            "https://httpbin.org/user-agent",
            ja3=ja3,
            enable_connection_reuse=True
        )
        print(f"Request 3 (reuse=True): {response3.status_code}")

        print("\nYou can mix connection reuse settings per request!")

        client.close()

    except Exception as e:
        print(f"Error: {e}")


def performance_comparison():
    """Compare performance between connection reuse enabled and disabled"""
    print("\n" + "=" * 60)
    print("Performance Comparison")
    print("=" * 60)

    print("\nRunning 3 requests WITH connection reuse...")
    time_with_reuse = example_with_connection_reuse()

    print("\nRunning 3 requests WITHOUT connection reuse...")
    time_without_reuse = example_without_connection_reuse()

    if time_with_reuse and time_without_reuse:
        improvement = ((time_without_reuse - time_with_reuse) / time_without_reuse) * 100
        print("\n" + "=" * 60)
        print("Results:")
        print(f"  With Connection Reuse:    {time_with_reuse:.3f} seconds")
        print(f"  Without Connection Reuse: {time_without_reuse:.3f} seconds")
        print(f"  Performance Improvement:  {improvement:.1f}%")
        print("=" * 60)

        if improvement > 0:
            print("\nConnection reuse improved performance!")
            print("Subsequent requests were faster due to connection pooling.")
        else:
            print("\nNote: Network conditions and server response times")
            print("may affect the results. Try running the test again.")


def main():
    """Run all connection pooling examples"""
    print("=" * 60)
    print("CycleTLS Connection Pooling Examples")
    print("=" * 60)

    # Run examples
    example_connection_reuse_different_methods()
    example_multiple_hosts()
    example_rapid_requests()
    example_mixed_reuse_settings()

    # Performance comparison
    performance_comparison()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("\nKey Takeaways:")
    print("- Connection reuse significantly improves performance")
    print("- enable_connection_reuse=True reuses TCP connections to the same host")
    print("- Works across different endpoints and HTTP methods on same host")
    print("- Each host maintains its own connection pool")
    print("- You can enable/disable per request for fine-grained control")
    print("=" * 60)


if __name__ == "__main__":
    main()
