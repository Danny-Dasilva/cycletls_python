#!/usr/bin/env python3
"""
Basic CycleTLS Request Example

This example demonstrates the simplest usage of CycleTLS:
- Creating a CycleTLS client
- Making a basic GET request
- Handling the response
- Properly closing the client
"""

import cycletls


def main():
    """
    Perform a basic GET request using CycleTLS.
    """
    # Create a CycleTLS client instance
    # The client will automatically start the Go binary if needed
    print("Creating CycleTLS client...")
    client = cycletls.CycleTLS()

    try:
        # Make a simple GET request
        print("\nMaking GET request to https://httpbin.org/get...")
        response = client.get("https://httpbin.org/get")

        # Print response details
        print(f"\nStatus Code: {response.status_code}")
        print(f"Request ID: {response.request_id}")

        # Print response headers
        print("\nResponse Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")

        # Print response body (first 500 characters)
        print("\nResponse Body (truncated):")
        print(response.body[:500] if len(response.body) > 500 else response.body)

        # Parse JSON response
        try:
            json_data = response.json()
            print("\nParsed JSON Origin:", json_data.get("origin", "N/A"))
        except Exception as e:
            print(f"\nCould not parse JSON: {e}")

        print("\n✓ Request completed successfully!")

    except Exception as e:
        print(f"\n✗ Error occurred: {e}")
        raise

    finally:
        # Always close the client to clean up resources
        print("\nClosing CycleTLS client...")
        client.close()
        print("✓ Client closed successfully!")


if __name__ == "__main__":
    main()
