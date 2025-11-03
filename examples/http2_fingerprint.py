"""
HTTP/2 Fingerprinting Example for CycleTLS

This example demonstrates HTTP/2 fingerprinting capabilities:
- Custom HTTP/2 settings using http2_fingerprint parameter
- Priority configuration (pseudo-header ordering)
- Window update values
- Settings frame customization

HTTP/2 fingerprinting allows you to mimic different browsers by customizing:
- SETTINGS frames (header table size, max concurrent streams, window size, etc.)
- WINDOW_UPDATE values
- Priority frames
- Pseudo-header ordering (method, authority, scheme, path)

Format: <settings>|<window_update>|<priority_frames>|<pseudo_header_order>
Example: 1:65536;2:0;4:131072;5:16384|12517377|0|m,p,a,s

Settings:
- 1: SETTINGS_HEADER_TABLE_SIZE
- 2: SETTINGS_ENABLE_PUSH
- 3: SETTINGS_MAX_CONCURRENT_STREAMS
- 4: SETTINGS_INITIAL_WINDOW_SIZE
- 5: SETTINGS_MAX_FRAME_SIZE
- 6: SETTINGS_MAX_HEADER_LIST_SIZE
"""

import sys
import json
from cycletls import CycleTLS


def main():
    """Main function demonstrating HTTP/2 fingerprinting examples"""

    # Initialize CycleTLS client
    print("Initializing CycleTLS client...")
    try:
        client = CycleTLS(port=9112)
        print("Client initialized successfully!\n")
    except Exception as e:
        print(f"Error initializing client: {e}")
        sys.exit(1)

    # Example 1: Firefox HTTP/2 Fingerprint
    print("=" * 70)
    print("Example 1: Firefox HTTP/2 Fingerprint")
    print("=" * 70)

    # Firefox HTTP/2 fingerprint components:
    # Settings: 1:65536 (header table), 2:0 (push disabled), 4:131072 (window), 5:16384 (frame size)
    # Window Update: 12517377
    # Priority: 0 (no priority frames)
    # Pseudo-header order: m,p,a,s (method, path, authority, scheme)
    firefox_http2 = "1:65536;2:0;4:131072;5:16384|12517377|0|m,p,a,s"

    print("Firefox Settings:")
    print("  SETTINGS_HEADER_TABLE_SIZE: 65536")
    print("  SETTINGS_ENABLE_PUSH: 0 (disabled)")
    print("  SETTINGS_INITIAL_WINDOW_SIZE: 131072")
    print("  SETTINGS_MAX_FRAME_SIZE: 16384")
    print("  WINDOW_UPDATE: 12517377")
    print("  Pseudo-header order: method, path, authority, scheme\n")

    try:
        response = client.get(
            'https://httpbin.org/get',
            http2_fingerprint=firefox_http2,
            user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0',
            timeout=15
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"URL: {data.get('url', 'N/A')}")
            print(f"User-Agent: {data.get('headers', {}).get('User-Agent', 'N/A')[:60]}...")
            print("\n✓ Firefox HTTP/2 fingerprint applied successfully")
        else:
            print(f"Request failed with status {response.status_code}")

    except Exception as e:
        print(f"Error in Firefox HTTP/2 example: {e}")

    print()

    # Example 2: Chrome HTTP/2 Fingerprint
    print("=" * 70)
    print("Example 2: Chrome HTTP/2 Fingerprint")
    print("=" * 70)

    # Chrome HTTP/2 fingerprint components:
    # Settings: 1:65536, 2:0, 4:6291456 (larger window), 6:262144 (max header list)
    # Window Update: 15663105 (larger than Firefox)
    # Priority: 0
    # Pseudo-header order: m,a,s,p (method, authority, scheme, path)
    chrome_http2 = "1:65536;2:0;4:6291456;6:262144|15663105|0|m,a,s,p"

    print("Chrome Settings:")
    print("  SETTINGS_HEADER_TABLE_SIZE: 65536")
    print("  SETTINGS_ENABLE_PUSH: 0 (disabled)")
    print("  SETTINGS_INITIAL_WINDOW_SIZE: 6291456 (much larger)")
    print("  SETTINGS_MAX_HEADER_LIST_SIZE: 262144")
    print("  WINDOW_UPDATE: 15663105")
    print("  Pseudo-header order: method, authority, scheme, path\n")

    try:
        response = client.get(
            'https://httpbin.org/get',
            http2_fingerprint=chrome_http2,
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            timeout=15
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"URL: {data.get('url', 'N/A')}")
            print(f"User-Agent: {data.get('headers', {}).get('User-Agent', 'N/A')[:60]}...")
            print("\n✓ Chrome HTTP/2 fingerprint applied successfully")
        else:
            print(f"Request failed with status {response.status_code}")

    except Exception as e:
        print(f"Error in Chrome HTTP/2 example: {e}")

    print()

    # Example 3: Custom HTTP/2 Settings
    print("=" * 70)
    print("Example 3: Custom HTTP/2 Settings Configuration")
    print("=" * 70)
    print("Demonstrating custom HTTP/2 settings for fine-tuned control\n")

    # Custom settings with specific values
    custom_http2_configs = [
        {
            "name": "Small Header Table",
            "fingerprint": "1:32768;2:0;4:131072;5:16384|12517377|0|m,p,a,s",
            "description": "Reduced header table size (32KB)"
        },
        {
            "name": "Large Window Size",
            "fingerprint": "1:65536;2:0;4:10485760;5:16384|20000000|0|m,a,s,p",
            "description": "10MB initial window size for high-throughput"
        },
        {
            "name": "Minimal Settings",
            "fingerprint": "1:4096;2:0;4:65536|10000000|0|m,p,a,s",
            "description": "Conservative settings for compatibility"
        }
    ]

    for config in custom_http2_configs:
        print(f"{config['name']}: {config['description']}")
        try:
            response = client.get(
                'https://httpbin.org/get',
                http2_fingerprint=config['fingerprint'],
                timeout=15
            )
            print(f"  Status: {response.status_code} - {'✓ Success' if response.status_code == 200 else 'Failed'}")
        except Exception as e:
            print(f"  Error: {e}")
        print()

    # Example 4: HTTP/2 Priority Configuration
    print("=" * 70)
    print("Example 4: HTTP/2 Priority Configuration (Pseudo-header Order)")
    print("=" * 70)
    print("Different browsers use different pseudo-header ordering:\n")

    priority_configs = [
        {
            "browser": "Firefox",
            "order": "m,p,a,s",
            "description": "method → path → authority → scheme",
            "fingerprint": "1:65536;2:0;4:131072;5:16384|12517377|0|m,p,a,s"
        },
        {
            "browser": "Chrome/Edge",
            "order": "m,a,s,p",
            "description": "method → authority → scheme → path",
            "fingerprint": "1:65536;2:0;4:6291456;6:262144|15663105|0|m,a,s,p"
        },
        {
            "browser": "Safari-like",
            "order": "m,a,p,s",
            "description": "method → authority → path → scheme",
            "fingerprint": "1:65536;2:0;4:131072;5:16384|12517377|0|m,a,p,s"
        }
    ]

    for config in priority_configs:
        print(f"{config['browser']} ({config['order']}): {config['description']}")
        try:
            response = client.get(
                'https://httpbin.org/get',
                http2_fingerprint=config['fingerprint'],
                timeout=15
            )
            print(f"  Status: {response.status_code} - {'✓ Success' if response.status_code == 200 else 'Failed'}")
        except Exception as e:
            print(f"  Error: {e}")
        print()

    # Example 5: HTTP/2 Window Update Values
    print("=" * 70)
    print("Example 5: HTTP/2 Window Update Configuration")
    print("=" * 70)
    print("Window update values control flow control behavior:\n")

    window_configs = [
        {
            "name": "Firefox Window (12.5MB)",
            "value": 12517377,
            "fingerprint": "1:65536;2:0;4:131072;5:16384|12517377|0|m,p,a,s"
        },
        {
            "name": "Chrome Window (15.6MB)",
            "value": 15663105,
            "fingerprint": "1:65536;2:0;4:6291456;6:262144|15663105|0|m,a,s,p"
        },
        {
            "name": "Custom Small Window (5MB)",
            "value": 5000000,
            "fingerprint": "1:65536;2:0;4:131072;5:16384|5000000|0|m,p,a,s"
        },
        {
            "name": "Custom Large Window (30MB)",
            "value": 30000000,
            "fingerprint": "1:65536;2:0;4:6291456;6:262144|30000000|0|m,a,s,p"
        }
    ]

    for config in window_configs:
        print(f"{config['name']} (value: {config['value']:,})")
        try:
            response = client.get(
                'https://httpbin.org/get',
                http2_fingerprint=config['fingerprint'],
                timeout=15
            )
            print(f"  Status: {response.status_code} - {'✓ Success' if response.status_code == 200 else 'Failed'}")
        except Exception as e:
            print(f"  Error: {e}")
        print()

    # Example 6: HTTP/2 with Additional Features
    print("=" * 70)
    print("Example 6: HTTP/2 Fingerprint with Custom Headers and Cookies")
    print("=" * 70)

    chrome_http2 = "1:65536;2:0;4:6291456;6:262144|15663105|0|m,a,s,p"

    custom_headers = {
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'X-Custom-Header': 'HTTP2-Fingerprint-Test'
    }

    cookies = [
        {
            "name": "session_id",
            "value": "abc123def456",
            "expires": "2026-01-01T00:00:00Z"
        }
    ]

    print("Testing HTTP/2 fingerprint with:")
    print("  - Custom headers")
    print("  - Cookies")
    print("  - Chrome fingerprint\n")

    try:
        response = client.get(
            'https://httpbin.org/headers',
            http2_fingerprint=chrome_http2,
            headers=custom_headers,
            cookies=cookies,
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            timeout=15
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\nHeaders received by server:")
            for key, value in data.get('headers', {}).items():
                if key in ['User-Agent', 'Accept', 'X-Custom-Header', 'Cookie']:
                    print(f"  {key}: {value[:80]}{'...' if len(value) > 80 else ''}")
            print("\n✓ HTTP/2 fingerprint with custom headers and cookies successful")
        else:
            print(f"Request failed with status {response.status_code}")

    except Exception as e:
        print(f"Error: {e}")

    print()

    # Example 7: HTTP/2 POST Request
    print("=" * 70)
    print("Example 7: HTTP/2 Fingerprint with POST Request")
    print("=" * 70)

    firefox_http2 = "1:65536;2:0;4:131072;5:16384|12517377|0|m,p,a,s"

    post_data = {
        "protocol": "HTTP/2",
        "fingerprint": "Firefox",
        "test": True,
        "message": "Testing HTTP/2 fingerprint with POST"
    }

    print(f"POST data: {json.dumps(post_data, indent=2)}\n")

    try:
        response = client.post(
            'https://httpbin.org/post',
            body=json.dumps(post_data),
            http2_fingerprint=firefox_http2,
            headers={'Content-Type': 'application/json'},
            user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0',
            timeout=15
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\nServer received JSON data:")
            print(f"  {json.dumps(data.get('json', {}), indent=2)}")
            print("\n✓ HTTP/2 POST with fingerprint successful")
        else:
            print(f"Request failed with status {response.status_code}")

    except Exception as e:
        print(f"Error: {e}")

    print()

    # Example 8: Fingerprint Validation with Detection Endpoint
    print("=" * 70)
    print("Example 8: HTTP/2 Fingerprint Validation")
    print("=" * 70)
    print("Testing fingerprints with fingerprint detection services\n")

    test_configs = [
        {
            "name": "Firefox",
            "fingerprint": firefox_http2,
            "user_agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0"
        },
        {
            "name": "Chrome",
            "fingerprint": chrome_http2,
            "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }
    ]

    for config in test_configs:
        print(f"Testing {config['name']} fingerprint with tls.peet.ws...")
        try:
            response = client.get(
                'https://tls.peet.ws/api/all',
                http2_fingerprint=config['fingerprint'],
                user_agent=config['user_agent'],
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                print(f"  Status: {response.status_code} ✓")
                print(f"  HTTP Version: {data.get('http_version', 'N/A')}")

                if 'http2' in data:
                    print(f"  HTTP/2 Data: {str(data.get('http2', {}))[:60]}...")
            else:
                print(f"  Status: {response.status_code}")

        except Exception as e:
            print(f"  Error: {e}")
        print()

    print("=" * 70)
    print("HTTP/2 Fingerprinting Examples Complete!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("- Different browsers have distinct HTTP/2 settings")
    print("- Window sizes and priority orders vary by browser")
    print("- Pseudo-header ordering is a key differentiator")
    print("- Custom settings allow fine-tuned control for specific use cases")

    # Clean up
    try:
        client.close()
        print("\nClient closed successfully.")
    except Exception as e:
        print(f"\nError closing client: {e}")


if __name__ == "__main__":
    main()
