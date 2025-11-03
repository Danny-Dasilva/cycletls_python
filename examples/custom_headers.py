#!/usr/bin/env python3
"""
Custom Headers and User-Agent Example

This example demonstrates how to customize HTTP headers with CycleTLS:
- Setting custom User-Agent strings
- Adding custom headers
- Controlling header ordering
- Using order_headers_as_provided flag for exact header control
"""

import cycletls


def basic_custom_headers_example(client):
    """
    Demonstrate basic custom headers usage.
    """
    print("\n" + "="*60)
    print("Example 1: Basic Custom Headers")
    print("="*60)

    try:
        # Make request with custom headers
        response = client.get(
            "https://httpbin.org/headers",
            headers={
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Custom-Header": "CustomValue123",
                "X-API-Key": "secret-api-key-12345"
            },
            user_agent="MyCustomBot/2.0 (compatible; Example/1.0)"
        )

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\nHeaders received by server:")
            for key, value in data["headers"].items():
                print(f"  {key}: {value}")
            print("\n✓ Custom headers sent successfully!")
        else:
            print(f"✗ Request failed with status {response.status_code}")

    except Exception as e:
        print(f"✗ Error: {e}")


def header_ordering_example(client):
    """
    Demonstrate controlling header order with header_order parameter.

    Some websites may detect bots based on header ordering, so CycleTLS
    allows you to specify the exact order in which headers should appear.
    """
    print("\n" + "="*60)
    print("Example 2: Custom Header Ordering")
    print("="*60)

    try:
        # Define custom header order (common Chrome browser order)
        custom_header_order = [
            "host",
            "connection",
            "cache-control",
            "sec-ch-ua",
            "sec-ch-ua-mobile",
            "sec-ch-ua-platform",
            "upgrade-insecure-requests",
            "user-agent",
            "accept",
            "sec-fetch-site",
            "sec-fetch-mode",
            "sec-fetch-user",
            "sec-fetch-dest",
            "accept-encoding",
            "accept-language"
        ]

        response = client.get(
            "https://httpbin.org/headers",
            headers={
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "max-age=0",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            },
            header_order=custom_header_order,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
        )

        print(f"\nStatus Code: {response.status_code}")
        print(f"Custom header order: {custom_header_order[:5]}...")

        if response.status_code == 200:
            print("\n✓ Request with custom header ordering successful!")
        else:
            print(f"✗ Request failed with status {response.status_code}")

    except Exception as e:
        print(f"✗ Error: {e}")


def order_as_provided_example(client):
    """
    Demonstrate the order_headers_as_provided flag.

    When set to True, headers will be sent in the exact order they appear
    in the headers dictionary (Python 3.7+ maintains insertion order).
    """
    print("\n" + "="*60)
    print("Example 3: Order Headers As Provided")
    print("="*60)

    try:
        # Headers will be sent in this exact order
        ordered_headers = {
            "X-Custom-First": "First header",
            "Accept": "application/json",
            "X-Custom-Second": "Second header",
            "Authorization": "Bearer token123",
            "X-Custom-Third": "Third header",
            "Content-Type": "application/json"
        }

        response = client.post(
            "https://httpbin.org/post",
            headers=ordered_headers,
            order_headers_as_provided=True,
            body='{"test": "data"}',
            user_agent="OrderedHeaderBot/1.0"
        )

        print(f"\nStatus Code: {response.status_code}")
        print("\nHeaders sent (in order):")
        for key in ordered_headers.keys():
            print(f"  {key}: {ordered_headers[key]}")

        if response.status_code == 200:
            print("\n✓ Headers sent in exact provided order!")
        else:
            print(f"✗ Request failed with status {response.status_code}")

    except Exception as e:
        print(f"✗ Error: {e}")


def browser_impersonation_example(client):
    """
    Demonstrate full browser impersonation with headers, user-agent, and JA3.

    This combines multiple features to closely mimic a real browser.
    """
    print("\n" + "="*60)
    print("Example 4: Full Browser Impersonation")
    print("="*60)

    # Chrome 120 configuration
    chrome_config = {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        },
        "ja3": "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0"
    }

    try:
        response = client.get(
            "https://httpbin.org/headers",
            **chrome_config
        )

        print(f"\nImpersonating: Chrome 120 on Windows")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\nServer detected User-Agent:")
            print(f"  {data['headers'].get('User-Agent', 'N/A')}")
            print("\n✓ Full browser impersonation successful!")
        else:
            print(f"✗ Request failed with status {response.status_code}")

    except Exception as e:
        print(f"✗ Error: {e}")


def main():
    """
    Main function to run all custom header examples.
    """
    print("CycleTLS Custom Headers and User-Agent Examples")
    print("=" * 60)

    # Create CycleTLS client
    print("\nInitializing CycleTLS client...")
    client = cycletls.CycleTLS()

    try:
        # Run all examples
        basic_custom_headers_example(client)
        header_ordering_example(client)
        order_as_provided_example(client)
        browser_impersonation_example(client)

        print("\n" + "="*60)
        print("✓ All custom header examples completed!")
        print("="*60)

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        raise

    finally:
        # Clean up
        print("\nClosing CycleTLS client...")
        client.close()
        print("✓ Done!")


if __name__ == "__main__":
    main()
