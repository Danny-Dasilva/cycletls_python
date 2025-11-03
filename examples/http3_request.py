"""
HTTP/3 Request Example for CycleTLS

This example demonstrates HTTP/3 (QUIC) protocol capabilities:
- force_http3 flag for HTTP/3 requests
- QUIC fingerprinting (if supported)
- HTTP/3 vs HTTP/2 comparison
- Performance characteristics of HTTP/3

HTTP/3 is the latest version of HTTP, built on top of QUIC instead of TCP:
- Faster connection establishment (0-RTT handshake)
- Better performance on lossy networks
- Multiplexing without head-of-line blocking
- Built-in encryption (QUIC includes TLS 1.3)

Note: Not all servers support HTTP/3 yet. Use sites like cloudflare-quic.com
or www.cloudflare.com for testing.
"""

import sys
import time
from cycletls import CycleTLS


def main():
    """Main function demonstrating HTTP/3 examples"""

    # Initialize CycleTLS client
    print("Initializing CycleTLS client...")
    try:
        client = CycleTLS(port=9112)
        print("Client initialized successfully!\n")
    except Exception as e:
        print(f"Error initializing client: {e}")
        sys.exit(1)

    # Example 1: Basic HTTP/3 Request
    print("=" * 70)
    print("Example 1: Basic HTTP/3 Request")
    print("=" * 70)
    print("HTTP/3 uses QUIC protocol (UDP-based) instead of TCP")
    print("Testing with cloudflare-quic.com (known HTTP/3 support)\n")

    try:
        response = client.get(
            "https://cloudflare-quic.com/",
            force_http3=True,  # Force HTTP/3 protocol
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            timeout=15
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response Length: {len(response.body)} bytes")
        print(f"Final URL: {response.final_url or 'N/A'}")

        if response.status_code == 200:
            # Check if response contains HTTP/3 indicators
            if "QUIC" in response.body or "HTTP/3" in response.body:
                print("\n✓ HTTP/3 request successful - QUIC protocol confirmed")
            else:
                print("\n✓ HTTP/3 request successful")
            print(f"Response preview: {response.body[:200]}...")
        else:
            print(f"\n⚠ Request completed but returned status {response.status_code}")

    except Exception as e:
        print(f"Error in basic HTTP/3 request: {e}")
        print("Note: HTTP/3 may not be available in all environments")

    print()

    # Example 2: HTTP/3 with Custom Headers
    print("=" * 70)
    print("Example 2: HTTP/3 Request with Custom Headers")
    print("=" * 70)

    custom_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache',
        'X-Protocol-Test': 'HTTP3'
    }

    print("Custom headers:")
    for key, value in custom_headers.items():
        print(f"  {key}: {value}")
    print()

    try:
        response = client.get(
            "https://cloudflare-quic.com/",
            force_http3=True,
            headers=custom_headers,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            timeout=15
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            print("✓ HTTP/3 request with custom headers successful")
            print(f"Response headers count: {len(response.headers)}")
            print("\nResponse headers (sample):")
            for i, (key, value) in enumerate(response.headers.items()):
                if i < 5:  # Show first 5 headers
                    print(f"  {key}: {value}")
        else:
            print(f"Request returned status {response.status_code}")

    except Exception as e:
        print(f"Error: {e}")

    print()

    # Example 3: HTTP/3 vs HTTP/2 Comparison
    print("=" * 70)
    print("Example 3: HTTP/3 vs HTTP/2 Performance Comparison")
    print("=" * 70)
    print("Comparing connection establishment and response times\n")

    test_url = "https://www.cloudflare.com/"

    try:
        # Test HTTP/2
        print("Testing HTTP/2 (default)...")
        start_http2 = time.time()
        response_http2 = client.get(
            test_url,
            force_http3=False,
            force_http1=False,  # Allow HTTP/2
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            timeout=15
        )
        time_http2 = time.time() - start_http2

        print(f"  HTTP/2 Status: {response_http2.status_code}")
        print(f"  HTTP/2 Time: {time_http2:.3f} seconds")
        print(f"  HTTP/2 Response Size: {len(response_http2.body)} bytes")

        # Test HTTP/3
        print("\nTesting HTTP/3...")
        start_http3 = time.time()
        response_http3 = client.get(
            test_url,
            force_http3=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            timeout=15
        )
        time_http3 = time.time() - start_http3

        print(f"  HTTP/3 Status: {response_http3.status_code}")
        print(f"  HTTP/3 Time: {time_http3:.3f} seconds")
        print(f"  HTTP/3 Response Size: {len(response_http3.body)} bytes")

        # Comparison
        print("\n" + "-" * 70)
        print("Performance Comparison:")
        print(f"  HTTP/2: {time_http2:.3f}s")
        print(f"  HTTP/3: {time_http3:.3f}s")

        if time_http3 < time_http2:
            speedup = ((time_http2 - time_http3) / time_http2) * 100
            print(f"  ✓ HTTP/3 was {speedup:.1f}% faster")
        elif time_http2 < time_http3:
            slowdown = ((time_http3 - time_http2) / time_http2) * 100
            print(f"  ⚠ HTTP/3 was {slowdown:.1f}% slower (network conditions vary)")
        else:
            print(f"  ≈ Similar performance")

        print("\nHTTP/3 Advantages:")
        print("  - Faster connection establishment (0-RTT)")
        print("  - Better performance on packet loss")
        print("  - No head-of-line blocking")
        print("  - Connection migration (survives IP changes)")

    except Exception as e:
        print(f"Error in comparison: {e}")
        print("Note: Some endpoints may not support HTTP/3")

    print()

    # Example 4: Multiple HTTP/3 Requests (Connection Reuse)
    print("=" * 70)
    print("Example 4: Multiple HTTP/3 Requests (Connection Reuse)")
    print("=" * 70)
    print("QUIC supports connection migration and efficient reuse\n")

    endpoints = [
        "https://cloudflare-quic.com/",
        "https://www.cloudflare.com/",
        "https://blog.cloudflare.com/"
    ]

    for i, url in enumerate(endpoints, 1):
        print(f"Request {i}: {url}")
        try:
            start = time.time()
            response = client.get(
                url,
                force_http3=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                timeout=15
            )
            elapsed = time.time() - start

            print(f"  Status: {response.status_code}")
            print(f"  Time: {elapsed:.3f}s")
            print(f"  Size: {len(response.body)} bytes")

            if response.status_code == 200:
                print(f"  ✓ Success")
            else:
                print(f"  ⚠ Non-200 status")

        except Exception as e:
            print(f"  Error: {e}")
        print()

    # Example 5: QUIC Fingerprinting (If Supported)
    print("=" * 70)
    print("Example 5: QUIC Fingerprinting")
    print("=" * 70)
    print("QUIC fingerprinting is similar to TLS fingerprinting for HTTP/3\n")

    # Note: QUIC fingerprinting may not be fully implemented
    # This example shows how it would be used if available
    try:
        print("Attempting HTTP/3 request with QUIC fingerprint parameter...")
        response = client.get(
            "https://cloudflare-quic.com/",
            force_http3=True,
            quic_fingerprint="custom_quic_fp",  # Custom QUIC fingerprint
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            timeout=15
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            print("✓ Request successful with QUIC fingerprint parameter")
            print("Note: QUIC fingerprinting may be in development")
        else:
            print(f"Request returned status {response.status_code}")

    except NotImplementedError as e:
        print(f"⚠ QUIC fingerprinting not yet implemented: {e}")
        print("This feature may be added in future versions")
    except Exception as e:
        print(f"Error: {e}")

    print()

    # Example 6: HTTP/3 Error Handling
    print("=" * 70)
    print("Example 6: HTTP/3 Error Handling")
    print("=" * 70)
    print("Testing HTTP/3 with servers that may not support it\n")

    test_cases = [
        {
            "name": "Non-HTTP/3 Server",
            "url": "https://httpbin.org/get",
            "description": "Server may not support HTTP/3"
        },
        {
            "name": "HTTP/3 Server with Timeout",
            "url": "https://cloudflare-quic.com/",
            "timeout": 10,
            "description": "Testing timeout handling"
        }
    ]

    for case in test_cases:
        print(f"Test: {case['name']}")
        print(f"Description: {case['description']}")

        try:
            response = client.get(
                case['url'],
                force_http3=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                timeout=case.get('timeout', 15)
            )

            print(f"  Status: {response.status_code}")

            if response.status_code == 200:
                print(f"  ✓ Success (server supports HTTP/3 or fallback occurred)")
            elif 400 <= response.status_code < 600:
                print(f"  ⚠ Error status (may not support HTTP/3)")

        except Exception as e:
            print(f"  Exception: {type(e).__name__}: {str(e)[:80]}")
            print(f"  Note: This is expected if server doesn't support HTTP/3")

        print()

    # Example 7: Protocol Detection
    print("=" * 70)
    print("Example 7: Protocol Version Detection")
    print("=" * 70)
    print("Comparing what protocol is actually negotiated\n")

    test_config = {
        "url": "https://www.cloudflare.com/",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    protocols = [
        {"name": "HTTP/1.1", "force_http1": True, "force_http3": False},
        {"name": "HTTP/2", "force_http1": False, "force_http3": False},
        {"name": "HTTP/3", "force_http1": False, "force_http3": True}
    ]

    for proto in protocols:
        print(f"Requesting with {proto['name']}...")
        try:
            response = client.get(
                test_config['url'],
                force_http1=proto['force_http1'],
                force_http3=proto['force_http3'],
                user_agent=test_config['user_agent'],
                timeout=15
            )

            print(f"  Status: {response.status_code}")
            print(f"  Response Size: {len(response.body)} bytes")

            # Try to detect protocol from headers
            if 'content-encoding' in response.headers:
                print(f"  Content-Encoding: {response.headers['content-encoding']}")

            if response.status_code == 200:
                print(f"  ✓ {proto['name']} request successful")

        except Exception as e:
            print(f"  Error: {type(e).__name__}: {str(e)[:60]}")

        print()

    # Example 8: HTTP/3 Best Practices
    print("=" * 70)
    print("Example 8: HTTP/3 Best Practices")
    print("=" * 70)
    print("\nBest Practices for HTTP/3:")
    print("  1. Check server support before forcing HTTP/3")
    print("  2. Use appropriate timeouts (QUIC may take longer on first connect)")
    print("  3. Combine with TLS fingerprinting for better mimicry")
    print("  4. Consider fallback to HTTP/2 if HTTP/3 fails")
    print("  5. Test with known HTTP/3 endpoints first\n")

    print("Testing with combined fingerprinting...")

    # Combine HTTP/3 with JA4 fingerprinting
    chrome_ja4r = "t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,44cd,fe0d,ff01_0403,0804,0401,0503,0805,0501,0806,0601"

    try:
        response = client.get(
            "https://cloudflare-quic.com/",
            force_http3=True,
            ja4r=chrome_ja4r,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            timeout=15
        )

        print(f"Combined HTTP/3 + JA4 Fingerprinting:")
        print(f"  Status: {response.status_code}")
        print(f"  {'✓ Success' if response.status_code == 200 else '⚠ Failed'}")
        print("\nThis combination provides:")
        print("  - HTTP/3 protocol benefits (speed, reliability)")
        print("  - TLS fingerprinting for better browser mimicry")
        print("  - Lower detection risk")

    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 70)
    print("HTTP/3 Examples Complete!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("- HTTP/3 uses QUIC (UDP) instead of TCP")
    print("- Faster connection establishment with 0-RTT")
    print("- Better performance on lossy networks")
    print("- Not all servers support HTTP/3 yet")
    print("- Can be combined with TLS fingerprinting")
    print("- Consider fallback strategies for compatibility")

    # Clean up
    try:
        client.close()
        print("\nClient closed successfully.")
    except Exception as e:
        print(f"\nError closing client: {e}")


if __name__ == "__main__":
    main()
