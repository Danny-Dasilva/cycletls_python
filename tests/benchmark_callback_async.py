#!/usr/bin/env python3
"""Benchmark comparing polling vs callback-based async for CycleTLS.

This benchmark measures:
1. Total execution time for N requests
2. Implicit FFI call reduction (callback uses 2 calls vs polling's 10-200)
"""

import asyncio
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cycletls._ffi import send_request_async, send_request_async_callback


async def benchmark_polling(url: str, n: int) -> tuple[float, list]:
    """Benchmark polling-based async."""
    payloads = [
        {
            "requestId": f"poll-{i}",
            "options": {
                "url": url,
                "method": "GET",
                "headers": {},
                "body": "",
                "ja3": "",
                "userAgent": "Benchmark-Polling/1.0"
            }
        }
        for i in range(n)
    ]

    start = time.perf_counter()
    results = await asyncio.gather(
        *[send_request_async(p, poll_interval=0.0, timeout=30.0) for p in payloads]
    )
    elapsed = time.perf_counter() - start

    return elapsed, results


async def benchmark_callback(url: str, n: int) -> tuple[float, list]:
    """Benchmark callback-based async."""
    payloads = [
        {
            "requestId": f"callback-{i}",
            "options": {
                "url": url,
                "method": "GET",
                "headers": {},
                "body": "",
                "ja3": "",
                "userAgent": "Benchmark-Callback/1.0"
            }
        }
        for i in range(n)
    ]

    start = time.perf_counter()
    results = await asyncio.gather(
        *[send_request_async_callback(p, timeout=30.0) for p in payloads]
    )
    elapsed = time.perf_counter() - start

    return elapsed, results


async def main():
    """Run benchmarks."""
    url = "https://httpbin.org/get"
    n_requests = 10  # Number of concurrent requests

    print("=" * 60)
    print("CycleTLS Async Benchmark: Polling vs Callback")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Concurrent requests: {n_requests}")
    print()

    # Warmup
    print("Warming up...")
    await benchmark_polling(url, 1)
    await benchmark_callback(url, 1)
    print()

    # Run benchmarks
    print("Running polling benchmark...")
    poll_time, poll_results = await benchmark_polling(url, n_requests)
    poll_success = sum(1 for r in poll_results if r.get("Status") == 200)

    print("Running callback benchmark...")
    callback_time, callback_results = await benchmark_callback(url, n_requests)
    callback_success = sum(1 for r in callback_results if r.get("Status") == 200)

    # Results
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Polling:  {poll_time:.3f}s ({poll_success}/{n_requests} successful)")
    print(f"Callback: {callback_time:.3f}s ({callback_success}/{n_requests} successful)")
    print()

    if callback_time < poll_time:
        speedup = (poll_time / callback_time - 1) * 100
        print(f"Callback is {speedup:.1f}% faster than polling")
    else:
        slowdown = (callback_time / poll_time - 1) * 100
        print(f"Callback is {slowdown:.1f}% slower than polling")

    print()
    print("FFI Call Analysis:")
    print("-" * 40)
    print(f"Polling:  ~{n_requests * 50} FFI calls (estimate)")
    print(f"         (submit + ~50 check polls per request)")
    print(f"Callback: {n_requests * 2} FFI calls (exact)")
    print(f"         (1 submit + 1 get per request)")
    print(f"Reduction: ~{(1 - 2/50) * 100:.0f}% fewer FFI calls")
    print()

    return 0 if callback_success == n_requests else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
