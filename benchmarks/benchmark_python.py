#!/usr/bin/env python3
"""
CycleTLS Python Benchmarks

A self-contained benchmark script to test CycleTLS performance against the Go
benchmark server. Tests both sync and async performance, with optional comparison
against the requests library.

Usage:
    python benchmarks/benchmark_python.py --url http://localhost:5001/ --repetitions 1000

Requirements:
    - CycleTLS installed (pip install cycletls or pip install -e .)
    - bench_server.go running (go run bench_server.go)
    - Optional: requests library for comparison
"""

import argparse
import asyncio
import csv
import sys
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

# Try importing cycletls
try:
    import cycletls
    from cycletls import CycleTLS, AsyncCycleTLS, get, aget
    CYCLETLS_AVAILABLE = True
except ImportError:
    CYCLETLS_AVAILABLE = False
    print("Warning: cycletls not available. Install with: pip install cycletls")

# Try importing requests for comparison
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


@dataclass
class BenchmarkResult:
    """Holds the result of a single benchmark run."""
    name: str
    elapsed_seconds: float
    requests_count: int
    errors: int
    requests_per_second: float

    def to_dict(self) -> dict:
        """Convert to dictionary for CSV output."""
        return {
            "name": self.name,
            "elapsed_seconds": f"{self.elapsed_seconds:.4f}",
            "requests_count": self.requests_count,
            "errors": self.errors,
            "requests_per_second": f"{self.requests_per_second:.2f}",
        }


def benchmark_cycletls_sync_session(url: str, reps: int) -> Tuple[float, int]:
    """
    Benchmark CycleTLS synchronous requests with session reuse.

    Uses a single CycleTLS instance for all requests (connection pooling).
    """
    if not CYCLETLS_AVAILABLE:
        raise ImportError("cycletls not available")

    errors = 0
    client = CycleTLS()
    try:
        start = time.perf_counter()
        for _ in range(reps):
            try:
                response = client.get(url)
                if response.status_code >= 400:
                    errors += 1
            except Exception:
                errors += 1
        elapsed = time.perf_counter() - start
    finally:
        client.close()

    return elapsed, errors


def benchmark_cycletls_sync_no_session(url: str, reps: int) -> Tuple[float, int]:
    """
    Benchmark CycleTLS synchronous requests without session reuse.

    Uses module-level get() function which uses a global session.
    """
    if not CYCLETLS_AVAILABLE:
        raise ImportError("cycletls not available")

    errors = 0
    start = time.perf_counter()
    for _ in range(reps):
        try:
            response = get(url)
            if response.status_code >= 400:
                errors += 1
        except Exception:
            errors += 1
    elapsed = time.perf_counter() - start

    return elapsed, errors


async def benchmark_cycletls_async_sequential(url: str, reps: int) -> Tuple[float, int]:
    """
    Benchmark CycleTLS asynchronous requests executed sequentially.

    Each request waits for the previous one to complete.
    """
    if not CYCLETLS_AVAILABLE:
        raise ImportError("cycletls not available")

    errors = 0
    start = time.perf_counter()

    async with AsyncCycleTLS() as client:
        for _ in range(reps):
            try:
                response = await client.get(url)
                if response.status_code >= 400:
                    errors += 1
            except Exception:
                errors += 1

    elapsed = time.perf_counter() - start
    return elapsed, errors


async def benchmark_cycletls_async_concurrent(url: str, reps: int) -> Tuple[float, int]:
    """
    Benchmark CycleTLS asynchronous requests executed concurrently.

    All requests are submitted at once using asyncio.gather().
    """
    if not CYCLETLS_AVAILABLE:
        raise ImportError("cycletls not available")

    errors = 0
    start = time.perf_counter()

    # Submit all requests concurrently
    tasks = [aget(url) for _ in range(reps)]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    for response in responses:
        if isinstance(response, Exception):
            errors += 1
        elif hasattr(response, 'status_code') and response.status_code >= 400:
            errors += 1

    elapsed = time.perf_counter() - start
    return elapsed, errors


def benchmark_requests_session(url: str, reps: int) -> Tuple[float, int]:
    """
    Benchmark requests library with session reuse.
    """
    if not REQUESTS_AVAILABLE:
        raise ImportError("requests not available")

    errors = 0
    session = requests.Session()
    try:
        start = time.perf_counter()
        for _ in range(reps):
            try:
                response = session.get(url, verify=False)
                if response.status_code >= 400:
                    errors += 1
            except Exception:
                errors += 1
        elapsed = time.perf_counter() - start
    finally:
        session.close()

    return elapsed, errors


def benchmark_requests_no_session(url: str, reps: int) -> Tuple[float, int]:
    """
    Benchmark requests library without session reuse.
    """
    if not REQUESTS_AVAILABLE:
        raise ImportError("requests not available")

    errors = 0
    start = time.perf_counter()
    for _ in range(reps):
        try:
            response = requests.get(url, verify=False)
            if response.status_code >= 400:
                errors += 1
        except Exception:
            errors += 1
    elapsed = time.perf_counter() - start

    return elapsed, errors


