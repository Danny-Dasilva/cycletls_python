# CycleTLS Benchmark Suite

Comprehensive benchmarking suite for comparing HTTP client libraries, with a focus on CycleTLS performance.

## Features

- **12 HTTP Libraries Tested**: requests, httpx, aiohttp, curl_cffi, niquests, pycurl, tls_client, ry, rnet, and CycleTLS
- **Multiple Test Modes**: Synchronous, asynchronous, with/without session reuse
- **Payload Size Variations**: Test with different response sizes (20KB, 50KB, 200KB)
- **Professional Visualizations**: Matplotlib-generated comparison charts
- **Detailed Metrics**: Wall time, CPU time, requests per second
- **Flexible Configuration**: Command-line arguments for all options

## Installation

Install the benchmark dependencies:

```bash
pip install -e '.[benchmark]'
```

Or with poetry:

```bash
poetry install -E benchmark
```

## Quick Start

### Synchronous Benchmarks

Test all synchronous HTTP libraries:

```bash
python benchmarks/bench.py
```

With custom URL and request count:

```bash
python benchmarks/bench.py --url http://example.com --repetitions 10000
```

With different payload sizes:

```bash
python benchmarks/bench.py \
  --url-small http://example.com/20k \
  --url-medium http://example.com/50k \
  --url-large http://example.com/200k \
  --repetitions 10000
```

### Asynchronous Benchmarks

Test all async-capable HTTP libraries:

```bash
python benchmarks/bench_async.py
```

Include synchronous baseline for comparison:

```bash
python benchmarks/bench_async.py --include-sync-baseline
```

### Test Specific Libraries

```bash
python benchmarks/bench.py --libraries cycletls requests httpx
python benchmarks/bench_async.py --libraries cycletls aiohttp httpx
```

## Command-Line Options

### Common Options (both scripts)

```
--url URL                 Base URL to test (default: http://localhost:5001/)
--url-small URL           URL for small payload (~20KB)
--url-medium URL          URL for medium payload (~50KB)
--url-large URL           URL for large payload (~200KB)
--repetitions, -r N       Number of requests per test (default: 10000)
--output, -o FILE         Output CSV filename (default: benchmark_results.csv)
--chart, -c FILE          Output chart filename (default: benchmark_results.jpg)
--cycletls-chart FILE     CycleTLS comparison chart filename
--no-visualization        Skip generating charts
--libraries LIB [LIB...]  Test only specific libraries
```

### Async-Only Options

```
--include-sync-baseline   Include synchronous CycleTLS baseline for comparison
```

## Output Files

### CSV Results

The benchmark generates a CSV file with the following columns:

- `library`: Library name (e.g., "cycletls", "requests", "httpx")
- `version`: Library version
- `session_type`: Test type (sync_session, sync_no_session, async_session, async_no_session)
- `payload_size`: Response size tested (20k, 50k, 200k, or default)
- `requests`: Number of requests made
- `wall_time`: Total wall clock time in seconds
- `cpu_time`: Total CPU time in seconds
- `req_per_sec`: Requests per second (throughput)

### Charts

Two types of charts are generated:

1. **Main Results Chart**: Grouped bar chart showing all libraries across different payload sizes and session types
2. **CycleTLS Comparison Chart**: Focused comparison highlighting CycleTLS performance vs other libraries

## Architecture

### Module Structure

```
benchmarks/
├── __init__.py           # Package initialization
├── core.py              # Test execution logic and utilities
├── chart.py             # Visualization functions
├── bench.py             # Synchronous benchmark orchestrator
├── bench_async.py       # Asynchronous benchmark orchestrator
└── README.md            # This file
```

### Key Components

**`core.py`**
- `PycurlSession`: Session wrapper for pycurl
- `session_get_test()`: Test with session reuse
- `non_session_get_test()`: Test without session reuse
- `async_session_get_test()`: Async test with session reuse
- `async_non_session_get_test()`: Async test without session reuse
- `run_sync_tests()`: Run all synchronous benchmarks
- `run_async_tests()`: Run all asynchronous benchmarks

