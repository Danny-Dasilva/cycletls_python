#!/usr/bin/env python3
"""Benchmark script to compare batch vs individual request performance."""

import argparse
import time
import statistics
from cycletls import CycleTLS


def benchmark_individual_requests(client: CycleTLS, url: str, count: int) -> float:
    """Time individual requests."""
    start = time.perf_counter()
    for _ in range(count):
        client.get(url)
    return time.perf_counter() - start


def benchmark_batch_requests(client: CycleTLS, url: str, count: int) -> float:
    """Time batch requests."""
    requests = [{"url": url, "method": "GET"} for _ in range(count)]
    start = time.perf_counter()
    client.batch(requests)
    return time.perf_counter() - start


def main():
    parser = argparse.ArgumentParser(description="Benchmark batch vs individual requests")
    parser.add_argument("--url", default="https://httpbin.org/get", help="URL to request")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of requests per batch")
    parser.add_argument("--iterations", type=int, default=5, help="Number of iterations for timing")
    args = parser.parse_args()

    print(f"Benchmarking: {args.url}")
    print(f"Batch size: {args.batch_size}")
    print(f"Iterations: {args.iterations}")
    print("-" * 60)

    with CycleTLS() as client:
        # Warm up
        print("Warming up...")
        client.get(args.url)
        client.batch([{"url": args.url, "method": "GET"}])

        # Benchmark individual requests
        individual_times = []
        print(f"\nBenchmarking individual requests ({args.batch_size} requests x {args.iterations} iterations)...")
        for i in range(args.iterations):
            t = benchmark_individual_requests(client, args.url, args.batch_size)
            individual_times.append(t)
            print(f"  Iteration {i + 1}: {t:.3f}s")

        # Benchmark batch requests
        batch_times = []
        print(f"\nBenchmarking batch requests ({args.batch_size} requests x {args.iterations} iterations)...")
        for i in range(args.iterations):
            t = benchmark_batch_requests(client, args.url, args.batch_size)
            batch_times.append(t)
            print(f"  Iteration {i + 1}: {t:.3f}s")

    # Calculate statistics
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    avg_individual = statistics.mean(individual_times)
    avg_batch = statistics.mean(batch_times)
    speedup = avg_individual / avg_batch if avg_batch > 0 else 0

    print(f"\nIndividual requests:")
    print(f"  Average: {avg_individual:.3f}s")
    print(f"  Min: {min(individual_times):.3f}s")
    print(f"  Max: {max(individual_times):.3f}s")
    if len(individual_times) > 1:
        print(f"  Stddev: {statistics.stdev(individual_times):.3f}s")

    print(f"\nBatch requests:")
    print(f"  Average: {avg_batch:.3f}s")
    print(f"  Min: {min(batch_times):.3f}s")
    print(f"  Max: {max(batch_times):.3f}s")
    if len(batch_times) > 1:
        print(f"  Stddev: {statistics.stdev(batch_times):.3f}s")

    print(f"\nSpeedup: {speedup:.2f}x")
    print(f"Time saved per batch: {avg_individual - avg_batch:.3f}s")

    # Per-request throughput
    individual_rps = args.batch_size / avg_individual
    batch_rps = args.batch_size / avg_batch
    print(f"\nThroughput:")
    print(f"  Individual: {individual_rps:.1f} req/s")
    print(f"  Batch: {batch_rps:.1f} req/s")


if __name__ == "__main__":
    main()
