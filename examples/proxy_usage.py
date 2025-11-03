"""
Proxy Usage Example for CycleTLS Python

This example demonstrates how to configure and use different types of proxies
with CycleTLS, including HTTP, HTTPS, SOCKS4, SOCKS5, and authenticated proxies.

Proxy URL Format:
- HTTP:   http://hostname:port
- HTTPS:  https://hostname:port
- SOCKS4: socks4://hostname:port
- SOCKS5: socks5://hostname:port
- With auth: protocol://username:password@hostname:port
"""

from cycletls import CycleTLS


def example_http_proxy():
    """Example: Using an HTTP proxy"""
    print("\n=== HTTP Proxy Example ===")

    try:
        client = CycleTLS()

        # Configure HTTP proxy
        proxy_url = "http://127.0.0.1:8080"

        response = client.get(
            "https://httpbin.org/ip",
            proxy=proxy_url,
            timeout=10
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.body}")

        client.close()

    except Exception as e:
        print(f"Error with HTTP proxy: {e}")
        print("Note: Make sure an HTTP proxy is running on 127.0.0.1:8080")


def example_https_proxy():
    """Example: Using an HTTPS proxy"""
    print("\n=== HTTPS Proxy Example ===")

    try:
        client = CycleTLS()

        # Configure HTTPS proxy
        proxy_url = "https://127.0.0.1:8443"

        response = client.get(
            "https://httpbin.org/ip",
            proxy=proxy_url,
            timeout=10
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.body}")

        client.close()

    except Exception as e:
        print(f"Error with HTTPS proxy: {e}")
        print("Note: Make sure an HTTPS proxy is running on 127.0.0.1:8443")


def example_socks4_proxy():
    """Example: Using a SOCKS4 proxy"""
    print("\n=== SOCKS4 Proxy Example ===")

    try:
        client = CycleTLS()

        # Configure SOCKS4 proxy
        proxy_url = "socks4://127.0.0.1:9050"

        response = client.get(
            "https://httpbin.org/ip",
            proxy=proxy_url,
            timeout=10
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.body}")

        client.close()

    except Exception as e:
        print(f"Error with SOCKS4 proxy: {e}")
        print("Note: Make sure a SOCKS4 proxy is running on 127.0.0.1:9050")


def example_socks5_proxy():
    """Example: Using a SOCKS5 proxy"""
    print("\n=== SOCKS5 Proxy Example ===")

    try:
        client = CycleTLS()

        # Configure SOCKS5 proxy (e.g., Tor)
        proxy_url = "socks5://127.0.0.1:9050"

        response = client.get(
            "https://httpbin.org/ip",
            proxy=proxy_url,
            timeout=10
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.body}")

        client.close()

    except Exception as e:
        print(f"Error with SOCKS5 proxy: {e}")
        print("Note: Make sure a SOCKS5 proxy is running on 127.0.0.1:9050")
        print("Tip: You can use Tor Browser or install Tor service")


def example_socks5h_proxy():
    """Example: Using a SOCKS5h proxy (hostname resolution via proxy)"""
    print("\n=== SOCKS5h Proxy Example ===")

    try:
        client = CycleTLS()

        # SOCKS5h resolves DNS queries through the proxy
        # This provides better privacy as DNS queries don't leak
        proxy_url = "socks5h://127.0.0.1:9050"

        response = client.get(
            "https://httpbin.org/ip",
            proxy=proxy_url,
            timeout=10
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.body}")

        client.close()

    except Exception as e:
        print(f"Error with SOCKS5h proxy: {e}")


def example_authenticated_proxy():
    """Example: Using a proxy with username and password authentication"""
    print("\n=== Authenticated Proxy Example ===")

    try:
        client = CycleTLS()

        # Proxy with authentication
        # Format: protocol://username:password@hostname:port
        proxy_url = "http://myuser:mypassword@127.0.0.1:8080"

        response = client.get(
            "https://httpbin.org/ip",
            proxy=proxy_url,
            timeout=10
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.body}")

        client.close()

    except Exception as e:
        print(f"Error with authenticated proxy: {e}")
        print("Note: Update username and password with valid credentials")


def example_proxy_with_ja3():
    """Example: Using proxy with JA3 fingerprint customization"""
    print("\n=== Proxy with JA3 Fingerprint Example ===")

    try:
        client = CycleTLS()

        # Combine proxy with JA3 fingerprinting
        proxy_url = "socks5://127.0.0.1:9050"

        # Chrome-like JA3 fingerprint
        ja3_chrome = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"

        response = client.get(
            "https://ja3er.com/json",
            proxy=proxy_url,
            ja3=ja3_chrome,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"JA3 Hash: {data.get('ja3_hash', 'N/A')}")
            print(f"User Agent: {data.get('User-Agent', 'N/A')}")

        client.close()

    except Exception as e:
        print(f"Error with proxy and JA3: {e}")


def example_proxy_post_request():
    """Example: Using proxy with POST request"""
    print("\n=== Proxy with POST Request Example ===")

    try:
        client = CycleTLS()

        proxy_url = "socks5://127.0.0.1:9050"

        import json
        payload = {
            "name": "CycleTLS",
            "type": "HTTP client",
            "features": ["TLS fingerprinting", "Proxy support"]
        }

        response = client.post(
            "https://httpbin.org/post",
            proxy=proxy_url,
            body=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Echo'd JSON: {data.get('json', {})}")

        client.close()

    except Exception as e:
        print(f"Error with proxy POST request: {e}")


def example_no_proxy():
    """Example: Making request without proxy (baseline)"""
    print("\n=== No Proxy (Direct Connection) Example ===")

    try:
        client = CycleTLS()

        # Direct connection without proxy
        response = client.get(
            "https://httpbin.org/ip",
            timeout=10
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.body}")

        client.close()

    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all proxy examples"""
    print("=" * 60)
    print("CycleTLS Proxy Configuration Examples")
    print("=" * 60)

    # Run examples
    example_no_proxy()
    example_http_proxy()
    example_https_proxy()
    example_socks4_proxy()
    example_socks5_proxy()
    example_socks5h_proxy()
    example_authenticated_proxy()
    example_proxy_with_ja3()
    example_proxy_post_request()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("\nNotes:")
    print("- Most examples require a local proxy server to be running")
    print("- For SOCKS5 examples, you can use Tor (default port 9050)")
    print("- For HTTP/HTTPS examples, you can use tools like mitmproxy or squid")
    print("- Update proxy URLs and credentials as needed for your setup")
    print("=" * 60)


if __name__ == "__main__":
    main()
