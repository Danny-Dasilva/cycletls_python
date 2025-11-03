"""
Binary Data Handling Example

This example demonstrates how to handle binary data with CycleTLS:
- Uploading binary data using body_bytes parameter
- Uploading image files
- Receiving binary response data
- Working with bytes in both requests and responses
"""

import cycletls
import os
from pathlib import Path


def upload_binary_data():
    """Example: Upload binary data to a server."""
    print("=" * 60)
    print("Binary Data Upload Example")
    print("=" * 60)

    # Initialize CycleTLS client
    client = cycletls.CycleTLS()

    try:
        # Example 1: Upload raw binary data
        print("\n1. Uploading raw binary data...")

        # Create some binary data
        binary_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'

        response = client.post(
            url="https://httpbin.org/post",
            body_bytes=binary_data,
            headers={
                "Content-Type": "application/octet-stream",
            }
        )

        print(f"Status: {response.status_code}")
        print(f"Request sent {len(binary_data)} bytes")

        # Parse JSON response to verify upload
        if response.status_code == 200:
            data = response.json()
            print(f"Server received data (base64): {data.get('data', '')[:50]}...")

    except Exception as e:
        print(f"Error uploading binary data: {e}")

    finally:
        client.close()


def upload_image_file():
    """Example: Upload an image file."""
    print("\n" + "=" * 60)
    print("Image Upload Example")
    print("=" * 60)

    client = cycletls.CycleTLS()

    try:
        # Example 2: Upload an image file
        print("\n2. Uploading image file...")

        # Create a simple 1x1 PNG image for testing
        # This is a minimal valid PNG file (1x1 transparent pixel)
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
            0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
            0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,  # IDAT chunk
            0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
            0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
            0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,  # IEND chunk
            0x42, 0x60, 0x82
        ])

        response = client.post(
            url="https://httpbin.org/post",
            body_bytes=png_data,
            headers={
                "Content-Type": "image/png",
                "Content-Disposition": "attachment; filename=test.png"
            }
        )

        print(f"Status: {response.status_code}")
        print(f"Uploaded image size: {len(png_data)} bytes")

        if response.status_code == 200:
            data = response.json()
            content_type = data.get('headers', {}).get('Content-Type', '')
            print(f"Server detected Content-Type: {content_type}")

    except Exception as e:
        print(f"Error uploading image: {e}")

    finally:
        client.close()


def download_binary_data():
    """Example: Download binary data and access body_bytes."""
    print("\n" + "=" * 60)
    print("Binary Download Example")
    print("=" * 60)

    client = cycletls.CycleTLS()

    try:
        # Example 3: Download binary data
        print("\n3. Downloading binary data (image)...")

        response = client.get(
            url="https://httpbin.org/image/png",
            headers={
                "Accept": "image/png"
            }
        )

        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")

        # Access binary response data
        if response.body_bytes:
            print(f"Received {len(response.body_bytes)} bytes of binary data")

            # Verify PNG signature
            if response.body_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                print("Verified: Valid PNG file signature detected")

            # You could save the file:
            # with open('downloaded_image.png', 'wb') as f:
            #     f.write(response.body_bytes)
        else:
            print("No binary data in response")

    except Exception as e:
        print(f"Error downloading binary data: {e}")

    finally:
        client.close()


def upload_with_mixed_data():
    """Example: Combine binary upload with custom headers and TLS settings."""
    print("\n" + "=" * 60)
    print("Advanced Binary Upload Example")
    print("=" * 60)

    client = cycletls.CycleTLS()

    try:
        # Example 4: Upload binary data with advanced settings
        print("\n4. Binary upload with custom TLS and headers...")

        # Create binary payload
        payload = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09'

        response = client.post(
            url="https://httpbin.org/post",
            body_bytes=payload,
            headers={
                "Content-Type": "application/octet-stream",
                "X-Custom-Header": "BinaryUpload",
                "User-Agent": "CycleTLS-Binary/1.0"
            },
            # TLS fingerprinting for additional stealth
            ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",
            # Custom user agent
            user_agent="CycleTLS-Binary/1.0",
            # Connection settings
            timeout=10,
            enable_connection_reuse=True
        )

        print(f"Status: {response.status_code}")
        print(f"Uploaded: {len(payload)} bytes")

        if response.status_code == 200:
            data = response.json()
            headers_sent = data.get('headers', {})
            print(f"Custom headers sent successfully:")
            print(f"  User-Agent: {headers_sent.get('User-Agent', 'N/A')}")
            print(f"  X-Custom-Header: {headers_sent.get('X-Custom-Header', 'N/A')}")

    except Exception as e:
        print(f"Error in advanced binary upload: {e}")

    finally:
        client.close()


def main():
    """Run all binary data examples."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 12 + "CycleTLS Binary Data Examples" + " " * 16 + "║")
    print("╚" + "═" * 58 + "╝")

    # Run all examples
    upload_binary_data()
    upload_image_file()
    download_binary_data()
    upload_with_mixed_data()

    print("\n" + "=" * 60)
    print("All binary data examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
