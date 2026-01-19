"""
Advanced TLS Configuration Examples

This example demonstrates advanced TLS features in CycleTLS:
- Custom SNI (Server Name Indication) with server_name
- Skip certificate verification with insecure_skip_verify
- TLS 1.3 auto-retry with tls13_auto_retry
- Force HTTP/1.1 with force_http1
- JA3 and JA4 fingerprinting
- HTTP/2 and QUIC fingerprinting
"""

import cycletls


def custom_sni_example():
    """Example: Use custom Server Name Indication (SNI)."""
    print("=" * 60)
    print("Custom SNI (Server Name Indication)")
    print("=" * 60)

    try:
        with cycletls.CycleTLS() as client:
            # Example 1: Custom SNI override
            print("\n1. Making request with custom SNI...")

            # This allows you to connect to an IP but present a different hostname
            # in the TLS handshake (useful for CDN bypass, testing, etc.)
            response = client.get(
                url="https://httpbin.org/get",
                server_name="custom.example.com",  # Override SNI
                headers={
                    "Host": "httpbin.org"  # HTTP Host header remains correct
                }
            )

            print(f"Status: {response.status_code}")
            print(f"Connected with custom SNI: custom.example.com")

            if response.ok:
                data = response.json()
                print(f"Request headers seen by server:")
                print(f"  Host: {data.get('headers', {}).get('Host', 'N/A')}")

    except Exception as e:
        print(f"Error with custom SNI: {e}")


def insecure_skip_verify_example():
    """Example: Skip TLS certificate verification."""
    print("\n" + "=" * 60)
    print("Skip TLS Certificate Verification")
    print("=" * 60)

    try:
        with cycletls.CycleTLS() as client:
            # Example 2: Skip certificate verification
            print("\n2. Making request with insecure_skip_verify...")
            print("WARNING: This disables certificate validation!")

            # Useful for testing with self-signed certificates or development servers
            # DO NOT use in production unless you know what you're doing
            response = client.get(
                url="https://httpbin.org/get",
                insecure_skip_verify=True,  # Skip certificate validation
            )

            print(f"Status: {response.status_code}")
            print(f"Connected without certificate verification")

            if response.ok:
                print(f"Response size: {len(response.text)} bytes")

    except Exception as e:
        print(f"Error with insecure connection: {e}")


def tls13_auto_retry_example():
    """Example: Use TLS 1.3 auto-retry feature."""
    print("\n" + "=" * 60)
    print("TLS 1.3 Auto-Retry")
    print("=" * 60)

    try:
        with cycletls.CycleTLS() as client:
            # Example 3: TLS 1.3 auto-retry
            print("\n3. Making request with TLS 1.3 auto-retry...")

            # Auto-retry with TLS 1.3 compatible curves if the initial handshake fails
            # This helps with certain servers that have strict TLS requirements
            response = client.get(
                url="https://httpbin.org/get",
                tls13_auto_retry=True,  # Enable auto-retry (default: True)
                ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0"
            )

            print(f"Status: {response.status_code}")
            print(f"TLS 1.3 auto-retry enabled")

            if response.ok:
                print(f"Connection successful with TLS 1.3 features")

    except Exception as e:
        print(f"Error with TLS 1.3 auto-retry: {e}")


def force_http1_example():
    """Example: Force HTTP/1.1 protocol."""
    print("\n" + "=" * 60)
    print("Force HTTP/1.1 Protocol")
    print("=" * 60)

    try:
        with cycletls.CycleTLS() as client:
            # Example 4: Force HTTP/1.1
            print("\n4. Making request with forced HTTP/1.1...")

            # Some servers behave differently on HTTP/1.1 vs HTTP/2
            # This forces the use of HTTP/1.1
            response = client.get(
                url="https://httpbin.org/get",
                force_http1=True,  # Force HTTP/1.1 protocol
            )

            print(f"Status: {response.status_code}")
            print(f"Forced protocol: HTTP/1.1")

            if response.ok:
                data = response.json()
                print(f"Server URL: {data.get('url', 'N/A')}")

    except Exception as e:
        print(f"Error forcing HTTP/1.1: {e}")


