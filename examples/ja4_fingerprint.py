"""
JA4 Fingerprinting Example for CycleTLS

This example demonstrates advanced JA4 fingerprinting capabilities:
- JA4R (JA4 raw) format usage for precise TLS fingerprinting
- disable_grease option for exact fingerprint matching
- Comparison between JA4 and JA3 fingerprinting approaches

JA4 is a more advanced fingerprinting method than JA3, providing:
- Raw TLS data in hex format for granular control
- Better support for modern TLS extensions (ECH, ALPS, Delegated Credentials)
- More detailed cipher suite and signature algorithm information

Format: JA4_r = <header>_<ciphers>_<extensions>_<signature_algorithms>
Example: t13d1516h2_002f,0035,..._0005,000a,..._0403,0804,...
"""

import sys
from cycletls import CycleTLS


def main():
    """Main function demonstrating JA4 fingerprinting examples"""

    # Initialize CycleTLS client
    print("Initializing CycleTLS client...")
    try:
        client = CycleTLS(port=9112)
        print("Client initialized successfully!\n")
    except Exception as e:
        print(f"Error initializing client: {e}")
        sys.exit(1)

    # Example 1: Firefox JA4R Fingerprint
    print("=" * 70)
    print("Example 1: Firefox JA4R Fingerprint")
    print("=" * 70)

    # Firefox 141 JA4_r fingerprint with modern extensions
    # t13d1717h2: TLS 1.3, 17 cipher suites, 17 extensions, HTTP/2
    # Includes ECH (fe0d) and Delegated Credentials (0022) extensions
    firefox_ja4r = "t13d1717h2_002f,0035,009c,009d,1301,1302,1303,c009,c00a,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,001c,0022,0023,002b,002d,0033,fe0d,ff01_0403,0503,0603,0804,0805,0806,0401,0501,0601,0203,0201"

    try:
        response = client.get(
            'https://tls.peet.ws/api/all',
            ja4r=firefox_ja4r,
            disable_grease=False,  # Allow GREASE for more realistic fingerprint
            user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0',
            timeout=15
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"HTTP Version: {data.get('http_version', 'N/A')}")

            if 'tls' in data and 'ja4_r' in data['tls']:
                ja4_r_response = data['tls']['ja4_r']
                print(f"\nJA4_r Sent: {firefox_ja4r}")
                print(f"JA4_r Received: {ja4_r_response}")
                print(f"Match: {ja4_r_response == firefox_ja4r}")

                # Check for modern extensions
                if 'fe0d' in ja4_r_response:
                    print("\n✓ ECH (Encrypted Client Hello) extension present (fe0d)")
                if '0022' in ja4_r_response:
                    print("✓ Delegated Credentials extension present (0022)")
            else:
                print("Warning: JA4_r not found in response")
        else:
            print(f"Request failed with status {response.status_code}")

    except Exception as e:
        print(f"Error in Firefox JA4R example: {e}")

    print()

    # Example 2: Chrome JA4R Fingerprint with ALPS
    print("=" * 70)
    print("Example 2: Chrome JA4R Fingerprint (with ALPS extension)")
    print("=" * 70)

    # Chrome 138+ JA4_r fingerprint
    # t13d1516h2: TLS 1.3, 15 cipher suites, 16 extensions, HTTP/2
    # Includes ALPS (44cd) and ECH (fe0d) extensions
    chrome_ja4r = "t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,44cd,fe0d,ff01_0403,0804,0401,0503,0805,0501,0806,0601"

    try:
        response = client.get(
            'https://tls.peet.ws/api/all',
            ja4r=chrome_ja4r,
            disable_grease=False,
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            timeout=15
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"HTTP Version: {data.get('http_version', 'N/A')}")

            if 'tls' in data and 'ja4_r' in data['tls']:
                ja4_r_response = data['tls']['ja4_r']
                print(f"\nJA4_r Sent: {chrome_ja4r}")
                print(f"JA4_r Received: {ja4_r_response}")
                print(f"Match: {ja4_r_response == chrome_ja4r}")

                # Check for Chrome-specific extensions
                if '44cd' in ja4_r_response:
                    print("\n✓ ALPS (Application-Layer Protocol Settings) extension present (44cd)")
                if 'fe0d' in ja4_r_response:
                    print("✓ ECH (Encrypted Client Hello) extension present (fe0d)")
            else:
                print("Warning: JA4_r not found in response")
        else:
            print(f"Request failed with status {response.status_code}")

    except Exception as e:
        print(f"Error in Chrome JA4R example: {e}")

    print()

    # Example 3: disable_grease Option
    print("=" * 70)
    print("Example 3: JA4R with disable_grease Option")
    print("=" * 70)
    print("GREASE (Generate Random Extensions And Sustain Extensibility) values")
    print("are randomized to prevent ossification of TLS implementations.")
    print("Disabling GREASE allows for exact fingerprint matching.\n")

    try:
        # Request with GREASE disabled
        response_no_grease = client.get(
            'https://tls.peet.ws/api/all',
            ja4r=firefox_ja4r,
            disable_grease=True,  # Exact fingerprint matching
            user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0',
            timeout=15
        )

        print(f"With disable_grease=True:")
        print(f"  Status Code: {response_no_grease.status_code}")

        if response_no_grease.status_code == 200:
            data_no_grease = response_no_grease.json()
            if 'tls' in data_no_grease and 'ja4_r' in data_no_grease['tls']:
                print(f"  JA4_r: {data_no_grease['tls']['ja4_r'][:50]}...")

        # Request with GREASE enabled (default)
        response_with_grease = client.get(
            'https://tls.peet.ws/api/all',
            ja4r=firefox_ja4r,
            disable_grease=False,  # Allow GREASE values
            user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0',
            timeout=15
        )

        print(f"\nWith disable_grease=False:")
        print(f"  Status Code: {response_with_grease.status_code}")

        if response_with_grease.status_code == 200:
            data_with_grease = response_with_grease.json()
            if 'tls' in data_with_grease and 'ja4_r' in data_with_grease['tls']:
                print(f"  JA4_r: {data_with_grease['tls']['ja4_r'][:50]}...")

        print("\nBoth requests should succeed, but GREASE values may differ.")

    except Exception as e:
        print(f"Error in disable_grease example: {e}")

    print()

    # Example 4: JA4 vs JA3 Comparison
    print("=" * 70)
    print("Example 4: JA4 vs JA3 Comparison")
    print("=" * 70)
    print("JA3: Hash-based fingerprinting (simpler, less detailed)")
    print("JA4: Raw format fingerprinting (more detailed, granular control)\n")

    # Chrome fingerprints
    chrome_ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"
    chrome_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    try:
        # Test with JA3
        print("Testing with JA3 fingerprint...")
        response_ja3 = client.get(
            'https://ja3er.com/json',
            ja3=chrome_ja3,
            user_agent=chrome_user_agent,
            timeout=15
        )

        print(f"JA3 Request Status: {response_ja3.status_code}")
        if response_ja3.status_code == 200:
            ja3_data = response_ja3.json()
            print(f"JA3 Hash: {ja3_data.get('ja3_hash', 'N/A')}")
            print(f"JA3 String: {ja3_data.get('ja3', 'N/A')[:50]}...")

        # Test with JA4R
        print("\nTesting with JA4R fingerprint...")
        response_ja4 = client.get(
            'https://tls.peet.ws/api/all',
            ja4r=chrome_ja4r,
            user_agent=chrome_user_agent,
            timeout=15
        )

        print(f"JA4 Request Status: {response_ja4.status_code}")
        if response_ja4.status_code == 200:
            ja4_data = response_ja4.json()
            if 'tls' in ja4_data and 'ja4_r' in ja4_data['tls']:
                print(f"JA4_r: {ja4_data['tls']['ja4_r'][:50]}...")

        print("\nKey Differences:")
        print("- JA3: Produces a hash (e.g., cd08e31494f9531f560d64c695473da9)")
        print("- JA4: Provides raw hex values for inspection and modification")
        print("- JA4: Better support for modern extensions (ALPS, ECH, etc.)")
        print("- JA4: More control over exact TLS handshake behavior")

    except Exception as e:
        print(f"Error in JA4 vs JA3 comparison: {e}")

    print()

    # Example 5: TLS 1.2 JA4R Fingerprint
    print("=" * 70)
    print("Example 5: TLS 1.2 JA4R Fingerprint")
    print("=" * 70)
    print("Demonstrating backward compatibility with TLS 1.2\n")

    # TLS 1.2 fingerprint
    # t12d128h2: TLS 1.2, 12 cipher suites, 8 extensions, HTTP/2
    tls12_ja4r = "t12d128h2_002f,0035,009c,009d,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0017,0023,ff01_0403,0804,0401,0503,0805,0501,0806,0601,0201"

    try:
        response = client.get(
            'https://tls.peet.ws/api/all',
            ja4r=tls12_ja4r,
            disable_grease=False,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            timeout=15
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"HTTP Version: {data.get('http_version', 'N/A')}")

            if 'tls' in data and 'ja4_r' in data['tls']:
                ja4_r_response = data['tls']['ja4_r']
                print(f"\nJA4_r Sent: {tls12_ja4r}")
                print(f"JA4_r Received: {ja4_r_response}")
                print(f"Match: {ja4_r_response == tls12_ja4r}")

                # Verify TLS 1.2
                if ja4_r_response.startswith('t12'):
                    print("\n✓ Successfully negotiated TLS 1.2")
            else:
                print("Warning: JA4_r not found in response")
        else:
            print(f"Request failed with status {response.status_code}")

    except Exception as e:
        print(f"Error in TLS 1.2 JA4R example: {e}")

    print("\n" + "=" * 70)
    print("JA4 Fingerprinting Examples Complete!")
    print("=" * 70)

    # Clean up
    try:
        client.close()
        print("\nClient closed successfully.")
    except Exception as e:
        print(f"\nError closing client: {e}")


if __name__ == "__main__":
    main()