**`chart.py`**
- `plot_benchmark_multi()`: Generate comprehensive comparison charts
- `plot_comparison_chart()`: Simple metric comparison
- `plot_cycletls_focus()`: CycleTLS-focused visualization

**`bench.py`**
- Main synchronous benchmark orchestrator
- Tests: requests, httpx, niquests, curl_cffi, tls_client, rnet, pycurl, cycletls

**`bench_async.py`**
- Main asynchronous benchmark orchestrator
- Tests: httpx, aiohttp, curl_cffi, rnet, ry, cycletls

## Libraries Tested

### Synchronous Libraries (7)

1. **requests** - The classic HTTP library for Python
2. **httpx** - Modern HTTP client with sync/async support
3. **niquests** - High-performance requests alternative
4. **curl_cffi** - Python bindings to libcurl with cffi
5. **tls_client** - TLS fingerprinting HTTP client
6. **rnet** - Rust-based HTTP client
7. **pycurl** - Python interface to libcurl
8. **cycletls** - Advanced TLS fingerprinting with JA3/JA4 support

### Asynchronous Libraries (5)

1. **httpx** - Modern async HTTP client
2. **aiohttp** - Asynchronous HTTP client/server framework
3. **curl_cffi** - Async-capable curl bindings
4. **rnet** - Rust-based async HTTP client
5. **ry** - Fast async HTTP library
6. **cycletls** - CycleTLS async mode

## Examples

### Example 1: Quick Comparison

Test CycleTLS against popular libraries:

```bash
python benchmarks/bench.py \
  --libraries cycletls requests httpx \
  --url http://example.com \
  --repetitions 1000 \
  --output quick_comparison.csv
```

### Example 2: Comprehensive Async Test

Full async benchmark with all payload sizes:

```bash
python benchmarks/bench_async.py \
  --url-small https://httpbin.org/bytes/20480 \
  --url-medium https://httpbin.org/bytes/51200 \
  --url-large https://httpbin.org/bytes/204800 \
  --repetitions 5000 \
  --output async_full_results.csv \
  --chart async_comparison.jpg
```

### Example 3: CycleTLS Focus

Benchmark CycleTLS with sync baseline:

```bash
python benchmarks/bench_async.py \
  --libraries cycletls \
  --include-sync-baseline \
  --repetitions 10000 \
  --output cycletls_performance.csv
```

## Performance Tips

1. **Request Count**: Use 10,000+ requests for reliable statistics
2. **Warm-up**: Run benchmarks multiple times and average results
3. **Network**: Test against local server for consistent results
4. **Payload Sizes**: Test multiple sizes to see performance across scenarios
5. **Session Reuse**: Compare session vs non-session to measure connection overhead

## Comparison to rnet Benchmarks

This benchmark suite is inspired by and compatible with the [rnet Python benchmarks](https://github.com/0x676e67/rnet/tree/main/python/benchmark), with these differences:

- **Default 10,000 requests** vs rnet's 400 (for better statistical significance)
- **No built-in test server** (test against any URL you provide)
- **No threading tests** (focused on sync/async comparison)
- **CycleTLS integration** as the primary focus library
- **Modular structure** for easy extension and customization

## Troubleshooting

### Import Errors

If you see import errors, ensure all dependencies are installed:

```bash
pip install -e '.[benchmark]'
```

### Missing Libraries

The benchmark will continue with available libraries if some are missing. Install individual libraries as needed:

```bash
pip install requests httpx aiohttp curl-cffi niquests pycurl tls-client ry rnet
```

### Visualization Issues

If chart generation fails, install visualization dependencies:

```bash
pip install matplotlib pandas seaborn
```

### macOS Issues

On macOS, pycurl may require additional setup:

```bash
brew install curl
pip install --no-cache-dir pycurl
```

## Contributing

To add a new library to the benchmarks:

1. Add the library to `pyproject.toml` under `[project.optional-dependencies].benchmark`
2. Add import logic in `bench.py` or `bench_async.py` `import_libraries()` function
3. Create a session wrapper if needed (see `PycurlSession` example)
4. Test with `--libraries your_library`

## License

MIT - Same as CycleTLS main project
