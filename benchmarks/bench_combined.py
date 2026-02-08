#!/usr/bin/env python3
"""Combined benchmark runner that produces a single ranked table.

Runs both sync and async benchmarks, picks the best session variant per library,
and outputs a combined CSV + markdown table sorted by µs/req.

Usage:
    python benchmarks/bench_combined.py --url http://localhost:5002/ -r 500
"""

import argparse
import asyncio
import csv
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Type

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmarks.core import (
    CycleTLSAsyncSession,
    CycleTLSSession,
    PycurlSession,
    Urllib3Session,
)


def import_sync_libraries() -> Dict[str, Tuple[Type, str]]:
    """Import sync libraries. Returns {name: (class, label)}."""
    libraries = {}
    errors = []

    try:
        import requests as req_lib
        libraries['requests'] = (req_lib.Session, 'session')
    except ImportError as e:
        errors.append(f"requests: {e}")

    try:
        import httpx
        libraries['httpx'] = (httpx.Client, 'sync')
    except ImportError as e:
        errors.append(f"httpx: {e}")

    try:
        import niquests
        libraries['niquests'] = (niquests.Session, 'session')
    except ImportError as e:
        errors.append(f"niquests: {e}")

    try:
        import curl_cffi.requests
        libraries['curl_cffi'] = (curl_cffi.requests.Session, 'sync')
    except ImportError as e:
        errors.append(f"curl_cffi: {e}")

    try:
        import tls_client
        libraries['tls_client'] = (tls_client.Session, 'sync')
    except ImportError as e:
        errors.append(f"tls_client: {e}")

    try:
        import primp
        libraries['primp'] = (primp.Client, 'sync')
    except ImportError as e:
        errors.append(f"primp: {e}")

    try:
        import hrequests
        libraries['hrequests'] = (hrequests.Session, 'sync')
    except ImportError as e:
        errors.append(f"hrequests: {e}")

    try:
        import urllib3  # noqa: F401 - verify availability
        libraries['urllib3'] = (Urllib3Session, 'pooled')
    except ImportError as e:
        errors.append(f"urllib3: {e}")

    try:
        import pycurl  # noqa: F401 - verify availability
        libraries['pycurl'] = (PycurlSession, 'reuse')
    except ImportError as e:
        errors.append(f"pycurl: {e}")

    try:
        from cycletls import CycleTLS  # noqa: F401 - verify availability
        libraries['cycletls'] = (CycleTLSSession, 'sync')
    except ImportError as e:
        errors.append(f"cycletls: {e}")

    if errors:
        print("  Missing sync libraries:")
        for error in errors:
            print(f"    - {error}")

    return libraries


def import_async_libraries() -> Dict[str, Tuple[Type, str]]:
    """Import async libraries. Returns {name: (class, label)}."""
    libraries = {}
    errors = []

    try:
        import aiohttp
        libraries['aiohttp'] = (aiohttp.ClientSession, 'async')
    except ImportError as e:
        errors.append(f"aiohttp: {e}")

    try:
        import curl_cffi.requests
        libraries['curl_cffi'] = (curl_cffi.requests.AsyncSession, 'async')
    except ImportError as e:
        errors.append(f"curl_cffi: {e}")

    try:
        import primp
        libraries['primp'] = (primp.AsyncClient, 'async')
    except ImportError as e:
        errors.append(f"primp: {e}")

    try:
        from cycletls import aget  # noqa: F401 - verify availability
        libraries['cycletls'] = (CycleTLSAsyncSession, 'async')
    except ImportError as e:
        errors.append(f"cycletls: {e}")

    if errors:
        print("  Missing async libraries:")
        for error in errors:
            print(f"    - {error}")

    return libraries


def run_sync_benchmark(
    name: str, session_class: Type, url: str, reps: int
) -> Optional[Dict[str, Any]]:
    """Run a sync benchmark with session reuse."""
    print(f"  {name} (sync)...", end=" ", flush=True)
    try:
        session = session_class()
        try:
            start = time.perf_counter()
            for _ in range(reps):
                response = session.get(url)
                # Access response body to ensure it's read
                if hasattr(response, 'text'):
                    _ = response.text
                elif hasattr(response, 'data'):
                    _ = response.data
                elif hasattr(response, 'body'):
                    _ = response.body
            elapsed = time.perf_counter() - start
        finally:
            if hasattr(session, 'close'):
                session.close()

        req_per_sec = reps / elapsed if elapsed > 0 else 0
        us_per_req = (elapsed * 1_000_000 / reps) if reps > 0 else 0
        print(f"{us_per_req:.1f} µs/req, {req_per_sec:.0f} req/s")
        return {
            'library': name,
            'elapsed': elapsed,
            'reps': reps,
            'req_per_sec': req_per_sec,
            'us_per_req': us_per_req,
        }
    except Exception as e:
        print(f"FAILED: {e}")
        return None


