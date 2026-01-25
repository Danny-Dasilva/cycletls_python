#!/usr/bin/env python3
"""Comprehensive HTTP client library benchmark tool."""

import argparse
import os
import sys
from typing import Dict, List, Optional

import pandas as pd

# Add parent directory to path for cycletls import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmarks.core import add_package_version, run_sync_tests
from benchmarks.chart import plot_benchmark_multi, plot_cycletls_focus


def import_libraries():
    """Import all benchmark libraries and handle missing dependencies."""
    libraries = {}
    errors = []

    # Try importing each library
    try:
        import requests
        libraries['requests'] = requests.Session
    except ImportError as e:
        errors.append(f"requests: {e}")

    try:
        import httpx
        libraries['httpx'] = httpx.Client
    except ImportError as e:
        errors.append(f"httpx: {e}")

    try:
        import niquests
        libraries['niquests'] = niquests.Session
    except ImportError as e:
        errors.append(f"niquests: {e}")

    try:
        import curl_cffi.requests
        libraries['curl_cffi'] = curl_cffi.requests.Session
    except ImportError as e:
        errors.append(f"curl_cffi: {e}")

    try:
        import tls_client
        libraries['tls_client'] = tls_client.Session
    except ImportError as e:
        errors.append(f"tls_client: {e}")

    try:
        import primp
        libraries['primp'] = primp.Client
    except ImportError as e:
        errors.append(f"primp: {e}")

    try:
        import hrequests
        libraries['hrequests'] = hrequests.Session
    except ImportError as e:
        errors.append(f"hrequests: {e}")

    try:
        import rnet.blocking
        libraries['rnet'] = rnet.blocking.Client
    except ImportError as e:
        errors.append(f"rnet: {e}")

    try:
        from benchmarks.core import PycurlSession
        import pycurl
        libraries['pycurl'] = PycurlSession
    except ImportError as e:
        errors.append(f"pycurl: {e}")

    # Try importing cycletls
    try:
        from cycletls import CycleTLS
        # Create a wrapper class for cycletls
        class CycleTLSSession:
            def __init__(self):
                self.client = CycleTLS()

            def get(self, url: str):
                return self.client.get(url)

            def close(self):
                self.client.close()

        libraries['cycletls'] = CycleTLSSession
    except ImportError as e:
        errors.append(f"cycletls: {e}")

    if errors:
        print("\nWarning: Some libraries could not be imported:")
        for error in errors:
            print(f"  - {error}")
        print("\nInstall missing dependencies with:")
        print("  pip install -e '.[benchmark]'")
        print()

    return libraries


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="HTTP Client Benchmark Tool - Synchronous Tests",
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
        default="benchmark_results.csv",
        help="Output CSV file name",
    )

    parser.add_argument(
        "--chart",
        "-c",
        type=str,
        default="benchmark_results.jpg",
        help="Output chart file name",
    )

    parser.add_argument(
        "--cycletls-chart",
        type=str,
        default="cycletls_comparison.jpg",
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

    return parser.parse_args()


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
    print("HTTP Client Library Benchmark - Synchronous Tests")
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

    # Import available libraries
    libraries = import_libraries()

    if not libraries:
        print("Error: No libraries could be imported. Please install dependencies.")
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
    sync_packages = [(name, cls) for name, cls in libraries.items()]
    sync_packages = add_package_version(sync_packages)

    print(f"Testing {len(sync_packages)} libraries:\n  {', '.join([p[0] for p in sync_packages])}\n")

    # Run benchmarks
    all_results = []

    for size, url in urls.items():
        print(f"\nTesting with {size} payload ({url})...")
        print("-" * 70)
        results = run_sync_tests(sync_packages, url, args.repetitions)
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
