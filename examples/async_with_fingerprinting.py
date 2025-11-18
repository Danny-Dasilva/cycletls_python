#!/usr/bin/env python3
"""
Async TLS Fingerprinting Example for CycleTLS

This example demonstrates using TLS fingerprinting with async requests,
including:
- JA3 fingerprint spoofing
- JA4R fingerprint spoofing
- HTTP/2 fingerprints
- Complete browser profile emulation
- Concurrent requests with different fingerprints
"""

import asyncio
import cycletls
from cycletls import AsyncCycleTLS


# Browser fingerprint configurations
CHROME_PROFILE = {
    "ja3": "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",
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
        "Upgrade-Insecure-Requests": "1",
    }
}

FIREFOX_PROFILE = {
    "ja3": "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "headers": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }
}

SAFARI_PROFILE = {
    "ja3": "771,4865-4867-4866-49196-49195-52393-49200-49199-52392-49162-49161-49172-49171-157-156-53-47-49160-49170-10,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513-21,29-23-24-25,0",
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "headers": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }
}


async def example_basic_ja3():
    """Basic JA3 fingerprint usage."""
    print("=== Basic JA3 Fingerprinting ===\n")

    print("Making request with Chrome JA3 fingerprint...")

    response = await cycletls.aget(
        "https://ja3er.com/json",
        ja3=CHROME_PROFILE["ja3"],
        user_agent=CHROME_PROFILE["user_agent"]
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"JA3 Hash: {data.get('ja3_hash', 'N/A')}")
        print(f"User Agent: {data.get('User-Agent', 'N/A')}")

    print()


async def example_different_browsers():
    """Test different browser fingerprints."""
    print("=== Different Browser Fingerprints ===\n")

    async with AsyncCycleTLS() as client:
        # Chrome
        print("1. Chrome fingerprint:")
        response = await client.get(
            "https://ja3er.com/json",
            ja3=CHROME_PROFILE["ja3"],
            user_agent=CHROME_PROFILE["user_agent"]
        )
        if response.status_code == 200:
            print(f"   JA3: {response.json().get('ja3_hash', 'N/A')}")

        # Firefox
        print("\n2. Firefox fingerprint:")
        response = await client.get(
            "https://ja3er.com/json",
            ja3=FIREFOX_PROFILE["ja3"],
            user_agent=FIREFOX_PROFILE["user_agent"]
        )
        if response.status_code == 200:
            print(f"   JA3: {response.json().get('ja3_hash', 'N/A')}")

        # Safari
        print("\n3. Safari fingerprint:")
        response = await client.get(
            "https://ja3er.com/json",
            ja3=SAFARI_PROFILE["ja3"],
            user_agent=SAFARI_PROFILE["user_agent"]
        )
        if response.status_code == 200:
            print(f"   JA3: {response.json().get('ja3_hash', 'N/A')}")

    print()


