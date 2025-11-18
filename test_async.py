#!/usr/bin/env python3
"""Test script for async CycleTLS implementation."""

import asyncio
import time
import os
import sys

# Set environment variable to use local build
os.environ["CYCLETLS_LIB_PATH"] = (
    "/Users/dannydasilva/Documents/personal/cycletls_python/dist/libcycletls.dylib"
)

# Add cycletls to path
sys.path.insert(0, "/Users/dannydasilva/Documents/personal/cycletls_python")

from cycletls import _ffi


async def test_single_async_request():
    """Test a single async request."""
    print("=" * 60)
    print("TEST 1: Single Async Request")
    print("=" * 60)

    payload = {
        "requestId": "test_async_1",
        "options": {
            "url": "http://localhost:5001/",
            "method": "GET",
        },
    }

    start = time.time()
    result = await _ffi.send_request_async(payload)
    elapsed = time.time() - start

    print(f"Status: {result.get('Status')}")
    print(f"URL: {result.get('FinalUrl')}")
    print(f"Time: {elapsed:.4f}s")
    print()


async def test_concurrent_async_requests():
    """Test multiple concurrent async requests."""
    print("=" * 60)
    print("TEST 2: Concurrent Async Requests (10 requests)")
    print("=" * 60)

    payloads = [
        {
            "requestId": f"test_async_{i}",
            "options": {
                "url": "http://localhost:5001/",
                "method": "GET",
            },
        }
        for i in range(10)
    ]

    start = time.time()
    results = await _ffi.send_requests_batch(payloads)
    elapsed = time.time() - start

    print(f"Completed: {len(results)} requests")
    print(f"Total time: {elapsed:.4f}s")
    print(f"Avg time per request: {elapsed / len(results):.4f}s")
    print(f"Requests per second: {len(results) / elapsed:.2f}")
    print()


async def test_large_batch():
    """Test large batch of concurrent requests."""
    print("=" * 60)
    print("TEST 3: Large Batch (100 requests)")
    print("=" * 60)

    payloads = [
        {
            "requestId": f"test_batch_{i}",
            "options": {
                "url": "http://localhost:5001/",
                "method": "GET",
            },
        }
        for i in range(100)
    ]

    start = time.time()
    results = await _ffi.send_requests_batch(payloads)
    elapsed = time.time() - start

    successful = sum(1 for r in results if r.get("Status") == 200)

    print(f"Completed: {successful}/{len(results)} successful")
    print(f"Total time: {elapsed:.4f}s")
    print(f"Avg time per request: {elapsed / len(results):.4f}s")
    print(f"Requests per second: {len(results) / elapsed:.2f}")
    print()


async def test_sync_vs_async():
    """Compare sync vs async performance."""
    print("=" * 60)
    print("TEST 4: Sync vs Async Comparison (10 requests)")
    print("=" * 60)

    payload_template = {
        "requestId": "test",
        "options": {
            "url": "http://localhost:5001/",
            "method": "GET",
        },
    }

    # Test sync (sequential)
    print("Running sync (sequential)...")
    start = time.time()
    for i in range(10):
        payload = payload_template.copy()
        payload["requestId"] = f"sync_{i}"
        result = _ffi.send_request(payload)
    sync_time = time.time() - start
    print(f"  Sync time: {sync_time:.4f}s")

    # Test async (concurrent)
    print("Running async (concurrent)...")
    payloads = [
        {
            "requestId": f"async_{i}",
            "options": {
                "url": "http://localhost:5001/",
                "method": "GET",
            },
        }
        for i in range(10)
    ]
    start = time.time()
    results = await _ffi.send_requests_batch(payloads)
    async_time = time.time() - start
    print(f"  Async time: {async_time:.4f}s")

    speedup = sync_time / async_time
    print(f"\n  Speedup: {speedup:.2f}x faster")
    print()


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("CycleTLS Async Implementation Tests")
    print("=" * 60)
    print()

    try:
        await test_single_async_request()
        await test_concurrent_async_requests()
        await test_large_batch()
        await test_sync_vs_async()

        print("=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
