"""
Comprehensive CycleTLS Features Example

This example demonstrates all major features of CycleTLS in one place:
- All HTTP methods (GET, POST, PUT, PATCH, DELETE, etc.)
- TLS fingerprinting (JA3, JA4, HTTP/2, QUIC)
- Advanced TLS configuration
- Binary data handling
- Form submissions
- Cookies
- Proxies
- Connection pooling
- Error handling
- Best practices
"""

import cycletls
import json
import urllib.parse
import time
from typing import Optional


class CycleTLSDemo:
    """Comprehensive demonstration of CycleTLS features."""

    def __init__(self, port: int = 9112):
        """Initialize the demo with a CycleTLS client."""
        self.client: Optional[cycletls.CycleTLS] = None
        self.port = port

    def __enter__(self):
        """Context manager entry - initialize client."""
        print("Initializing CycleTLS client...")
        self.client = cycletls.CycleTLS(port=self.port)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup client."""
        if self.client:
            print("Closing CycleTLS client...")
            self.client.close()
        return False

    def basic_requests(self):
        """Example: Basic HTTP methods."""
        print("\n" + "=" * 60)
        print("1. Basic HTTP Methods")
        print("=" * 60)

        try:
            # GET request
            print("\nGET request:")
            response = self.client.get("https://httpbin.org/get")
            print(f"  Status: {response.status_code}")

            # POST request
            print("\nPOST request:")
            response = self.client.post(
                "https://httpbin.org/post",
                json_data={"key": "value"}
            )
            print(f"  Status: {response.status_code}")

            # PUT request
            print("\nPUT request:")
            response = self.client.put(
                "https://httpbin.org/put",
                json_data={"updated": True}
            )
            print(f"  Status: {response.status_code}")

            # PATCH request
            print("\nPATCH request:")
            response = self.client.patch(
                "https://httpbin.org/patch",
                json_data={"patched": True}
            )
            print(f"  Status: {response.status_code}")

            # DELETE request
            print("\nDELETE request:")
            response = self.client.delete("https://httpbin.org/delete")
            print(f"  Status: {response.status_code}")

            print("\nAll HTTP methods successful!")

        except Exception as e:
            print(f"Error in basic requests: {e}")

    def tls_fingerprinting(self):
        """Example: Advanced TLS fingerprinting."""
        print("\n" + "=" * 60)
        print("2. TLS Fingerprinting")
        print("=" * 60)

        try:
            # Chrome fingerprint
            print("\nChrome-like fingerprint:")
            chrome_ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0"

            response = self.client.get(
                "https://httpbin.org/get",
                ja3=chrome_ja3,
                http2_fingerprint="1:65536,2:0,3:1000,4:6291456,6:262144|15663105|0|m,a,s,p",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            print(f"  Status: {response.status_code}")
            print(f"  JA3: {chrome_ja3[:50]}...")

            # Firefox fingerprint
            print("\nFirefox-like fingerprint:")
            firefox_ja3 = "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0"

            response = self.client.get(
                "https://httpbin.org/get",
                ja3=firefox_ja3,
                user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
            )
            print(f"  Status: {response.status_code}")
            print(f"  JA3: {firefox_ja3[:50]}...")

            print("\nFingerprinting successful!")

        except Exception as e:
            print(f"Error in TLS fingerprinting: {e}")

    def advanced_tls_config(self):
        """Example: Advanced TLS configuration options."""
        print("\n" + "=" * 60)
        print("3. Advanced TLS Configuration")
        print("=" * 60)

        try:
            # Custom SNI
            print("\nCustom SNI override:")
            response = self.client.get(
                "https://httpbin.org/get",
                server_name="custom.example.com",
                headers={"Host": "httpbin.org"}
            )
            print(f"  Status: {response.status_code}")
            print(f"  SNI: custom.example.com")

            # Force HTTP/1.1
            print("\nForce HTTP/1.1:")
            response = self.client.get(
                "https://httpbin.org/get",
                force_http1=True
            )
            print(f"  Status: {response.status_code}")
            print(f"  Protocol: HTTP/1.1 (forced)")

            # TLS 1.3 auto-retry
            print("\nTLS 1.3 auto-retry:")
            response = self.client.get(
                "https://httpbin.org/get",
                tls13_auto_retry=True
            )
            print(f"  Status: {response.status_code}")
            print(f"  TLS 1.3 auto-retry enabled")

            print("\nAdvanced TLS config successful!")

        except Exception as e:
            print(f"Error in advanced TLS config: {e}")

    def binary_data_handling(self):
        """Example: Binary data upload and download."""
        print("\n" + "=" * 60)
        print("4. Binary Data Handling")
        print("=" * 60)

        try:
            # Upload binary data
            print("\nUploading binary data:")
            binary_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'

            response = self.client.post(
                "https://httpbin.org/post",
                body_bytes=binary_data,
                headers={"Content-Type": "application/octet-stream"}
            )
            print(f"  Status: {response.status_code}")
            print(f"  Uploaded: {len(binary_data)} bytes")

            # Download binary data
            print("\nDownloading binary data (image):")
            response = self.client.get(
                "https://httpbin.org/image/png",
                headers={"Accept": "image/png"}
            )
            print(f"  Status: {response.status_code}")
            if response.content:
                print(f"  Downloaded: {len(response.content)} bytes")
                if response.content[:8] == b'\x89PNG\r\n\x1a\n':
                    print(f"  Verified: Valid PNG signature")

            print("\nBinary data handling successful!")

        except Exception as e:
            print(f"Error in binary data handling: {e}")

    def form_submissions(self):
        """Example: Different form submission methods."""
        print("\n" + "=" * 60)
        print("5. Form Submissions")
        print("=" * 60)

        try:
            # URL-encoded form
            print("\nURL-encoded form:")
            form_data = urllib.parse.urlencode({
                "username": "johndoe",
                "password": "secret",
                "remember": "true"
            })

            response = self.client.post(
                "https://httpbin.org/post",
                body=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Form fields: {list(data.get('form', {}).keys())}")

            # JSON form
            print("\nJSON form:")
            json_data = {
                "user": {"username": "johndoe", "email": "john@example.com"},
                "preferences": {"newsletter": True}
            }

            response = self.client.post(
                "https://httpbin.org/post",
                json_data=json_data
            )
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  JSON keys: {list(data.get('json', {}).keys())}")

            print("\nForm submissions successful!")

        except Exception as e:
            print(f"Error in form submissions: {e}")

    def cookie_handling(self):
        """Example: Working with cookies."""
        print("\n" + "=" * 60)
        print("6. Cookie Handling")
        print("=" * 60)

        try:
            # Send cookies
            print("\nSending cookies:")
            cookies = [
                cycletls.schema.Cookie(
                    name="session_id",
                    value="abc123def456",
                    domain="httpbin.org",
                    path="/",
                    secure=True,
                    http_only=True
                ),
                cycletls.schema.Cookie(
                    name="user_token",
                    value="xyz789",
                    domain="httpbin.org"
                )
            ]

            response = self.client.get(
                "https://httpbin.org/cookies",
                cookies=cookies
            )
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Cookies sent: {data.get('cookies', {})}")

            # Set cookies
            print("\nReceiving cookies:")
            response = self.client.get("https://httpbin.org/cookies/set?test=value")
            print(f"  Status: {response.status_code}")
            if response.cookies:
                print(f"  Cookies received: {len(response.cookies)} cookie(s)")
                for cookie in response.cookies:
                    print(f"    {cookie.name}={cookie.value}")

            print("\nCookie handling successful!")

        except Exception as e:
            print(f"Error in cookie handling: {e}")

    def connection_management(self):
        """Example: Connection pooling and management."""
        print("\n" + "=" * 60)
        print("7. Connection Management")
        print("=" * 60)

        try:
            # Connection pooling
            print("\nConnection pooling (reuse enabled):")
            start_time = time.time()

            for i in range(3):
                response = self.client.get(
                    "https://httpbin.org/get",
                    enable_connection_reuse=True,
                    timeout=10
                )
                print(f"  Request {i+1}: Status {response.status_code}")

            elapsed = time.time() - start_time
            print(f"  Total time with connection reuse: {elapsed:.2f}s")

            # Redirects
            print("\nHandling redirects:")
            response = self.client.get(
                "https://httpbin.org/redirect/2",
                disable_redirect=False
            )
            print(f"  Status: {response.status_code}")
            if response.final_url:
                print(f"  Final URL: {response.final_url}")

            print("\nConnection management successful!")

        except Exception as e:
            print(f"Error in connection management: {e}")

    def header_customization(self):
        """Example: Custom header ordering and configuration."""
        print("\n" + "=" * 60)
        print("8. Header Customization")
        print("=" * 60)

        try:
            # Custom header order
            print("\nCustom header ordering:")
            response = self.client.get(
                "https://httpbin.org/get",
                headers={
                    "Accept": "application/json",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Cache-Control": "no-cache",
                    "X-Custom-Header": "CustomValue"
                },
                header_order=["Accept", "Accept-Language", "Accept-Encoding", "Cache-Control", "X-Custom-Header"],
                order_headers_as_provided=True
            )
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Headers sent: {len(data.get('headers', {}))} headers")

            print("\nHeader customization successful!")

        except Exception as e:
            print(f"Error in header customization: {e}")

    def error_handling_demo(self):
        """Example: Proper error handling."""
        print("\n" + "=" * 60)
        print("9. Error Handling Best Practices")
        print("=" * 60)

        # Timeout handling
        print("\nTimeout handling:")
        try:
            response = self.client.get(
                "https://httpbin.org/delay/1",
                timeout=2
            )
            print(f"  Status: {response.status_code}")
            print(f"  Request completed within timeout")
        except Exception as e:
            print(f"  Timeout error: {e}")

        # Invalid URL handling
        print("\nInvalid URL handling:")
        try:
            response = self.client.get(
                "https://this-domain-definitely-does-not-exist-12345.com",
                timeout=5
            )
            print(f"  Status: {response.status_code}")
        except Exception as e:
            print(f"  Expected error caught: Connection/DNS error")

        # HTTP error status codes
        print("\nHTTP error status handling:")
        try:
            response = self.client.get("https://httpbin.org/status/404")
            if response.status_code == 404:
                print(f"  Received 404 as expected")
                print(f"  Handling 404 gracefully...")
        except Exception as e:
            print(f"  Error: {e}")

        print("\nError handling demonstration complete!")

    def comprehensive_example(self):
        """Example: Everything combined."""
        print("\n" + "=" * 60)
        print("10. Comprehensive Example (All Features)")
        print("=" * 60)

        try:
            print("\nMaking request with all features combined:")

            # Prepare form data
            form_data = {
                "username": "advanced_user",
                "action": "login",
                "timestamp": str(int(time.time()))
            }

            response = self.client.post(
                url="https://httpbin.org/post",
                # Body
                json_data=form_data,
                # Headers
                headers={
                    "Accept": "application/json",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Authorization": "Bearer token123",
                    "X-Request-ID": "comprehensive-example-001",
                    "Origin": "https://example.com",
                    "Referer": "https://example.com/login"
                },
                # TLS Fingerprinting
                ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",
                http2_fingerprint="1:65536,2:0,3:1000,4:6291456,6:262144|15663105|0|m,a,s,p",
                disable_grease=False,
                # TLS Configuration
                server_name="httpbin.org",
                insecure_skip_verify=False,
                tls13_auto_retry=True,
                # Protocol
                force_http1=False,
                # Connection
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                timeout=15,
                enable_connection_reuse=True,
                disable_redirect=False,
                # Cookies
                cookies=[
                    cycletls.schema.Cookie(
                        name="session",
                        value="comprehensive_session_123",
                        secure=True,
                        http_only=True
                    )
                ],
                # Header ordering
                header_order=["Content-Type", "Accept", "Accept-Language", "Accept-Encoding", "Authorization", "Origin", "Referer", "X-Request-ID"],
                order_headers_as_provided=True
            )

            print(f"  Status: {response.status_code}")
            print(f"  Response size: {len(response.text)} bytes")

            if response.status_code == 200:
                data = response.json()
                print(f"  Headers sent: {len(data.get('headers', {}))} headers")
                print(f"  JSON data sent: {list(data.get('json', {}).keys())}")
                print(f"  Cookies sent: {list(data.get('cookies', {}).keys())}")

            print("\nComprehensive example successful!")
            print("All CycleTLS features working correctly!")

        except Exception as e:
            print(f"Error in comprehensive example: {e}")


def main():
    """Run comprehensive CycleTLS demonstration."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 8 + "CycleTLS Comprehensive Feature Demo" + " " * 13 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\nThis demo showcases all major features of CycleTLS.")
    print("Each section demonstrates different capabilities.\n")

    # Use context manager for automatic cleanup
    try:
        with CycleTLSDemo() as demo:
            # Run all demonstrations
            demo.basic_requests()
            demo.tls_fingerprinting()
            demo.advanced_tls_config()
            demo.binary_data_handling()
            demo.form_submissions()
            demo.cookie_handling()
            demo.connection_management()
            demo.header_customization()
            demo.error_handling_demo()
            demo.comprehensive_example()

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nDemo error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Comprehensive demonstration completed!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("  1. Use context managers for automatic cleanup")
    print("  2. Always handle errors appropriately")
    print("  3. Choose appropriate TLS fingerprints for your use case")
    print("  4. Enable connection reuse for better performance")
    print("  5. Set reasonable timeouts")
    print("  6. Use binary data (body_bytes) for non-text content")
    print("  7. Combine features as needed for your requirements")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
