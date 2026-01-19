#!/usr/bin/env python3
"""
Basic CycleTLS Request Example

This example demonstrates the simplest usage of CycleTLS:
- Using module-level convenience functions (simplest API)
- Using the context manager pattern (recommended for multiple requests)
- Accessing response properties
"""

import cycletls


def example_simple_api():
    """
    Example 1: Using module-level convenience functions.

    This is the simplest way to make requests - CycleTLS handles
    session management automatically.
    """
    print("=" * 60)
    print("Example 1: Simple Module-Level API")
    print("=" * 60)

    # Make a simple GET request - no client setup needed!
    print("\nMaking GET request to https://httpbin.org/get...")
    response = cycletls.get("https://httpbin.org/get")

    # Print response details using modern API
    print(f"\nStatus Code: {response.status_code}")
    print(f"OK: {response.ok}")

    # Use .text property (preferred) or .content for bytes
    print("\nResponse Text (first 200 chars):")
    print(response.text[:200] if len(response.text) > 200 else response.text)

    # Parse JSON response
    try:
        json_data = response.json()
        print(f"\nParsed JSON Origin: {json_data.get('origin', 'N/A')}")
    except Exception as e:
        print(f"\nCould not parse JSON: {e}")

    print("\nRequest completed successfully!")


def example_context_manager():
    """
    Example 2: Using context manager for multiple requests.

    This is the recommended pattern when making multiple requests,
    as it properly manages the client lifecycle.
    """
    print("\n" + "=" * 60)
    print("Example 2: Context Manager Pattern (Recommended)")
    print("=" * 60)

    # Use context manager - client is automatically cleaned up
    with cycletls.CycleTLS() as client:
        print("\nClient created and ready for requests...")

        # Make multiple requests
        print("\nMaking GET request...")
        response = client.get("https://httpbin.org/get")
        print(f"GET Status: {response.status_code}")

        print("\nMaking POST request...")
        response = client.post(
            "https://httpbin.org/post",
            json_data={"message": "Hello from CycleTLS!"}
        )
        print(f"POST Status: {response.status_code}")

        # Access response properties
        print("\nResponse Properties:")
        print(f"  status_code: {response.status_code}")
        print(f"  ok: {response.ok}")
        print(f"  encoding: {response.encoding}")
        print(f"  headers count: {len(response.headers)}")

    # Client is automatically closed here
    print("\nClient automatically closed after context exit!")


def example_response_properties():
    """
    Example 3: Exploring all response properties.
    """
    print("\n" + "=" * 60)
    print("Example 3: Response Properties")
    print("=" * 60)

    response = cycletls.get("https://httpbin.org/json")

    print("\nAvailable Response Properties:")
    print(f"  .status_code: {response.status_code}")
    print(f"  .text: {response.text[:50]}...")  # String content
    print(f"  .content: {response.content[:50]}...")  # Bytes content
    print(f"  .json(): {list(response.json().keys())}")
    print(f"  .headers: {dict(list(response.headers.items())[:3])}...")
    print(f"  .cookies: {response.cookies}")
    print(f"  .ok: {response.ok}")
    print(f"  .encoding: {response.encoding}")
    print(f"  .url: {response.url}")
    print(f"  .is_error: {response.is_error}")


def main():
    """Run all basic request examples."""
    print("\n")
    print("=" * 60)
    print("CycleTLS Basic Request Examples")
    print("=" * 60)

    # Run examples
    example_simple_api()
    example_context_manager()
    example_response_properties()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
