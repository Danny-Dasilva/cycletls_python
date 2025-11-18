#!/usr/bin/env python3
"""
Basic Async Usage Example for CycleTLS

This example demonstrates basic async/await usage with CycleTLS,
including:
- Simple async GET/POST requests
- Using async context manager
- Module-level async functions
- Handling JSON responses
"""

import asyncio
import cycletls
from cycletls import AsyncCycleTLS


async def example_module_functions():
    """Example using module-level async convenience functions."""
    print("=== Module-Level Async Functions ===\n")

    # Simple GET request
    print("1. Simple GET request:")
    response = await cycletls.aget("https://httpbin.org/get")
    print(f"Status: {response.status_code}")
    print(f"URL: {response.json()['url']}\n")

    # GET with query parameters
    print("2. GET with query parameters:")
    response = await cycletls.aget(
        "https://httpbin.org/get",
        params={"name": "CycleTLS", "version": "async"}
    )
    data = response.json()
    print(f"Status: {response.status_code}")
    print(f"Query params: {data['args']}\n")

    # POST with JSON data
    print("3. POST with JSON data:")
    payload = {
        "username": "async_user",
        "email": "user@example.com",
        "async": True
    }
    response = await cycletls.apost(
        "https://httpbin.org/post",
        json_data=payload
    )
    data = response.json()
    print(f"Status: {response.status_code}")
    print(f"Sent data: {data['json']}\n")

    # PUT request
    print("4. PUT request:")
    response = await cycletls.aput(
        "https://httpbin.org/put",
        json_data={"update": "async"}
    )
    print(f"Status: {response.status_code}\n")

    # DELETE request
    print("5. DELETE request:")
    response = await cycletls.adelete("https://httpbin.org/delete")
    print(f"Status: {response.status_code}\n")


async def example_context_manager():
    """Example using async context manager for multiple requests."""
    print("=== Async Context Manager ===\n")

    async with AsyncCycleTLS() as client:
        print("Client created and ready for multiple requests\n")

        # Multiple requests using same client
        print("1. First request:")
        response1 = await client.get("https://httpbin.org/get?request=1")
        print(f"Status: {response1.status_code}")

        print("\n2. Second request:")
        response2 = await client.post(
            "https://httpbin.org/post",
            json_data={"request": 2}
        )
        print(f"Status: {response2.status_code}")

        print("\n3. Third request:")
        response3 = await client.get("https://httpbin.org/get?request=3")
        print(f"Status: {response3.status_code}")

    print("\nClient automatically closed after context\n")


async def example_custom_headers():
    """Example with custom headers."""
    print("=== Custom Headers ===\n")

    async with AsyncCycleTLS() as client:
        headers = {
            "X-API-Key": "your-api-key",
            "X-Request-ID": "async-example-123",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        response = await client.get(
            "https://httpbin.org/headers",
            headers=headers,
            user_agent="CycleTLS-Async/1.0"
        )

        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Headers sent: {data['headers']}\n")


async def example_error_handling():
    """Example with error handling."""
    print("=== Error Handling ===\n")

    # Handle HTTP errors
    print("1. Handling 404 error:")
    response = await cycletls.aget("https://httpbin.org/status/404")
    print(f"Status: {response.status_code}")
    print(f"Is error: {response.is_error}")
    print(f"Is client error: {response.is_client_error}\n")

    # Handle timeout
    print("2. Handling timeout:")
    try:
        response = await cycletls.aget(
            "https://httpbin.org/delay/10",
            timeout=2  # 2 second timeout
        )
    except asyncio.TimeoutError:
        print("Request timed out as expected\n")

    # Raise for status
    print("3. Using raise_for_status:")
    response = await cycletls.aget("https://httpbin.org/status/500")
    print(f"Status: {response.status_code}")
    try:
        response.raise_for_status()
    except Exception as e:
        print(f"Raised exception: {type(e).__name__}\n")


async def example_response_properties():
    """Example exploring response properties."""
    print("=== Response Properties ===\n")

    response = await cycletls.aget("https://httpbin.org/json")

    print(f"Status Code: {response.status_code}")
    print(f"OK: {response.ok}")
    print(f"Is Error: {response.is_error}")
    print(f"Headers count: {len(response.headers)}")
    print(f"Text length: {len(response.text)} bytes")

    # JSON parsing
    data = response.json()
    print(f"\nJSON keys: {list(data.keys())}")
    print()


async def example_form_data():
    """Example with form data."""
    print("=== Form Data ===\n")

    # URL-encoded form data
    print("1. URL-encoded form:")
    form_data = {
        "username": "async_user",
        "password": "secret123",
        "remember": "true"
    }

    response = await cycletls.apost(
        "https://httpbin.org/post",
        data=form_data
    )

    data = response.json()
    print(f"Status: {response.status_code}")
    print(f"Form data sent: {data['form']}\n")


async def example_cookies():
    """Example with cookies."""
    print("=== Cookies ===\n")

    cookies = {
        "session_id": "abc123xyz",
        "user_pref": "dark_mode",
        "lang": "en"
    }

    response = await cycletls.aget(
        "https://httpbin.org/cookies",
        cookies=cookies
    )

    data = response.json()
    print(f"Status: {response.status_code}")
    print(f"Cookies sent: {data['cookies']}\n")


async def example_compression():
    """Example with compressed responses."""
    print("=== Compression ===\n")

    # Gzip compression
    print("1. Gzip compressed response:")
    response = await cycletls.aget("https://httpbin.org/gzip")
    data = response.json()
    print(f"Status: {response.status_code}")
    print(f"Gzipped: {data.get('gzipped', False)}\n")

    # Brotli compression
    print("2. Brotli compressed response:")
    response = await cycletls.aget("https://httpbin.org/brotli")
    data = response.json()
    print(f"Status: {response.status_code}")
    print(f"Brotli: {data.get('brotli', False)}\n")


async def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("CycleTLS Async Basic Examples")
    print("="*60 + "\n")

    await example_module_functions()
    await example_context_manager()
    await example_custom_headers()
    await example_error_handling()
    await example_response_properties()
    await example_form_data()
    await example_cookies()
    await example_compression()

    print("="*60)
    print("All examples completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
