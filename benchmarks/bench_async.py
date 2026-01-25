#!/usr/bin/env python3
"""Comprehensive asynchronous HTTP client library benchmark tool."""

import argparse
import asyncio
import os
import sys
import time
from typing import Dict, List

import pandas as pd

# Add parent directory to path for cycletls import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmarks.core import add_package_version, run_async_tests
from benchmarks.chart import plot_benchmark_multi, plot_cycletls_focus

# Try to install uvloop for better async performance
try:
    import uvloop
    uvloop.install()
except ImportError:
    pass


def import_async_libraries():
    """Import all async-capable benchmark libraries."""
    libraries = {}
    errors = []

    # Try importing each async library
    try:
        import httpx
        libraries['httpx'] = httpx.AsyncClient
    except ImportError as e:
        errors.append(f"httpx: {e}")

    try:
        import aiohttp
        libraries['aiohttp'] = aiohttp.ClientSession
    except ImportError as e:
        errors.append(f"aiohttp: {e}")

    try:
        import curl_cffi.requests
        libraries['curl_cffi'] = curl_cffi.requests.AsyncSession
    except ImportError as e:
        errors.append(f"curl_cffi: {e}")

    try:
        import rnet
        libraries['rnet'] = rnet.Client
    except ImportError as e:
        errors.append(f"rnet: {e}")


    # Try importing cycletls async
    try:
        from cycletls import aget

        class CycleTLSAsyncSession:
            """Wrapper for CycleTLS async operations."""

            async def get(self, url: str):
                return await aget(url)

            async def close(self):
                pass

            async def aclose(self):
                pass

        libraries['cycletls'] = CycleTLSAsyncSession
    except ImportError as e:
        errors.append(f"cycletls: {e}")

    if errors:
        print("\nWarning: Some async libraries could not be imported:")
        for error in errors:
            print(f"  - {error}")
        print("\nInstall missing dependencies with:")
        print("  pip install -e '.[benchmark]'")
        print()

    return libraries


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="HTTP Client Benchmark Tool - Asynchronous Tests",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:5001/",
        help="URL to benchmark against",
    )

    parser.add_argument(
        "--url-small",
        type=str,
        help="URL for small payload (~20KB). If not set, uses --url",
    )

    parser.add_argument(
        "--url-medium",
        type=str,
        help="URL for medium payload (~50KB). If not set, uses --url",
    )

    parser.add_argument(
        "--url-large",
        type=str,
        help="URL for large payload (~200KB). If not set, uses --url",
    )

    parser.add_argument(
        "--repetitions",
        "-r",
        type=int,
        default=10000,
        help="Number of requests per test",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="benchmark_async_results.csv",
        help="Output CSV file name",
    )

    parser.add_argument(
        "--chart",
        "-c",
        type=str,
        default="benchmark_async_results.jpg",
        help="Output chart file name",
    )

    parser.add_argument(
        "--cycletls-chart",
        type=str,
        default="cycletls_async_comparison.jpg",
        help="Output CycleTLS comparison chart file name",
    )

    parser.add_argument(
        "--no-visualization",
        action="store_true",
        help="Skip generating charts",
    )

    parser.add_argument(
        "--libraries",
        nargs="+",
        help="Specific libraries to test (default: all available)",
    )

    parser.add_argument(
        "--include-sync-baseline",
        action="store_true",
        help="Include synchronous CycleTLS baseline for comparison",
    )

    return parser.parse_args()


async def run_sync_cycletls_baseline(url: str, repetitions: int) -> Dict:
    """Run synchronous CycleTLS as a baseline."""
    try:
        from cycletls import get

        print("  Running synchronous CycleTLS baseline...")
        cpu_start = time.process_time()
        wall_start = time.perf_counter()

        for _ in range(repetitions):
            get(url)

        wall_time = time.perf_counter() - wall_start
        cpu_time = time.process_time() - cpu_start

        size = url.split('/')[-1] if '/' in url else 'default'

        return {
            'library': 'cycletls_sync',
            'version': 'baseline',
            'session_type': 'sync_baseline',
            'payload_size': size,
            'requests': repetitions,
            'wall_time': wall_time,
            'cpu_time': cpu_time,
            'req_per_sec': repetitions / wall_time if wall_time > 0 else 0,
        }
    except Exception as e:
        print(f"    Failed: {e}")
        return None


def main():
    """Main entry point."""
    args = parse_arguments()

    # Determine URLs for different payload sizes
    urls = {
        '20k': args.url_small or args.url,
        '50k': args.url_medium or args.url,
        '200k': args.url_large or args.url,
    }

    # If all URLs are the same, just use 'default' as the size
    if len(set(urls.values())) == 1:
        urls = {'default': args.url}

    print("=" * 70)
    print("HTTP Client Library Benchmark - Asynchronous Tests")
    print("=" * 70)
    print(f"Requests per test: {args.repetitions}")
    print(f"URLs:")
    for size, url in urls.items():
        print(f"  {size}: {url}")
    print(f"Output CSV: {args.output}")
    if not args.no_visualization:
        print(f"Output chart: {args.chart}")
        print(f"CycleTLS chart: {args.cycletls_chart}")
    print("=" * 70)
    print()

    # Import available async libraries
    libraries = import_async_libraries()

    if not libraries:
        print("Error: No async libraries could be imported. Please install dependencies.")
        sys.exit(1)

    # Filter libraries if specific ones requested
    if args.libraries:
        libraries = {
            name: cls for name, cls in libraries.items()
            if name in args.libraries
        }
        if not libraries:
            print(f"Error: None of the specified libraries are available: {args.libraries}")
            sys.exit(1)

    # Prepare package list
    async_packages = [(name, cls) for name, cls in libraries.items()]
    async_packages = add_package_version(async_packages)

    print(f"Testing {len(async_packages)} async libraries:\n  {', '.join([p[0] for p in async_packages])}\n")

    # Run benchmarks
    all_results = []

    for size, url in urls.items():
        print(f"\nTesting with {size} payload ({url})...")
        print("-" * 70)

        # Run sync baseline if requested
        if args.include_sync_baseline:
            result = asyncio.run(run_sync_cycletls_baseline(url, args.repetitions))
            if result:
                all_results.append(result)

        # Run async tests
        results = run_async_tests(async_packages, url, args.repetitions)
        all_results.extend(results)

    # Save results to CSV
    if all_results:
        print(f"\nSaving results to {args.output}...")
        df = pd.DataFrame(all_results)
        df.to_csv(args.output, index=False)

        # Print summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(df.groupby(['library', 'session_type'])['req_per_sec'].mean().to_string())
        print("=" * 70)

        # Generate visualizations
        if not args.no_visualization:
            print(f"\nGenerating chart {args.chart}...")
            plot_benchmark_multi(df, args.chart)

            if 'cycletls' in df['library'].values:
                print(f"Generating CycleTLS comparison chart {args.cycletls_chart}...")
                plot_cycletls_focus(df, args.cycletls_chart)

        print("\nBenchmark completed successfully!")
    else:
        print("\nNo results collected. Check for errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
