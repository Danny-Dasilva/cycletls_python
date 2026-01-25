#!/usr/bin/env python3
"""Async benchmark for CycleTLS comparing sync vs async performance."""

import argparse
import asyncio
import csv
import os
import sys
import time

# Set environment variable to use local build
os.environ['CYCLETLS_LIB_PATH'] = '/Users/dannydasilva/Documents/personal/cycletls_python/dist/libcycletls.dylib'

# Add cycletls to path
sys.path.insert(0, '/Users/dannydasilva/Documents/personal/cycletls_python')

from cycletls import get, aget


def benchmark_sync(url: str, repetitions: int) -> float:
    """Benchmark synchronous requests using module-level get()."""
    start = time.time()
    for i in range(repetitions):
        response = get(url)
    elapsed = time.time() - start

    return elapsed




async def benchmark_async_concurrent(url: str, repetitions: int) -> float:
    """Benchmark async requests executed concurrently."""
    start = time.time()

    # Submit all requests concurrently
    tasks = [aget(url) for _ in range(repetitions)]
    responses = await asyncio.gather(*tasks)

    elapsed = time.time() - start

    return elapsed




async def run_all_benchmarks(url: str, repetitions: int, output_file: str = "results_async.csv"):
    """Run all benchmarks and save results."""
    print("=" * 70)
    print(f"CycleTLS Async Benchmarks")
    print(f"URL: {url}")
    print(f"Repetitions: {repetitions}")
    print("=" * 70)
    print()

    results = []

    # Test 1: Sync (baseline)
    print("Running SYNC benchmark...")
    sync_time = benchmark_sync(url, repetitions)
    print(f"  Time: {sync_time:.4f}s")
    print(f"  Requests/sec: {repetitions / sync_time:.2f}")
    print()
    results.append(("cycletls_sync", sync_time))



    # Test 3: Async Concurrent
    print("Running ASYNC CONCURRENT benchmark (all at once)...")
    async_con_time = await benchmark_async_concurrent(url, repetitions)
    print(f"  Time: {async_con_time:.4f}s")
    print(f"  Requests/sec: {repetitions / async_con_time:.2f}")
    print(f"  Speedup vs sync: {sync_time / async_con_time:.2f}x")
    print()
    results.append(("cycletls_async_concurrent", async_con_time))



    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"{'Method':<30} {'Time (s)':<12} {'Req/s':<12} {'Speedup':<10}")
    print("-" * 70)

    baseline = sync_time
    for name, elapsed in results:
        req_per_sec = repetitions / elapsed
        speedup = baseline / elapsed
        print(f"{name:<30} {elapsed:<12.4f} {req_per_sec:<12.2f} {speedup:<10.2f}x")

    print("=" * 70)
    print()

    # Save to CSV
    if output_file:
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['method', 'time_seconds', 'requests_per_second', 'speedup'])
            for name, elapsed in results:
                writer.writerow([
                    name,
                    f"{elapsed:.4f}",
                    f"{repetitions / elapsed:.2f}",
                    f"{baseline / elapsed:.2f}"
                ])
        print(f"Results saved to {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Benchmark CycleTLS sync vs async performance"
    )
    parser.add_argument(
        '--url',
        type=str,
        default='http://localhost:5001/',
        help="URL to test (default: http://localhost:5001/)"
    )
    parser.add_argument(
        '--repetitions',
        type=int,
        default=10000,
        help="Number of requests (default: 10000)"
    )
    parser.add_argument(
        '--output',
        type=str,
        default='results_async.csv',
        help="Output CSV file (default: results_async.csv)"
    )

    args = parser.parse_args()

    print(f"\nConfiguration: url={args.url}, repetitions={args.repetitions}, output={args.output}\n")

    asyncio.run(run_all_benchmarks(args.url, args.repetitions, args.output))


if __name__ == '__main__':
    main()
