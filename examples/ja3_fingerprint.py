#!/usr/bin/env python3
"""
JA3 TLS Fingerprinting Example

This example demonstrates how to use custom JA3 fingerprints with CycleTLS
to mimic different browsers and verify the fingerprint.

JA3 is a method for creating SSL/TLS client fingerprints that are easy to
produce and can be used for identifying clients across different platforms.
"""

import cycletls


# Common browser JA3 fingerprints
BROWSER_FINGERPRINTS = {
    "chrome_120": "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",

    "firefox_122": "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-34-51-43-13-45-28-21,29-23-24-25-256-257,0",

    "safari_17": "771,4865-4866-4867-49196-49195-52393-49200-49199-52392-49162-49161-49172-49171-157-156-53-47-49160-49170-10,0-23-65281-10-11-16-5-13,29-23-24-25,0",
}


def verify_ja3_fingerprint(client, ja3_string, browser_name):
    """
    Verify the JA3 fingerprint using ja3er.com service.

    Args:
        client: CycleTLS client instance
        ja3_string: JA3 fingerprint string to verify
        browser_name: Name of the browser for display purposes
    """
    print(f"\n{'='*60}")
    print(f"Testing {browser_name} JA3 Fingerprint")
    print(f"{'='*60}")
    print(f"JA3: {ja3_string[:50]}...")

    try:
        # Make request with custom JA3 to ja3er.com
        # This service echoes back the detected JA3 fingerprint
        response = client.get(
            "https://ja3er.com/json",
            ja3=ja3_string,
            timeout=10
        )

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()

            print(f"\nDetected JA3 Hash: {data.get('ja3_hash', 'N/A')}")
            print(f"Detected User Agent: {data.get('User-Agent', 'N/A')}")

            # Compare the JA3 string
            detected_ja3 = data.get('ja3', '')
            if detected_ja3 == ja3_string:
                print("✓ JA3 fingerprint matches perfectly!")
            else:
                print("⚠ JA3 fingerprint differs from expected")
                print(f"Expected: {ja3_string[:50]}...")
                print(f"Detected: {detected_ja3[:50]}...")
        else:
            print(f"✗ Request failed with status {response.status_code}")

    except Exception as e:
        print(f"✗ Error during verification: {e}")


def demonstrate_custom_ja3(client):
    """
    Demonstrate using a fully custom JA3 fingerprint.
    """
    print(f"\n{'='*60}")
    print("Custom JA3 Fingerprint Example")
    print(f"{'='*60}")

    # Custom JA3 string with specific cipher suites
    custom_ja3 = "771,49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27,29-23-24-25,0"

    print(f"Custom JA3: {custom_ja3}")

    try:
        # Make request to httpbin to test
        response = client.get(
            "https://httpbin.org/headers",
            ja3=custom_ja3,
            user_agent="CustomBot/1.0"
        )

        if response.status_code == 200:
            print("\n✓ Request with custom JA3 successful!")
            data = response.json()
            print(f"Server saw User-Agent: {data['headers'].get('User-Agent', 'N/A')}")
        else:
            print(f"✗ Request failed with status {response.status_code}")

    except Exception as e:
        print(f"✗ Error with custom JA3: {e}")


def main():
    """
    Main function to demonstrate JA3 fingerprinting capabilities.
    """
    print("CycleTLS JA3 Fingerprinting Examples")
    print("=" * 60)

    # Create CycleTLS client
    print("\nInitializing CycleTLS client...")
    client = cycletls.CycleTLS()

    try:
        # Test Chrome fingerprint
        verify_ja3_fingerprint(
            client,
            BROWSER_FINGERPRINTS["chrome_120"],
            "Chrome 120"
        )

        # Test Firefox fingerprint
        verify_ja3_fingerprint(
            client,
            BROWSER_FINGERPRINTS["firefox_122"],
            "Firefox 122"
        )

        # Test Safari fingerprint
        verify_ja3_fingerprint(
            client,
            BROWSER_FINGERPRINTS["safari_17"],
            "Safari 17"
        )

        # Demonstrate custom JA3
        demonstrate_custom_ja3(client)

        print("\n" + "="*60)
        print("✓ All JA3 fingerprint tests completed!")
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