def run_benchmark(
    name: str,
    func,
    url: str,
    reps: int,
    is_async: bool = False
) -> Optional[BenchmarkResult]:
    """
    Run a single benchmark and return results.

    Args:
        name: Human-readable name for the benchmark
        func: The benchmark function to run
        url: Target URL
        reps: Number of repetitions
        is_async: Whether the function is async

    Returns:
        BenchmarkResult or None if the benchmark failed
    """
    print(f"  Running {name}...")
    try:
        if is_async:
            elapsed, errors = asyncio.run(func(url, reps))
        else:
            elapsed, errors = func(url, reps)

        req_per_sec = reps / elapsed if elapsed > 0 else 0
        result = BenchmarkResult(
            name=name,
            elapsed_seconds=elapsed,
            requests_count=reps,
            errors=errors,
            requests_per_second=req_per_sec,
        )
        print(f"    Time: {elapsed:.4f}s | Req/s: {req_per_sec:.2f} | Errors: {errors}")
        return result
    except ImportError as e:
        print(f"    Skipped: {e}")
        return None
    except Exception as e:
        print(f"    Failed: {e}")
        return None


def run_all_benchmarks(
    url: str,
    repetitions: int,
    include_requests: bool = True,
) -> List[BenchmarkResult]:
    """
    Run all available benchmarks.

    Args:
        url: Target URL to benchmark against
        repetitions: Number of requests per benchmark
        include_requests: Whether to include requests library comparison

    Returns:
        List of benchmark results
    """
    results: List[BenchmarkResult] = []

    print("\n" + "=" * 70)
    print("CycleTLS Python Benchmarks")
    print(f"URL: {url}")
    print(f"Repetitions: {repetitions}")
    print("=" * 70 + "\n")

    # CycleTLS sync benchmarks
    print("CycleTLS Synchronous Benchmarks:")
    print("-" * 40)

    result = run_benchmark(
        "cycletls_sync_session",
        benchmark_cycletls_sync_session,
        url,
        repetitions,
    )
    if result:
        results.append(result)

    result = run_benchmark(
        "cycletls_sync_global",
        benchmark_cycletls_sync_no_session,
        url,
        repetitions,
    )
    if result:
        results.append(result)

    # CycleTLS async benchmarks
    print("\nCycleTLS Asynchronous Benchmarks:")
    print("-" * 40)

    result = run_benchmark(
        "cycletls_async_sequential",
        benchmark_cycletls_async_sequential,
        url,
        repetitions,
        is_async=True,
    )
    if result:
        results.append(result)

    result = run_benchmark(
        "cycletls_async_concurrent",
        benchmark_cycletls_async_concurrent,
        url,
        repetitions,
        is_async=True,
    )
    if result:
        results.append(result)

    # Requests library benchmarks (optional comparison)
    if include_requests and REQUESTS_AVAILABLE:
        print("\nRequests Library Benchmarks (comparison):")
        print("-" * 40)

        result = run_benchmark(
            "requests_session",
            benchmark_requests_session,
            url,
            repetitions,
        )
        if result:
            results.append(result)

        result = run_benchmark(
            "requests_no_session",
            benchmark_requests_no_session,
            url,
            repetitions,
        )
        if result:
            results.append(result)

    return results


def print_summary(results: List[BenchmarkResult], repetitions: int) -> None:
    """Print a summary table of benchmark results."""
    if not results:
        print("\nNo results to summarize.")
        return

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"{'Benchmark':<30} {'Time (s)':<12} {'Req/s':<12} {'Errors':<10}")
    print("-" * 70)

    # Find baseline (first cycletls sync result) for speedup calculation
    baseline_time = None
    for r in results:
        if r.name.startswith("cycletls_sync"):
            baseline_time = r.elapsed_seconds
            break

    for r in results:
        speedup = ""
        if baseline_time and r.elapsed_seconds > 0:
            speedup_val = baseline_time / r.elapsed_seconds
            if speedup_val != 1.0:
                speedup = f"({speedup_val:.2f}x)"

        print(f"{r.name:<30} {r.elapsed_seconds:<12.4f} {r.requests_per_second:<12.2f} {r.errors:<10} {speedup}")

    print("=" * 70)


def write_csv(results: List[BenchmarkResult], output_file: str) -> None:
    """Write benchmark results to a CSV file."""
    if not results:
        print(f"No results to write to {output_file}")
        return

    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ["name", "elapsed_seconds", "requests_count", "errors", "requests_per_second"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result.to_dict())

    print(f"\nResults written to {output_file}")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="CycleTLS Python Benchmark Tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:5001/",
        help="URL to benchmark against (bench_server.go should be running)",
    )

    parser.add_argument(
        "--repetitions",
        "-r",
        type=int,
        default=1000,
        help="Number of requests per benchmark",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="benchmark_python_results.csv",
        help="Output CSV file name",
    )

    parser.add_argument(
        "--no-requests",
        action="store_true",
        help="Skip requests library comparison",
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Minimal output (just the summary)",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_arguments()

    # Validate inputs
    if args.repetitions < 1:
        print("Error: repetitions must be >= 1")
        return 1

    if not CYCLETLS_AVAILABLE:
        print("Error: cycletls is not installed. Install with: pip install cycletls")
        return 1

    # Print configuration
    if not args.quiet:
        print(f"Configuration:")
        print(f"  URL: {args.url}")
        print(f"  Repetitions: {args.repetitions}")
        print(f"  Output: {args.output}")
        print(f"  Include requests: {not args.no_requests}")

    # Run benchmarks
    results = run_all_benchmarks(
        url=args.url,
        repetitions=args.repetitions,
        include_requests=not args.no_requests,
    )

    # Print summary
    print_summary(results, args.repetitions)

    # Write CSV
    write_csv(results, args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