async def example_complete_browser_profile():
    """Use complete browser profile (JA3 + headers + user agent)."""
    print("=== Complete Browser Profile ===\n")

    print("Making request with complete Chrome profile...")

    async with AsyncCycleTLS() as client:
        response = await client.get(
            "https://ja3er.com/json",
            ja3=CHROME_PROFILE["ja3"],
            user_agent=CHROME_PROFILE["user_agent"],
            headers=CHROME_PROFILE["headers"]
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\nFingerprint Details:")
            print(f"  JA3 Hash: {data.get('ja3_hash', 'N/A')}")
            print(f"  User Agent: {data.get('User-Agent', 'N/A')}")
            print(f"  Headers sent: {len(CHROME_PROFILE['headers'])}")

    print()


async def example_concurrent_different_fingerprints():
    """Make concurrent requests with different browser fingerprints."""
    print("=== Concurrent Requests with Different Fingerprints ===\n")

    print("Making 3 concurrent requests (Chrome, Firefox, Safari)...")

    tasks = [
        cycletls.aget(
            "https://ja3er.com/json",
            ja3=CHROME_PROFILE["ja3"],
            user_agent=CHROME_PROFILE["user_agent"]
        ),
        cycletls.aget(
            "https://ja3er.com/json",
            ja3=FIREFOX_PROFILE["ja3"],
            user_agent=FIREFOX_PROFILE["user_agent"]
        ),
        cycletls.aget(
            "https://ja3er.com/json",
            ja3=SAFARI_PROFILE["ja3"],
            user_agent=SAFARI_PROFILE["user_agent"]
        ),
    ]

    responses = await asyncio.gather(*tasks)

    browsers = ["Chrome", "Firefox", "Safari"]
    for browser, response in zip(browsers, responses):
        if response.status_code == 200:
            ja3_hash = response.json().get('ja3_hash', 'N/A')
            print(f"{browser}: {ja3_hash}")

    print()


async def example_ja4r_fingerprint():
    """Use JA4R fingerprint."""
    print("=== JA4R Fingerprinting ===\n")

    # Chrome JA4R fingerprint
    ja4r = "t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,4469_0403,0804,0401,0503,0805,0501,0806,0601"

    print("Making request with JA4R fingerprint...")

    response = await cycletls.aget(
        "https://tls.peet.ws/api/all",
        ja4r=ja4r,
        user_agent=CHROME_PROFILE["user_agent"]
    )

    print(f"Status: {response.status_code}")
    print()


async def example_http2_fingerprint():
    """Use HTTP/2 settings fingerprint."""
    print("=== HTTP/2 Fingerprinting ===\n")

    # Chrome HTTP/2 settings
    http2_settings = {
        "HEADER_TABLE_SIZE": 65536,
        "MAX_CONCURRENT_STREAMS": 1000,
        "INITIAL_WINDOW_SIZE": 6291456,
        "MAX_HEADER_LIST_SIZE": 262144,
    }

    print("Making request with HTTP/2 settings fingerprint...")

    response = await cycletls.aget(
        "https://www.google.com",
        http2_settings=http2_settings,
        user_agent=CHROME_PROFILE["user_agent"]
    )

    print(f"Status: {response.status_code}")
    print()


async def example_fingerprint_rotation():
    """Rotate fingerprints across multiple requests."""
    print("=== Fingerprint Rotation ===\n")

    profiles = [
        ("Chrome", CHROME_PROFILE),
        ("Firefox", FIREFOX_PROFILE),
        ("Safari", SAFARI_PROFILE),
    ]

    async with AsyncCycleTLS() as client:
        print("Making 6 requests, rotating fingerprints...\n")

        for i in range(6):
            # Rotate through profiles
            browser, profile = profiles[i % 3]

            response = await client.get(
                f"https://ja3er.com/json?request={i}",
                ja3=profile["ja3"],
                user_agent=profile["user_agent"]
            )

            if response.status_code == 200:
                ja3_hash = response.json().get('ja3_hash', 'N/A')
                print(f"Request {i+1} ({browser}): {ja3_hash}")

    print()


async def example_concurrent_same_fingerprint():
    """Multiple concurrent requests with same fingerprint."""
    print("=== Concurrent Requests with Same Fingerprint ===\n")

    num_requests = 10
    print(f"Making {num_requests} concurrent requests with Chrome fingerprint...")

    tasks = [
        cycletls.aget(
            f"https://ja3er.com/json?id={i}",
            ja3=CHROME_PROFILE["ja3"],
            user_agent=CHROME_PROFILE["user_agent"]
        )
        for i in range(num_requests)
    ]

    responses = await asyncio.gather(*tasks)

    successful = sum(1 for r in responses if r.status_code == 200)
    print(f"Completed: {successful}/{num_requests} successful")

    # Verify all used same fingerprint
    if all(r.status_code == 200 for r in responses):
        ja3_hashes = [r.json().get('ja3_hash') for r in responses]
        all_same = len(set(ja3_hashes)) == 1
        print(f"All same fingerprint: {all_same}")
        if all_same:
            print(f"JA3 Hash: {ja3_hashes[0]}")

    print()


async def example_bypass_detection():
    """Example of bypassing TLS fingerprint detection."""
    print("=== Bypassing TLS Detection ===\n")

    # Some sites check for automated browsers
    # Using proper fingerprints can help bypass detection

    print("Making request to a protected site with proper fingerprint...")

    async with AsyncCycleTLS() as client:
        response = await client.get(
            "https://www.google.com",
            ja3=CHROME_PROFILE["ja3"],
            user_agent=CHROME_PROFILE["user_agent"],
            headers=CHROME_PROFILE["headers"]
        )

        print(f"Status: {response.status_code}")
        print(f"Response size: {len(response.text)} bytes")

        if response.status_code == 200:
            print("✓ Successfully accessed protected site")
        else:
            print("✗ Request blocked or failed")

    print()


async def example_custom_header_order():
    """Use custom header ordering with fingerprints."""
    print("=== Custom Header Order with Fingerprints ===\n")

    # Chrome's typical header order
    header_order = [
        ":method",
        ":authority",
        ":scheme",
        ":path",
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
        "accept-language",
    ]

    print("Making request with custom header order...")

    response = await cycletls.aget(
        "https://www.google.com",
        ja3=CHROME_PROFILE["ja3"],
        user_agent=CHROME_PROFILE["user_agent"],
        header_order=header_order
    )

    print(f"Status: {response.status_code}")
    print()


async def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("CycleTLS Async TLS Fingerprinting Examples")
    print("="*60 + "\n")

    await example_basic_ja3()
    await example_different_browsers()
    await example_complete_browser_profile()
    await example_concurrent_different_fingerprints()
    await example_ja4r_fingerprint()
    await example_http2_fingerprint()
    await example_fingerprint_rotation()
    await example_concurrent_same_fingerprint()
    await example_bypass_detection()
    await example_custom_header_order()

    print("="*60)
    print("All examples completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
