"""
Form Submission Examples

This example demonstrates different ways to submit forms with CycleTLS:
- Multipart form data (file uploads)
- URL-encoded form data
- JSON form submissions
- Mixed form data with files and fields
"""

import cycletls
import json
import urllib.parse


def submit_urlencoded_form():
    """Example: Submit a URL-encoded form (application/x-www-form-urlencoded)."""
    print("=" * 60)
    print("URL-Encoded Form Submission")
    print("=" * 60)

    client = cycletls.CycleTLS()

    try:
        # Example 1: URL-encoded form data
        print("\n1. Submitting URL-encoded form...")

        # Form data as dictionary
        form_data = {
            "username": "johndoe",
            "password": "secret123",
            "remember": "true",
            "email": "john@example.com"
        }

        # Encode form data
        encoded_data = urllib.parse.urlencode(form_data)

        response = client.post(
            url="https://httpbin.org/post",
            body=encoded_data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Form data received by server:")
            for key, value in data.get('form', {}).items():
                print(f"  {key}: {value}")

    except Exception as e:
        print(f"Error submitting URL-encoded form: {e}")

    finally:
        client.close()


def submit_multipart_form():
    """Example: Submit multipart form data with file upload."""
    print("\n" + "=" * 60)
    print("Multipart Form Data Submission")
    print("=" * 60)

    client = cycletls.CycleTLS()

    try:
        # Example 2: Multipart form data
        print("\n2. Submitting multipart form with file...")

        # Define boundary for multipart data
        boundary = "----CycleTLSFormBoundary7MA4YWxkTrZu0gW"

        # Build multipart form data manually
        multipart_data = []

        # Add text field
        multipart_data.append(f'--{boundary}')
        multipart_data.append('Content-Disposition: form-data; name="username"')
        multipart_data.append('')
        multipart_data.append('johndoe')

        # Add another text field
        multipart_data.append(f'--{boundary}')
        multipart_data.append('Content-Disposition: form-data; name="email"')
        multipart_data.append('')
        multipart_data.append('john@example.com')

        # Add file field with text content
        multipart_data.append(f'--{boundary}')
        multipart_data.append('Content-Disposition: form-data; name="file"; filename="test.txt"')
        multipart_data.append('Content-Type: text/plain')
        multipart_data.append('')
        multipart_data.append('This is a test file content.')

        # Close boundary
        multipart_data.append(f'--{boundary}--')
        multipart_data.append('')

        # Join with CRLF
        body = '\r\n'.join(multipart_data)

        response = client.post(
            url="https://httpbin.org/post",
            body=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            }
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Form fields received:")
            for key, value in data.get('form', {}).items():
                print(f"  {key}: {value}")
            print(f"Files received:")
            for key, value in data.get('files', {}).items():
                print(f"  {key}: {value[:50]}..." if len(value) > 50 else f"  {key}: {value}")

    except Exception as e:
        print(f"Error submitting multipart form: {e}")

    finally:
        client.close()


def submit_multipart_binary_file():
    """Example: Submit multipart form with binary file (image)."""
    print("\n" + "=" * 60)
    print("Multipart Form with Binary File")
    print("=" * 60)

    client = cycletls.CycleTLS()

    try:
        # Example 3: Multipart with binary file
        print("\n3. Submitting multipart form with binary file (PNG)...")

        # Create a simple 1x1 PNG image
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
            0x89, 0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41,
            0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
            0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
            0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
            0x42, 0x60, 0x82
        ])

        # Build multipart form data with binary file
        boundary = "----CycleTLSBinaryBoundary9QZ8xN3bP"

        # Build body parts as bytes
        parts = []

        # Text field
        parts.append(f'--{boundary}\r\n'.encode())
        parts.append(b'Content-Disposition: form-data; name="title"\r\n\r\n')
        parts.append(b'My Profile Picture\r\n')

        # Binary file field
        parts.append(f'--{boundary}\r\n'.encode())
        parts.append(b'Content-Disposition: form-data; name="image"; filename="profile.png"\r\n')
        parts.append(b'Content-Type: image/png\r\n\r\n')
        parts.append(png_data)
        parts.append(b'\r\n')

        # Close boundary
        parts.append(f'--{boundary}--\r\n'.encode())

        # Combine all parts
        body_bytes = b''.join(parts)

        response = client.post(
            url="https://httpbin.org/post",
            body_bytes=body_bytes,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            }
        )

        print(f"Status: {response.status_code}")
        print(f"Uploaded {len(png_data)} bytes of image data")

        if response.status_code == 200:
            data = response.json()
            print(f"Form fields: {list(data.get('form', {}).keys())}")
            print(f"Files uploaded: {list(data.get('files', {}).keys())}")

    except Exception as e:
        print(f"Error submitting binary file: {e}")

    finally:
        client.close()


def submit_json_form():
    """Example: Submit form data as JSON."""
    print("\n" + "=" * 60)
    print("JSON Form Submission")
    print("=" * 60)

    client = cycletls.CycleTLS()

    try:
        # Example 4: JSON form submission
        print("\n4. Submitting form as JSON...")

        form_data = {
            "user": {
                "username": "johndoe",
                "email": "john@example.com",
                "profile": {
                    "firstName": "John",
                    "lastName": "Doe",
                    "age": 30
                }
            },
            "preferences": {
                "newsletter": True,
                "notifications": False
            }
        }

        response = client.post(
            url="https://httpbin.org/post",
            body=json.dumps(form_data),
            headers={
                "Content-Type": "application/json",
            }
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            json_received = data.get('json', {})
            print(f"JSON data received by server:")
            print(f"  Username: {json_received.get('user', {}).get('username')}")
            print(f"  Email: {json_received.get('user', {}).get('email')}")
            print(f"  Newsletter: {json_received.get('preferences', {}).get('newsletter')}")

    except Exception as e:
        print(f"Error submitting JSON form: {e}")

    finally:
        client.close()


def submit_form_with_authentication():
    """Example: Submit form with custom headers and authentication."""
    print("\n" + "=" * 60)
    print("Form Submission with Authentication")
    print("=" * 60)

    client = cycletls.CycleTLS()

    try:
        # Example 5: Form with authentication headers
        print("\n5. Submitting form with authentication...")

        form_data = {
            "action": "update_profile",
            "field": "email",
            "value": "newemail@example.com"
        }

        response = client.post(
            url="https://httpbin.org/post",
            body=json.dumps(form_data),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "X-CSRF-Token": "abc123def456",
                "Origin": "https://example.com",
                "Referer": "https://example.com/profile"
            },
            # TLS fingerprinting for realistic browser behavior
            ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            timeout=15
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            headers_sent = data.get('headers', {})
            print(f"Authentication headers sent:")
            print(f"  Authorization: {headers_sent.get('Authorization', 'N/A')[:50]}...")
            print(f"  X-CSRF-Token: {headers_sent.get('X-Csrf-Token', 'N/A')}")
            print(f"  Origin: {headers_sent.get('Origin', 'N/A')}")

    except Exception as e:
        print(f"Error submitting authenticated form: {e}")

    finally:
        client.close()


def main():
    """Run all form submission examples."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 13 + "CycleTLS Form Examples" + " " * 22 + "║")
    print("╚" + "═" * 58 + "╝")

    # Run all examples
    submit_urlencoded_form()
    submit_multipart_form()
    submit_multipart_binary_file()
    submit_json_form()
    submit_form_with_authentication()

    print("\n" + "=" * 60)
    print("All form submission examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