def advanced_fingerprinting_example():
    """Example: Use advanced TLS fingerprinting (JA3, JA4, HTTP/2)."""
    print("\n" + "=" * 60)
    print("Advanced TLS Fingerprinting")
    print("=" * 60)

    try:
        with cycletls.CycleTLS() as client:
            # Example 5: Advanced fingerprinting
            print("\n5. Making request with advanced fingerprinting...")

            # Chrome-like JA3 fingerprint
            chrome_ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0"

            # JA4 raw format (optional, for more advanced fingerprinting)
            ja4r_fingerprint = "t13d1516h2_8daaf6152771_e5627efa2ab1"

            # HTTP/2 fingerprint (SETTINGS frame parameters)
            http2_fp = "1:65536,2:0,3:1000,4:6291456,6:262144|15663105|0|m,a,s,p"

            response = client.get(
                url="https://httpbin.org/get",
                ja3=chrome_ja3,
                ja4r=ja4r_fingerprint,
                http2_fingerprint=http2_fp,
                disable_grease=False,  # Keep GREASE enabled for realism
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            print(f"Status: {response.status_code}")
            print(f"Applied fingerprints:")
            print(f"  JA3: {chrome_ja3[:50]}...")
            print(f"  JA4R: {ja4r_fingerprint}")
            print(f"  HTTP/2: {http2_fp[:40]}...")

            if response.ok:
                data = response.json()
                user_agent_seen = data.get('headers', {}).get('User-Agent', 'N/A')
                print(f"User-Agent seen by server: {user_agent_seen[:60]}...")

    except Exception as e:
        print(f"Error with advanced fingerprinting: {e}")


def combined_tls_options_example():
    """Example: Combine multiple advanced TLS options."""
    print("\n" + "=" * 60)
    print("Combined Advanced TLS Options")
    print("=" * 60)

    try:
        with cycletls.CycleTLS() as client:
            # Example 6: Combine multiple options
            print("\n6. Making request with combined TLS options...")

            response = client.get(
                url="https://httpbin.org/get",
                # TLS Configuration
                server_name="httpbin.org",
                insecure_skip_verify=False,  # Keep verification enabled
                tls13_auto_retry=True,
                # Protocol
                force_http1=False,  # Allow HTTP/2
                # Fingerprinting
                ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",
                # Connection
                timeout=15,
                enable_connection_reuse=True,
                disable_redirect=False,
                # Headers
                headers={
                    "Accept": "application/json",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache"
                },
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )

            print(f"Status: {response.status_code}")
            print(f"All advanced TLS options applied successfully")

            if response.ok:
                data = response.json()
                print(f"Headers sent: {len(data.get('headers', {}))} headers")
                print(f"Response size: {len(response.text)} bytes")

    except Exception as e:
        print(f"Error with combined options: {e}")


def firefox_fingerprint_example():
    """Example: Mimic Firefox browser using TLS fingerprinting."""
    print("\n" + "=" * 60)
    print("Firefox Browser Fingerprint")
    print("=" * 60)

    try:
        with cycletls.CycleTLS() as client:
            # Example 7: Firefox fingerprint
            print("\n7. Making request mimicking Firefox browser...")

            # Firefox-like JA3 fingerprint
            firefox_ja3 = "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0"

            response = client.get(
                url="https://httpbin.org/get",
                ja3=firefox_ja3,
                user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1"
                }
            )

            print(f"Status: {response.status_code}")
            print(f"Firefox fingerprint applied")

            if response.ok:
                data = response.json()
                ua = data.get('headers', {}).get('User-Agent', '')
                print(f"User-Agent: {ua}")
                print(f"Appears as Firefox browser to the server")

    except Exception as e:
        print(f"Error with Firefox fingerprint: {e}")


def main():
    """Run all advanced TLS examples."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "CycleTLS Advanced TLS Examples" + " " * 17 + "║")
    print("╚" + "═" * 58 + "╝")

    # Run all examples
    custom_sni_example()
    insecure_skip_verify_example()
    tls13_auto_retry_example()
    force_http1_example()
    advanced_fingerprinting_example()
    combined_tls_options_example()
    firefox_fingerprint_example()

    print("\n" + "=" * 60)
    print("All advanced TLS examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