async def run_async_benchmark(
    name: str, session_class: Type, url: str, reps: int
) -> Optional[Dict[str, Any]]:
    """Run an async benchmark with session reuse and concurrent requests."""
    print(f"  {name} (async)...", end=" ", flush=True)

    async def _execute(session, url: str, lib_name: str):
        if lib_name == 'aiohttp':
            async with session.get(url) as response:
                return await response.text()
        else:
            response = await session.get(url)
            return response.text if hasattr(response, 'text') else None

    try:
        session = session_class()
        try:
            start = time.perf_counter()
            tasks = [_execute(session, url, name) for _ in range(reps)]
            await asyncio.gather(*tasks)
            elapsed = time.perf_counter() - start
        finally:
            if hasattr(session, 'aclose'):
                await session.aclose()
            elif hasattr(session, 'close'):
                if asyncio.iscoroutinefunction(session.close):
                    await session.close()
                else:
                    session.close()

        req_per_sec = reps / elapsed if elapsed > 0 else 0
        us_per_req = (elapsed * 1_000_000 / reps) if reps > 0 else 0
        print(f"{us_per_req:.1f} µs/req, {req_per_sec:.0f} req/s")
        return {
            'library': name,
            'elapsed': elapsed,
            'reps': reps,
            'req_per_sec': req_per_sec,
            'us_per_req': us_per_req,
        }
    except Exception as e:
        print(f"FAILED: {e}")
        return None


def compute_vs_requests(results: List[Dict], baseline_time: Optional[float]) -> List[Dict]:
    """Add vs_requests column to results."""
    for r in results:
        if baseline_time is None or r['elapsed'] <= 0:
            r['vs_requests'] = 'N/A'
        elif r['library'] == 'requests':
            r['vs_requests'] = 'baseline'
        else:
            ratio = baseline_time / r['elapsed']
            if ratio >= 1.0:
                r['vs_requests'] = f'{ratio:.1f}x faster'
            else:
                r['vs_requests'] = f'{1/ratio:.1f}x slower'
    return results


def print_markdown_table(results: List[Dict]) -> None:
    """Print results as a markdown table."""
    print("\n| Library | µs/req | Requests/sec | vs Requests |")
    print("|---------|--------|-------------|-------------|")
    for r in results:
        lib = r['display_name']
        us = f"{r['us_per_req']:.1f}"
        rps = f"{r['req_per_sec']:,.0f}"
        vs = r.get('vs_requests', 'N/A')
        print(f"| {lib} | {us} | {rps} | {vs} |")


def write_csv_output(results: List[Dict], output_file: str) -> None:
    """Write combined results to CSV."""
    with open(output_file, 'w', newline='') as f:
        fieldnames = ['library', 'us_per_req', 'requests_per_sec', 'vs_requests']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                'library': r['display_name'],
                'us_per_req': f"{r['us_per_req']:.1f}",
                'requests_per_sec': f"{r['req_per_sec']:.0f}",
                'vs_requests': r.get('vs_requests', 'N/A'),
            })
    print(f"\nCSV written to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Combined HTTP client benchmark (sync + async)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--url", default="http://localhost:5001/", help="Target URL")
    parser.add_argument("-r", "--repetitions", type=int, default=500, help="Requests per test")
    parser.add_argument("-o", "--output", default="benchmark_combined.csv", help="Output CSV")
    args = parser.parse_args()

    url = args.url
    reps = args.repetitions

    print("=" * 70)
    print("Combined HTTP Client Benchmark (Sync + Async)")
    print(f"URL: {url}  |  Repetitions: {reps}")
    print("=" * 70)

    # --- Import libraries ---
    print("\nImporting libraries...")
    sync_libs = import_sync_libraries()
    async_libs = import_async_libraries()

    # --- Run sync benchmarks ---
    sync_results = {}
    if sync_libs:
        print(f"\nSync benchmarks ({len(sync_libs)} libraries):")
        print("-" * 50)
        for name, (cls, label) in sync_libs.items():
            result = run_sync_benchmark(name, cls, url, reps)
            if result:
                result['label'] = label
                result['mode'] = 'sync'
                sync_results[name] = result

    # --- Run async benchmarks ---
    async_results = {}
    if async_libs:
        print(f"\nAsync benchmarks ({len(async_libs)} libraries):")
        print("-" * 50)
        for name, (cls, label) in async_libs.items():
            result = asyncio.run(run_async_benchmark(name, cls, url, reps))
            if result:
                result['label'] = label
                result['mode'] = 'async'
                async_results[name] = result

    # --- Combine: pick best per library, but keep both sync and async if both tested ---
    def _display_name(name: str, label: str) -> str:
        if name == 'cycletls':
            return f"**{name}** ({label})"
        return f"{name} ({label})"

    combined = []
    all_names = sync_results.keys() | async_results.keys()

    for name in all_names:
        for result in (sync_results.get(name), async_results.get(name)):
            if result is not None:
                result['display_name'] = _display_name(name, result['label'])
                combined.append(result)

    # Sort by µs/req (fastest first)
    combined.sort(key=lambda x: x['us_per_req'])

    # Compute vs_requests
    baseline_time = None
    for r in combined:
        if r['library'] == 'requests':
            baseline_time = r['elapsed']
            break

    combined = compute_vs_requests(combined, baseline_time)

    # --- Output ---
    print("\n" + "=" * 70)
    print(f"RESULTS ({reps} requests per test)")
    print("=" * 70)
    print_markdown_table(combined)
    write_csv_output(combined, args.output)


if __name__ == "__main__":
    main()
