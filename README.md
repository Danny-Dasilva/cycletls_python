# CycleTLS Python

<div align="center">

[![CI](https://github.com/Danny-Dasilva/cycletls_python/actions/workflows/main.yml/badge.svg)](https://github.com/Danny-Dasilva/cycletls_python/actions/workflows/main.yml)
[![PyPI version](https://img.shields.io/pypi/v/cycletls.svg)](https://pypi.org/project/cycletls/)
[![Downloads](https://static.pepy.tech/badge/cycletls/month)](https://pepy.tech/project/cycletls)
[![Python versions](https://img.shields.io/pypi/pyversions/cycletls.svg)](https://pypi.org/project/cycletls/)
[![license](https://img.shields.io/github/license/Danny-Dasilva/CycleTLS.svg)](https://github.com/Danny-Dasilva/CycleTLS/blob/main/LICENSE)

**Python HTTP client that impersonates real browsers - bypass anti-bot detection with TLS/JA3/JA4/HTTP2 fingerprinting**

*Advanced TLS fingerprinting library with JA3, JA4, HTTP/2, HTTP/3, WebSocket, and SSE support.*

*Unlike requests or httpx, CycleTLS can make your requests indistinguishable from real browser traffic.*

</div>

If you have an API change or feature request feel free to open an [Issue](https://github.com/Danny-Dasilva/CycleTLS/issues/new/choose)

## 🚀 Features

- **Async/Await Support** - Full async API with 1.7x performance boost for concurrent requests
- **Advanced TLS Fingerprinting** - JA3, JA4R, and HTTP/2 fingerprinting support
- **HTTP/3 and QUIC** - Modern protocol support with QUIC fingerprinting
- **Pythonic API** - Familiar requests-like interface with context managers
- **Connection Pooling** - Built-in connection reuse for high performance
- **Comprehensive Proxy Support** - HTTP, HTTPS, SOCKS4, SOCKS5, SOCKS5h
- **WebSocket & SSE** - Full bidirectional WebSocket and Server-Sent Events support
- **Binary Data Handling** - Seamless upload and download of binary content
- **Type-Safe** - Pydantic models with full type hints
- **Session Management** - Persistent cookies and headers across requests
- **🆕 Browser Fingerprint Profiles** - Built-in Chrome, Firefox, Safari, Edge profiles with plugin support
- **🆕 Zero-Copy FFI** - 3x faster sync requests with optimized Python-Go communication

## Table of Contents

* [Installation](#installation)
* [Quick Start](#quick-start)
* [Usage](#usage)
  * [Basic Requests](#basic-requests)
  * [Async API](#async-api-asyncawait-support)
  * [TLS Fingerprinting](#tls-fingerprinting)
    * [JA3 Fingerprinting](#ja3-fingerprinting)
    * [JA4R Fingerprinting](#ja4r-fingerprinting-advanced)
    * [HTTP/2 Fingerprinting](#http2-fingerprinting)
  * [HTTP/3 Support](#http3-support)
  * [Proxy Configuration](#proxy-configuration)
  * [Cookie Handling](#cookie-handling)
  * [Binary Data](#binary-data)
  * [WebSocket Client](#websocket-client)
  * [Server-Sent Events (SSE)](#server-sent-events-sse)
  * [Session Management](#session-management)
  * [Advanced Features](#advanced-features)
* [API Reference](#api-reference)
* [Comparison with TypeScript Version](#comparison-with-typescript-version)
* [Examples](#examples)
* [Testing](#testing)
* [License](#license)

## Dependencies

```
python ^3.8
golang ^1.21x (for building from source)
```

## Installation

**With uv (Recommended):**
```bash
uv add cycletls
```

**With pip:**
```bash
pip install cycletls
```

## Quick Start

### Simple API (Zero Boilerplate) - NEW! 🎉

```python
import cycletls

# That's it! Auto-setup, auto-cleanup
response = cycletls.get('https://httpbin.org/get')
print(response.status_code)  # 200
print(response.json())
```

### Configure Once, Use Everywhere

```python
import cycletls

# Set defaults for all requests
cycletls.set_default(
    proxy='socks5://127.0.0.1:9050',
    timeout=10,
    ja3='771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0',
    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
)

# All future requests use these defaults
response1 = cycletls.get('https://httpbin.org/get')
response2 = cycletls.post('https://httpbin.org/post', json_data={'key': 'value'})

# Per-request overrides
response3 = cycletls.get('https://httpbin.org/get', timeout=5)  # Override timeout
```

### Three Usage Patterns

CycleTLS supports three patterns to fit your needs:

```python
# Pattern 1: Simple API (NEW) - Zero boilerplate, like requests
import cycletls
response = cycletls.get('https://example.com')

# Pattern 2: Manual Client - Full control
from cycletls import CycleTLS
with CycleTLS() as client:
    response = client.get('https://example.com')

# Pattern 3: Session - Persistent cookies/headers
from cycletls import Session
with Session() as session:
    session.headers['Authorization'] = 'Bearer token'
    response1 = session.post('/login', json_data={...})
    response2 = session.get('/profile')  # Cookies preserved
```

### With TLS Fingerprinting

```python
import cycletls

# Chrome 83 fingerprint - Simple API
response = cycletls.get(
    'https://ja3er.com/json',
    ja3='771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0',
    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
)
print(f"JA3 Hash: {response.json()['ja3_hash']}")
```

## Usage

### Basic Requests

#### Simple API (Module-Level Functions)

```python
import cycletls

# All HTTP methods available as module-level functions
response = cycletls.get('https://httpbin.org/get')
response = cycletls.post('https://httpbin.org/post', json_data={'key': 'value'})
response = cycletls.put('https://httpbin.org/put', json_data={'status': 'updated'})
response = cycletls.patch('https://httpbin.org/patch', json_data={'field': 'value'})
response = cycletls.delete('https://httpbin.org/delete')
response = cycletls.head('https://httpbin.org/get')
response = cycletls.options('https://httpbin.org/get')

# POST with form data
response = cycletls.post(
    'https://httpbin.org/post',
    data={'username': 'john', 'password': 'secret'}
)
```

#### Manual Client (Context Manager)

```python
from cycletls import CycleTLS

with CycleTLS() as client:
    # GET request
    response = client.get('https://httpbin.org/get')

    # POST with JSON data
    response = client.post(
        'https://httpbin.org/post',
        json_data={'key': 'value'}
    )

    # POST with form data
    response = client.post(
        'https://httpbin.org/post',
        data={'username': 'john', 'password': 'secret'}
    )

    # Other methods
    response = client.put('https://httpbin.org/put', json_data={'status': 'updated'})
    response = client.patch('https://httpbin.org/patch', json_data={'field': 'value'})
    response = client.delete('https://httpbin.org/delete')
    response = client.head('https://httpbin.org/get')
    response = client.options('https://httpbin.org/get')
```

#### Response Properties

```python
from cycletls import CycleTLS

with CycleTLS() as client:
    response = client.get('https://httpbin.org/get')

    # Status information
    print(response.status_code)  # 200
    print(response.ok)  # True (200-399)
    print(response.reason)  # "OK"

    # Content access
    print(response.text)  # Response as string
    print(response.content)  # Response as bytes
    print(response.json())  # Parse JSON

    # Headers (case-insensitive)
    print(response.headers['Content-Type'])
    print(response.headers.get('content-type'))  # Same as above

    # Cookies
    print(response.cookies['session_id'])

    # URL after redirects
    print(response.url)

    # Encoding detection
    print(response.encoding)  # 'utf-8'

    # Error checking
    if response.is_error:
        print(f"Error: {response.status_code}")

    # Raise exception on error
    response.raise_for_status()  # Raises HTTPError if status >= 400
```

### Async API (async/await Support)

CycleTLS now provides full async/await support for concurrent request handling, offering **1.7x performance improvement** for I/O-bound workloads.

#### Simple Async Requests

```python
import asyncio
import cycletls

async def main():
    # Module-level async functions
    response = await cycletls.aget('https://httpbin.org/get')
    print(response.status_code)  # 200

    # POST with JSON
    response = await cycletls.apost(
        'https://httpbin.org/post',
        json_data={'key': 'value'}
    )

    # Other async methods
    await cycletls.aput('https://httpbin.org/put', json_data={...})
    await cycletls.apatch('https://httpbin.org/patch', json_data={...})
    await cycletls.adelete('https://httpbin.org/delete')
    await cycletls.ahead('https://httpbin.org/get')
    await cycletls.aoptions('https://httpbin.org/get')

asyncio.run(main())
```

#### Async Context Manager

```python
import asyncio
from cycletls import AsyncCycleTLS

async def main():
    async with AsyncCycleTLS() as client:
        # Reuse client for multiple requests
        response1 = await client.get('https://httpbin.org/get')
        response2 = await client.post('https://httpbin.org/post', json_data={})
        response3 = await client.put('https://httpbin.org/put', json_data={})

asyncio.run(main())
```

#### Concurrent Requests (The Power of Async!)

```python
import asyncio
import cycletls

async def main():
    # Make 10 requests concurrently - all execute in parallel!
    responses = await asyncio.gather(*[
        cycletls.aget(f'https://httpbin.org/get?id={i}')
        for i in range(10)
    ])

    print(f"Completed {len(responses)} requests")
    print(f"All successful: {all(r.status_code == 200 for r in responses)}")

asyncio.run(main())
```

#### Performance Comparison

```python
import asyncio
import time
import cycletls

async def benchmark():
    urls = [f'https://httpbin.org/delay/1?id={i}' for i in range(5)]

    # Sequential (slow)
    start = time.time()
    for url in urls:
        await cycletls.aget(url)
    sequential_time = time.time() - start

    # Concurrent (fast!)
    start = time.time()
    await asyncio.gather(*[cycletls.aget(url) for url in urls])
    concurrent_time = time.time() - start

    print(f"Sequential: {sequential_time:.2f}s")
    print(f"Concurrent: {concurrent_time:.2f}s")
    print(f"Speedup: {sequential_time / concurrent_time:.2f}x")
    # Output: Speedup: ~5.0x

asyncio.run(benchmark())
```

#### Async with TLS Fingerprinting

```python
import asyncio
import cycletls

async def main():
    # Async works with all CycleTLS features!
    chrome_ja3 = "771,4865-4866-4867-49195-49199-49196-49200..."

    # Single async request with fingerprint
    response = await cycletls.aget(
        'https://ja3er.com/json',
        ja3=chrome_ja3,
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )

    # Concurrent requests with fingerprints
    tasks = [
        cycletls.aget('https://ja3er.com/json', ja3=chrome_ja3),
        cycletls.aget('https://ja3er.com/json', ja3=firefox_ja3),
        cycletls.aget('https://ja3er.com/json', ja3=safari_ja3),
    ]
    responses = await asyncio.gather(*tasks)

asyncio.run(main())
```

#### Async Configuration

Async requests support the same configuration options as sync requests:

```python
async with AsyncCycleTLS() as client:
    response = await client.get(
        'https://httpbin.org/delay/5',
        timeout=10.0,           # Max time to wait for response (seconds)
        poll_interval=0.01,     # Polling interval (seconds), 0.0 = adaptive
        proxy='socks5://127.0.0.1:9050',
        ja3='...',
        user_agent='...',
        headers={'X-Custom': 'Header'},
        cookies={'session': 'abc123'}
    )
```

**Polling Behavior:**
- `poll_interval=0.0` (default): Adaptive polling (tight loop → 100μs → 1ms)
- `poll_interval=0.01`: Fixed 10ms polling interval
- `timeout=30.0` (default): Request timeout in seconds

#### Rate Limiting with Semaphore

```python
import asyncio
import cycletls

async def main():
    # Limit to 5 concurrent requests at a time
    semaphore = asyncio.Semaphore(5)

    async def limited_request(url):
        async with semaphore:
            return await cycletls.aget(url)

    # Launch 100 requests, but only 5 run concurrently
    responses = await asyncio.gather(*[
        limited_request(f'https://httpbin.org/get?id={i}')
        for i in range(100)
    ])

asyncio.run(main())
```

#### Error Handling

```python
import asyncio
import cycletls
from cycletls.exceptions import HTTPError

async def main():
    # Handle HTTP errors
    response = await cycletls.aget('https://httpbin.org/status/404')
    if response.is_error:
        print(f"Error: {response.status_code}")

    # Raise exception on error
    try:
        response.raise_for_status()
    except HTTPError as e:
        print(f"HTTP Error: {e}")

    # Handle timeouts
    try:
        response = await cycletls.aget(
            'https://httpbin.org/delay/10',
            timeout=2.0
        )
    except asyncio.TimeoutError:
        print("Request timed out")

    # Concurrent requests with error handling
    results = await asyncio.gather(
        cycletls.aget('https://httpbin.org/status/200'),
        cycletls.aget('https://httpbin.org/status/404'),
        return_exceptions=True  # Don't stop on first error
    )

    for result in results:
        if isinstance(result, Exception):
            print(f"Error: {result}")
        else:
            print(f"Success: {result.status_code}")

asyncio.run(main())
```

**Available Async Functions:**
- `cycletls.aget()` - Async GET request
- `cycletls.apost()` - Async POST request
- `cycletls.aput()` - Async PUT request
- `cycletls.apatch()` - Async PATCH request
- `cycletls.adelete()` - Async DELETE request
- `cycletls.ahead()` - Async HEAD request
- `cycletls.aoptions()` - Async OPTIONS request
- `cycletls.async_request()` - Generic async request

**Performance Benefits:**
- **1.7x faster** for concurrent I/O-bound workloads
- Efficient CPU usage with adaptive polling
- Non-blocking: thousands of concurrent requests with minimal overhead
- Perfect for web scraping, API aggregation, and bulk data fetching

## Configuration

### Module-Level Defaults

Set default values once and have them apply to all requests:

```python
import cycletls

# Configure defaults once
cycletls.set_default(
    proxy='socks5://127.0.0.1:9050',
    timeout=10,
    ja3='771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0',
    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    enable_connection_reuse=True,
    insecure_skip_verify=False
)

# All subsequent requests use these defaults
response1 = cycletls.get('https://api.example.com/endpoint1')
response2 = cycletls.get('https://api.example.com/endpoint2')

# Override defaults per-request
response3 = cycletls.get('https://api.example.com/endpoint3', timeout=30)
```

**Available Configuration Options:**

| Option | Type | Description |
|--------|------|-------------|
| `ja3` | str | JA3 TLS fingerprint string |
| `ja4r` | str | JA4 raw format fingerprint |
| `http2_fingerprint` | str | HTTP/2 fingerprint |
| `quic_fingerprint` | str | QUIC fingerprint |
| `disable_grease` | bool | Disable GREASE for exact JA4 matching |
| `user_agent` | str | User-Agent header |
| `proxy` | str | Proxy URL (http/https/socks4/socks5) |
| `timeout` | int | Request timeout in seconds |
| `enable_connection_reuse` | bool | Enable connection pooling |
| `insecure_skip_verify` | bool | Skip TLS certificate verification |
| `server_name` | str | Custom SNI (Server Name Indication) |
| `force_http1` | bool | Force HTTP/1.1 protocol |
| `force_http3` | bool | Force HTTP/3 protocol |
| `protocol` | str | Protocol selection (http1/http2/http3) |
| `disable_redirect` | bool | Disable automatic redirects |
| `header_order` | list | Custom header ordering |
| `order_headers_as_provided` | bool | Use provided header order |

### Read Configuration

```python
import cycletls

# Set a default
cycletls.set_default(timeout=10)

# Read configuration value
timeout = cycletls.get_default('timeout')
print(f"Default timeout: {timeout}")  # 10

# Read via module attribute
timeout = cycletls.default_timeout
print(f"Default timeout: {timeout}")  # 10
```

### Reset Configuration

```python
import cycletls

# Configure defaults
cycletls.set_default(proxy='socks5://127.0.0.1:9050', timeout=10)

# Reset all defaults
cycletls.reset_defaults()

# All defaults are now cleared
```

### Manual Session Cleanup

The global session is automatically cleaned up on program exit, but you can manually close it:

```python
import cycletls

response = cycletls.get('https://example.com')

# Manually close the global session (useful in notebooks)
cycletls.close_global_session()

# Next call creates a new session
response = cycletls.get('https://example.com')
```

### TLS Fingerprinting

#### JA3 Fingerprinting

JA3 fingerprinting allows you to mimic specific browser TLS implementations:

**Simple API:**
```python
import cycletls

# Browser fingerprints
BROWSER_FINGERPRINTS = {
    'chrome_83': {
        'ja3': '771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36'
    },
    'firefox_87': {
        'ja3': '771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0',
        'user_agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0'
    },
    'safari_15': {
        'ja3': '771,4865-4867-4866-49196-49195-52393-49200-49199-52392-49162-49161-49172-49171-157-156-53-47-49160-49170-10,0-23-65281-10-11-35-16-5-13-45-28-21,29-23-24-25,0',
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15'
    }
}

# Use Chrome 83 fingerprint
chrome_fp = BROWSER_FINGERPRINTS['chrome_83']
response = cycletls.get(
    'https://ja3er.com/json',
    ja3=chrome_fp['ja3'],
    user_agent=chrome_fp['user_agent']
)

data = response.json()
print(f"JA3 Hash: {data['ja3_hash']}")
print(f"User Agent: {data['User-Agent']}")
```

**Manual Client:**
```python
from cycletls import CycleTLS

with CycleTLS() as client:
    chrome_fp = BROWSER_FINGERPRINTS['chrome_83']
    response = client.get(
        'https://ja3er.com/json',
        ja3=chrome_fp['ja3'],
        user_agent=chrome_fp['user_agent']
    )

    data = response.json()
    print(f"JA3 Hash: {data['ja3_hash']}")
    print(f"User Agent: {data['User-Agent']}")
```

#### JA4R Fingerprinting (Advanced)

> **Important:** Use `ja4r` (raw format) to configure TLS fingerprints. JA4 hashes are for observation only.

JA4R provides explicit control over cipher suites, extensions, and signature algorithms:

```python
from cycletls import CycleTLS

with CycleTLS() as client:
    # Chrome 138 JA4R fingerprint
    response = client.get(
        'https://tls.peet.ws/api/all',
        ja4r='t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0000,0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,44cd,fe0d,ff01_0403,0804,0401,0503,0805,0501,0806,0601',
        disable_grease=False,
        user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
    )

    data = response.json()
    print(f"JA4: {data['tls']['ja4']}")
    print(f"JA4_r: {data['tls']['ja4_r']}")
    print(f"TLS Version: {data['tls']['tls_version_negotiated']}")
```

**JA4R Format Breakdown:**

```
t13d1516h2_<ciphers>_<extensions>_<signature_algorithms>
│││││││││   │        │            │
│││││││││   │        │            └─ Signature algorithms (0x0403, 0x0804, ...)
│││││││││   │        └─ Extensions (0x0000=SNI, 0x000a=supported_groups, ...)
│││││││││   └─ Cipher suites (0x002f=AES128, 0x1301=TLS_AES_128, ...)
││││││││└─ HTTP version (h2=HTTP/2)
│││││││└─ Max fragment length (1516 bytes)
││││││└─ ALPN first value length
│││││└─ Extension count (13 decimal)
││││└─ TLS version (1.3)
│││└─ QUIC support
││└─ TLS version
│└─ Transport (t=TCP, q=QUIC)
└─ Type (t=standard)
```

#### HTTP/2 Fingerprinting

Mimic specific browser HTTP/2 implementations:

```python
from cycletls import CycleTLS

with CycleTLS() as client:
    # Firefox HTTP/2 fingerprint
    response = client.get(
        'https://tls.peet.ws/api/all',
        http2_fingerprint='1:65536;2:0;4:131072;5:16384|12517377|0|m,p,a,s',
        ja3='771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0',
        user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0'
    )

    data = response.json()
    print(f"HTTP/2 Fingerprint: {data['http2']['akamai_fingerprint']}")
    print(f"Settings: {data['http2']['sent_frames'][0]['settings']}")
```

**Common Browser HTTP/2 Fingerprints:**

| Browser | HTTP/2 Fingerprint | Description |
|---------|-------------------|-------------|
| Firefox | `1:65536;2:0;4:131072;5:16384\|12517377\|0\|m,p,a,s` | Smaller window, MPAS priority |
| Chrome | `1:65536;2:0;4:6291456;6:262144\|15663105\|0\|m,a,s,p` | Larger window, MASP priority |

**HTTP/2 Fingerprint Format:**

```
<settings>|<window_update>|<priority>|<pseudo_header_order>
│          │               │          │
│          │               │          └─ Pseudo-header order (m=method, p=path, a=authority, s=scheme)
│          │               └─ Priority (0=no priority frame)
│          └─ Window update value
└─ Settings (1=header_table_size, 2=enable_push, 4=max_concurrent_streams, ...)
```

#### Browser Fingerprint Profiles (NEW!)

Use built-in browser profiles instead of manually configuring JA3/JA4/HTTP2 strings:

```python
import cycletls
from cycletls import CHROME_120, FIREFOX_121, SAFARI_17, FingerprintRegistry

# Use built-in browser profile
response = cycletls.get(
    'https://ja3er.com/json',
    fingerprint=CHROME_120  # Pre-configured Chrome 120 fingerprint
)

# Available built-in profiles
profiles = [
    CHROME_120,      # Chrome 120 on Windows
    CHROME_121,      # Chrome 121 on Windows
    FIREFOX_121,     # Firefox 121 on Linux
    SAFARI_17,       # Safari 17 on macOS
    EDGE_120,        # Edge 120 on Windows
    CHROME_ANDROID,  # Chrome on Android
    SAFARI_IOS,      # Safari on iOS
]

# List all registered profiles
registry = FingerprintRegistry()
for name in registry.all():
    print(f"Available: {name}")
```

**Custom Fingerprint Profiles:**

```python
from cycletls import TLSFingerprint, FingerprintRegistry

# Create custom fingerprint
my_profile = TLSFingerprint(
    name='custom_browser',
    ja3='771,4865-4866-4867-49195...',
    user_agent='Mozilla/5.0...',
    http2_fingerprint='1:65536;2:0;4:131072...',
)

# Register for reuse
registry = FingerprintRegistry()
registry.register(my_profile)

# Use in requests
response = cycletls.get('https://example.com', fingerprint=my_profile)
```

**Load Fingerprints from Files:**

```python
from cycletls import load_fingerprints_from_dir, load_fingerprint_from_file

# Load single profile from JSON/YAML
profile = load_fingerprint_from_file('profiles/chrome_125.json')

# Load all profiles from a directory
load_fingerprints_from_dir('profiles/')  # Auto-registers all found profiles

# Use environment variable for plugin directory
# Set CYCLETLS_FINGERPRINT_DIR=/path/to/profiles
from cycletls import load_fingerprints_from_env
load_fingerprints_from_env()
```

### HTTP/3 Support

```python
from cycletls import CycleTLS

with CycleTLS() as client:
    # Force HTTP/3
    response = client.get(
        'https://cloudflare-quic.com/',
        force_http3=True,
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        insecure_skip_verify=True
    )

    print(f"Response over HTTP/3: {response.status_code}")
```

### Proxy Configuration

CycleTLS supports multiple proxy protocols:

**Simple API (with defaults):**
```python
import cycletls

# Set proxy as default
cycletls.set_default(proxy='socks5://127.0.0.1:9050')

# All requests use the proxy
response = cycletls.get('https://httpbin.org/ip')
print(response.json())
```

**Simple API (per-request):**
```python
import cycletls

# HTTP Proxy with authentication
response = cycletls.get(
    'https://httpbin.org/ip',
    proxy='http://username:password@proxy.example.com:8080'
)

# SOCKS5 Proxy (Tor example)
response = cycletls.get(
    'https://httpbin.org/ip',
    proxy='socks5://127.0.0.1:9050'
)

print(response.json())
```

**Supported Proxy Protocols:**
- `http://` - HTTP proxy
- `https://` - HTTPS proxy
- `socks4://` - SOCKS4 proxy
- `socks5://` - SOCKS5 proxy
- `socks5h://` - SOCKS5 with hostname resolution through proxy

**Manual Client:**
```python
from cycletls import CycleTLS

with CycleTLS() as client:
    # HTTP Proxy with authentication
    response = client.get(
        'https://httpbin.org/ip',
        proxy='http://username:password@proxy.example.com:8080'
    )

    # SOCKS5 Proxy
    response = client.get(
        'https://httpbin.org/ip',
        proxy='socks5://127.0.0.1:9050'
    )

    print(response.json())
```

### Cookie Handling

#### Simple Cookie Dict

**Simple API:**
```python
import cycletls

# Send cookies as dict
response = cycletls.get(
    'https://httpbin.org/cookies',
    cookies={'session_id': 'abc123', 'user_token': 'xyz789'}
)

print(response.json())
```

**Manual Client:**
```python
from cycletls import CycleTLS

with CycleTLS() as client:
    response = client.get(
        'https://httpbin.org/cookies',
        cookies={'session_id': 'abc123', 'user_token': 'xyz789'}
    )

    print(response.json())
```

#### Advanced Cookie Objects

```python
from cycletls import CycleTLS, Cookie

with CycleTLS() as client:
    # Create Cookie objects with full attributes
    cookies = [
        Cookie(
            name='session_id',
            value='abc123',
            domain='httpbin.org',
            path='/',
            secure=True,
            http_only=True,
            same_site='Lax'
        ),
        Cookie(
            name='preferences',
            value='dark_mode',
            max_age=3600
        )
    ]

    response = client.get('https://httpbin.org/cookies', cookies=cookies)
    print(response.json())
```

#### Response Cookies

```python
from cycletls import CycleTLS

with CycleTLS() as client:
    # Server sets cookies
    response = client.get('https://httpbin.org/cookies/set?name=value')

    # Access response cookies
    print(response.cookies['name'])  # 'value'

    # CookieJar interface
    for name in response.cookies:
        print(f"{name}: {response.cookies[name]}")
```

### Binary Data

#### Download Binary Data

**Simple API:**
```python
import cycletls

# Download image
response = cycletls.get('https://httpbin.org/image/jpeg')

# Access binary content
image_data = response.content  # bytes

# Save to file
with open('image.jpg', 'wb') as f:
    f.write(image_data)

print(f"Downloaded {len(image_data)} bytes")
```

**Manual Client:**
```python
from cycletls import CycleTLS

with CycleTLS() as client:
    response = client.get('https://httpbin.org/image/jpeg')

    with open('image.jpg', 'wb') as f:
        f.write(response.content)

    print(f"Downloaded {len(response.content)} bytes")
```

#### Upload Binary Data

**Simple API:**
```python
import cycletls

# Read binary data
with open('image.jpg', 'rb') as f:
    binary_data = f.read()

# Upload binary data
response = cycletls.post(
    'https://httpbin.org/post',
    data=binary_data,
    headers={'Content-Type': 'image/jpeg'}
)

print(response.json())
```

**Manual Client:**
```python
from cycletls import CycleTLS

with CycleTLS() as client:
    with open('image.jpg', 'rb') as f:
        binary_data = f.read()

    # Upload using body_bytes
    response = client.post(
        'https://httpbin.org/post',
        body_bytes=binary_data,
        headers={'Content-Type': 'application/octet-stream'}
    )

    print(response.status_code)
```

#### Supported Media Types

The following content types are automatically handled as binary data:

- **Images**: `image/jpeg`, `image/png`, `image/gif`, `image/webp`, `image/svg+xml`
- **Videos**: `video/mp4`, `video/webm`, `video/avi`, `video/quicktime`
- **Documents**: `application/pdf`

### WebSocket Client

Full bidirectional WebSocket support with TLS fingerprinting.

```python
from cycletls import WebSocketConnection

# Basic WebSocket connection
with WebSocketConnection('wss://echo.websocket.org') as ws:
    # Send text message
    ws.send('Hello, WebSocket!')

    # Receive message
    message = ws.receive()
    print(f"Received: {message.data}")
    print(f"Message type: {message.type}")  # MessageType.TEXT or MessageType.BINARY

# WebSocket with TLS fingerprinting
with WebSocketConnection(
    'wss://example.com/socket',
    ja3='771,4865-4867-4866-49195-49199...',
    user_agent='Mozilla/5.0...',
    headers={'Authorization': 'Bearer token'},
    proxy='socks5://127.0.0.1:9050'
) as ws:
    # Send and receive messages
    ws.send('{"action": "subscribe", "channel": "updates"}')

    # Iterate over messages
    for message in ws:
        if message.is_close:
            break
        print(f"Event: {message.data}")
```

**WebSocket Features:**
- ✅ Full bidirectional messaging (text and binary)
- ✅ TLS fingerprinting (JA3, JA4R)
- ✅ Custom headers and proxy support
- ✅ Context manager for automatic cleanup
- ✅ Message type detection (TEXT, BINARY, CLOSE, PING, PONG)

### Server-Sent Events (SSE)

Full SSE streaming support with TLS fingerprinting.

```python
from cycletls import SSEConnection

# Basic SSE connection
with SSEConnection('https://example.com/events') as sse:
    # Iterate over events
    for event in sse:
        print(f"Event type: {event.event}")  # 'message', 'update', etc.
        print(f"Data: {event.data}")
        print(f"ID: {event.id}")

# SSE with TLS fingerprinting and resume support
with SSEConnection(
    'https://api.example.com/stream',
    ja3='771,4865-4867-4866-49195-49199...',
    user_agent='Mozilla/5.0...',
    headers={'Authorization': 'Bearer token'},
    last_event_id='event-99',  # Resume from last known event
    proxy='socks5://127.0.0.1:9050'
) as sse:
    for event in sse:
        if event.retry:
            print(f"Server requested retry interval: {event.retry}ms")
        process_event(event.data)
```

**SSE Features:**
- ✅ Full event streaming with automatic parsing
- ✅ TLS fingerprinting (JA3, JA4R)
- ✅ Last-Event-ID for resumption
- ✅ Custom retry interval handling
- ✅ Context manager for automatic cleanup
- ✅ Event type, ID, and data extraction

### Session Management

Use `Session` for persistent cookies and headers across requests:

```python
from cycletls import Session

# Create session
with Session() as session:
    # Set persistent headers
    session.headers['Authorization'] = 'Bearer token123'
    session.headers['User-Agent'] = 'CustomBot/1.0'

    # Login - cookies are automatically saved
    login_response = session.post(
        'https://httpbin.org/cookies/set?session=abc123',
        json_data={'username': 'admin', 'password': 'secret'}
    )

    # Subsequent requests include cookies and headers automatically
    profile_response = session.get('https://httpbin.org/cookies')
    print(profile_response.json())
    # {'cookies': {'session': 'abc123'}}

    # Add more cookies to session
    session.cookies.set('preferences', 'dark_mode')

    # All future requests will include both cookies
    settings_response = session.get('https://httpbin.org/cookies')
    print(settings_response.json())
    # {'cookies': {'session': 'abc123', 'preferences': 'dark_mode'}}
```

**Session Features:**
- Persistent cookies across requests
- Persistent headers across requests
- Automatic cookie updates from responses
- Request-specific cookies/headers override session values
- Context manager support for automatic cleanup

### Advanced Features

#### Connection Reuse

**Simple API (with defaults):**
```python
import cycletls

# Enable connection reuse for all requests
cycletls.set_default(enable_connection_reuse=True)

# First request establishes connection
response1 = cycletls.get('https://httpbin.org/get')

# Second request reuses connection (faster)
response2 = cycletls.get('https://httpbin.org/headers')
```

**Manual Client:**
```python
from cycletls import CycleTLS

with CycleTLS() as client:
    # Enable connection reuse for better performance
    response1 = client.get(
        'https://httpbin.org/get',
        enable_connection_reuse=True
    )

    # Second request reuses connection (faster)
    response2 = client.get(
        'https://httpbin.org/headers',
        enable_connection_reuse=True
    )
```

#### Custom SNI (Domain Fronting)

```python
from cycletls import CycleTLS

with CycleTLS() as client:
    # Set SNI different from Host header
    response = client.get(
        'https://127.0.0.1:8443',
        server_name='front.example',  # TLS SNI
        headers={'Host': 'real.example'},  # HTTP Host header
        insecure_skip_verify=True
    )
```

#### Timeout Configuration

```python
from cycletls import CycleTLS

with CycleTLS() as client:
    try:
        # Set timeout (seconds)
        response = client.get(
            'https://httpbin.org/delay/10',
            timeout=5
        )
    except Exception as e:
        print(f"Request timed out: {e}")
```

#### Redirect Handling

```python
from cycletls import CycleTLS

with CycleTLS() as client:
    # Disable automatic redirects
    response = client.get(
        'https://httpbin.org/redirect/3',
        disable_redirect=True
    )

    print(response.status_code)  # 302
    print(response.headers['Location'])
```

#### Error Handling

**Simple API:**
```python
import cycletls
from cycletls import HTTPError, ConnectionError, Timeout

try:
    response = cycletls.get('https://httpbin.org/status/404')
    response.raise_for_status()  # Raises HTTPError
except HTTPError as e:
    print(f"HTTP Error: {e}")
    print(f"Status Code: {e.response.status_code}")
    print(f"Response Body: {e.response.text}")
except ConnectionError as e:
    print(f"Connection Error: {e}")
except Timeout as e:
    print(f"Timeout: {e}")
```

**Manual Client:**
```python
from cycletls import CycleTLS, HTTPError, ConnectionError, Timeout

with CycleTLS() as client:
    try:
        response = client.get('https://httpbin.org/status/404')
        response.raise_for_status()  # Raises HTTPError
    except HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Status Code: {e.response.status_code}")
        print(f"Response Body: {e.response.text}")
    except ConnectionError as e:
        print(f"Connection Error: {e}")
    except Timeout as e:
        print(f"Timeout: {e}")
```

#### Custom Header Ordering

```python
from cycletls import CycleTLS

with CycleTLS() as client:
    response = client.get(
        'https://httpbin.org/headers',
        headers={
            'Accept': 'application/json',
            'User-Agent': 'CustomBot/1.0',
            'Accept-Language': 'en-US'
        },
        header_order=['accept', 'user-agent', 'accept-language'],
        order_headers_as_provided=True
    )
```

### Debugging and Logging

CycleTLS includes comprehensive Python logging support for debugging requests, responses, and FFI operations.

#### Enable Debug Logging

```python
import logging
import cycletls

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Make a request - see detailed logs
response = cycletls.get('https://httpbin.org/get')
```

**Log Output:**
```
DEBUG:cycletls.api:Sending GET request to https://httpbin.org/get
DEBUG:cycletls.api:Request headers: {...}
DEBUG:cycletls._ffi:Calling Go shared library getRequest()
DEBUG:cycletls._ffi:Received response from Go (size: 1234 bytes)
DEBUG:cycletls.api:Received response: 200 OK
DEBUG:cycletls.api:Response headers: {...}
```

#### Log Levels

- **DEBUG**: Detailed request/response info, headers, FFI calls, response sizes
- **INFO**: Library loading events
- **ERROR**: Request failures, parsing errors

#### Selective Logging

```python
import logging

# Only log errors
logging.basicConfig(level=logging.ERROR)

# Or configure specific loggers
logging.getLogger('cycletls.api').setLevel(logging.DEBUG)
logging.getLogger('cycletls._ffi').setLevel(logging.INFO)
```

#### Logging with Proxies

```python
import logging
import cycletls

logging.basicConfig(level=logging.DEBUG)

# Proxy usage is logged automatically
response = cycletls.get(
    'https://httpbin.org/ip',
    proxy='socks5://127.0.0.1:9050'
)
# Log: "Using proxy: socks5://127.0.0.1:9050"
```

## API Reference

### Module-Level Functions (Simple API)

The Simple API provides convenient module-level functions that use a shared global client.

#### Synchronous Functions

```python
import cycletls

# Make requests directly
response = cycletls.get(url, **kwargs)
response = cycletls.post(url, data=None, json_data=None, **kwargs)
response = cycletls.put(url, data=None, json_data=None, **kwargs)
response = cycletls.patch(url, data=None, json_data=None, **kwargs)
response = cycletls.delete(url, **kwargs)
response = cycletls.head(url, **kwargs)
response = cycletls.options(url, **kwargs)
response = cycletls.request(method, url, **kwargs)
```

#### Async Functions

```python
import asyncio
import cycletls

async def main():
    # Async module-level functions
    response = await cycletls.aget(url, **kwargs)
    response = await cycletls.apost(url, data=None, json_data=None, **kwargs)
    response = await cycletls.aput(url, data=None, json_data=None, **kwargs)
    response = await cycletls.apatch(url, data=None, json_data=None, **kwargs)
    response = await cycletls.adelete(url, **kwargs)
    response = await cycletls.ahead(url, **kwargs)
    response = await cycletls.aoptions(url, **kwargs)
    response = await cycletls.async_request(method, url, **kwargs)

asyncio.run(main())
```

**Async-Specific Parameters:**
- `timeout` (float): Maximum time to wait for request completion (default: 30.0 seconds)
- `poll_interval` (float): Polling interval for checking completion (default: 0.0 = adaptive)
  - `0.0`: Adaptive polling (tight loop → 100μs → 1ms based on checks)
  - `> 0.0`: Fixed polling interval in seconds

**Configuration Functions:**

```python
# Set default values
cycletls.set_default(
    proxy='socks5://127.0.0.1:9050',
    timeout=10,
    ja3='771,4865-4866...',
    # ... any other request parameter
)

# Get a default value
value = cycletls.get_default('timeout')  # Returns 10 or None

# Read via module attribute
timeout = cycletls.default_timeout  # Same as get_default('timeout')

# Reset all defaults
cycletls.reset_defaults()

# Manually close global session (useful in notebooks)
cycletls.close_global_session()
```

**Features:**
- Zero boilerplate - import and use immediately
- Automatic resource management (no context managers needed)
- Configurable defaults that persist across requests
- Thread-safe for concurrent requests
- Automatic cleanup on program exit
- Fork-safe (creates new session in child processes)

### CycleTLS Class

```python
class CycleTLS:
    def __init__(self):
        """Initialize CycleTLS client."""

    def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        data: Optional[Any] = None,
        json_data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        **kwargs
    ) -> Response:
        """Send an HTTP request."""

    def get(self, url: str, params: Optional[Dict] = None, **kwargs) -> Response:
        """Send a GET request."""

    def post(
        self,
        url: str,
        params: Optional[Dict] = None,
        data: Optional[Any] = None,
        json_data: Optional[Dict] = None,
        **kwargs
    ) -> Response:
        """Send a POST request."""

    def put(self, url: str, data: Optional[Any] = None, json_data: Optional[Dict] = None, **kwargs) -> Response:
        """Send a PUT request."""

    def patch(self, url: str, data: Optional[Any] = None, json_data: Optional[Dict] = None, **kwargs) -> Response:
        """Send a PATCH request."""

    def delete(self, url: str, **kwargs) -> Response:
        """Send a DELETE request."""

    def head(self, url: str, **kwargs) -> Response:
        """Send a HEAD request."""

    def options(self, url: str, **kwargs) -> Response:
        """Send an OPTIONS request."""

    def close(self):
        """Close the client and cleanup resources."""

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
```

### AsyncCycleTLS Class

```python
class AsyncCycleTLS:
    def __init__(self):
        """Initialize async CycleTLS client."""

    async def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        data: Optional[Any] = None,
        json_data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        poll_interval: float = 0.0,
        timeout: float = 30.0,
        **kwargs
    ) -> Response:
        """Send an async HTTP request."""

    async def get(self, url: str, params: Optional[Dict] = None, **kwargs) -> Response:
        """Send an async GET request."""

    async def post(
        self,
        url: str,
        params: Optional[Dict] = None,
        data: Optional[Any] = None,
        json_data: Optional[Dict] = None,
        **kwargs
    ) -> Response:
        """Send an async POST request."""

    async def put(self, url: str, data: Optional[Any] = None, json_data: Optional[Dict] = None, **kwargs) -> Response:
        """Send an async PUT request."""

    async def patch(self, url: str, data: Optional[Any] = None, json_data: Optional[Dict] = None, **kwargs) -> Response:
        """Send an async PATCH request."""

    async def delete(self, url: str, **kwargs) -> Response:
        """Send an async DELETE request."""

    async def head(self, url: str, **kwargs) -> Response:
        """Send an async HEAD request."""

    async def options(self, url: str, **kwargs) -> Response:
        """Send an async OPTIONS request."""

    async def close(self):
        """Close the async client and cleanup resources."""

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
```

**Usage:**

```python
import asyncio
from cycletls import AsyncCycleTLS

async def main():
    # Async context manager (recommended)
    async with AsyncCycleTLS() as client:
        response = await client.get('https://httpbin.org/get')

    # Manual lifecycle
    client = AsyncCycleTLS()
    response = await client.get('https://httpbin.org/get')
    await client.close()

asyncio.run(main())
```

### Request Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | Target URL (required) |
| `method` | `str` | HTTP method: GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS |
| `params` | `dict` | Query parameters to append to URL |
| `data` | `dict/str/bytes` | Request body (form data or raw) |
| `json_data` | `dict` | JSON request body (auto-serialized) |
| `files` | `dict` | File uploads (not yet implemented) |
| `headers` | `dict` | Custom HTTP headers |
| `cookies` | `dict/list/CookieJar` | Cookies to send with request |
| **TLS Fingerprinting** | | |
| `ja3` | `str` | JA3 fingerprint string |
| `ja4r` | `str` | JA4R raw format fingerprint |
| `http2_fingerprint` | `str` | HTTP/2 fingerprint string |
| `quic_fingerprint` | `str` | QUIC fingerprint string |
| `disable_grease` | `bool` | Disable GREASE for exact JA4 matching |
| **TLS Configuration** | | |
| `server_name` | `str` | Custom SNI (Server Name Indication) |
| `insecure_skip_verify` | `bool` | Skip TLS certificate verification |
| `tls13_auto_retry` | `bool` | Auto-retry with TLS 1.3 compatible curves |
| **Protocol Options** | | |
| `force_http1` | `bool` | Force HTTP/1.1 protocol |
| `force_http3` | `bool` | Force HTTP/3 protocol |
| `protocol` | `Protocol` | Explicit protocol: http1, http2, http3, websocket, sse |
| **Connection Options** | | |
| `user_agent` | `str` | User Agent string |
| `proxy` | `str` | Proxy URL (http://, socks4://, socks5://, socks5h://) |
| `timeout` | `int` | Request timeout in seconds (default: 6) |
| `disable_redirect` | `bool` | Disable automatic redirects |
| `enable_connection_reuse` | `bool` | Enable connection pooling |
| **Header Options** | | |
| `header_order` | `list[str]` | Custom header ordering |
| `order_headers_as_provided` | `bool` | Use provided header order |

### Response Object

```python
class Response:
    # Properties
    status_code: int        # HTTP status code
    ok: bool               # True if 200 <= status < 400
    is_redirect: bool      # True if 300 <= status < 400
    is_error: bool         # True if status >= 400
    is_client_error: bool  # True if 400 <= status < 500
    is_server_error: bool  # True if 500 <= status < 600
    reason: str            # HTTP reason phrase ("OK", "Not Found", etc.)
    url: str              # Final URL after redirects
    encoding: str         # Character encoding (detected from headers)

    text: str             # Response body as string
    content: bytes        # Response body as bytes
    headers: CaseInsensitiveDict  # Response headers
    cookies: CookieJar    # Response cookies

    # Methods
    def json(self) -> dict:
        """Parse response body as JSON."""

    def raise_for_status(self) -> None:
        """Raise HTTPError if status indicates error (>= 400)."""
```

### Session Class

```python
class Session(CycleTLS):
    cookies: CookieJar              # Persistent cookie jar
    headers: CaseInsensitiveDict    # Persistent headers

    def __init__(self):
        """Initialize a Session with persistent cookies/headers."""
```

### Cookie Class

```python
class Cookie:
    name: str
    value: str
    path: Optional[str] = None
    domain: Optional[str] = None
    expires: Optional[datetime] = None
    max_age: Optional[int] = None
    secure: bool = False
    http_only: bool = False
    same_site: Optional[str] = None  # "Strict", "Lax", or "None"
```

### Exception Hierarchy

```python
CycleTLSError                # Base exception
└── RequestException         # Base for request errors
    ├── HTTPError           # HTTP error (4xx, 5xx)
    ├── ConnectionError     # Connection failed
    ├── Timeout            # Request timeout
    │   ├── ConnectTimeout  # Connection timeout
    │   └── ReadTimeout     # Read timeout
    ├── TooManyRedirects   # Exceeded redirect limit
    ├── InvalidURL         # Malformed URL
    ├── TLSError           # TLS handshake error
    ├── ProxyError         # Proxy connection error
    └── InvalidHeader      # Invalid header value
```

## Comparison with TypeScript Version

### API Differences

| Feature | TypeScript | Python |
|---------|-----------|--------|
| **Initialization** | `const client = await initCycleTLS()` | `client = CycleTLS()` |
| **Context Manager** | Manual `.exit()` | `with CycleTLS() as client:` |
| **Response Parsing** | `await response.json()` | `response.json()` (sync) |
| **Binary Data** | `responseType: 'stream'` | `response.content` (bytes) |
| **Cookies** | Dict or Cookie array | Dict or Cookie objects |
| **Parameter Naming** | camelCase (`userAgent`) | snake_case (`user_agent`) |
| **Error Handling** | Promise rejection | Python exceptions |
| **Sessions** | Not built-in | `Session()` class |

### Python Advantages

✅ **Simple API** - Zero boilerplate module-level functions (`cycletls.get(url)`)
✅ **Pythonic API** - Context managers, properties, snake_case naming
✅ **Synchronous by default** - Simpler for most use cases
✅ **Type hints** - Full Pydantic model validation
✅ **requests-like interface** - Familiar to Python developers
✅ **Session support** - Built-in persistent cookies/headers
✅ **Case-insensitive headers** - Automatic via `CaseInsensitiveDict`
✅ **Rich exceptions** - Specific exception types for different errors
✅ **Configurable defaults** - Set once, use everywhere

### Migration Example

**TypeScript:**
```javascript
const initCycleTLS = require('cycletls');

(async () => {
  const cycleTLS = await initCycleTLS();

  const response = await cycleTLS('https://httpbin.org/post', {
    body: JSON.stringify({key: 'value'}),
    headers: {'Content-Type': 'application/json'},
    ja3: '771,4865-4866...',
    userAgent: 'Mozilla/5.0...'
  }, 'POST');

  const data = await response.json();
  console.log(data);

  await cycleTLS.exit();
})();
```

**Python (Simple API - Recommended):**
```python
import cycletls

response = cycletls.post(
    'https://httpbin.org/post',
    json_data={'key': 'value'},
    ja3='771,4865-4866...',
    user_agent='Mozilla/5.0...'
)

data = response.json()
print(data)
```

**Python (Manual Client):**
```python
from cycletls import CycleTLS

with CycleTLS() as client:
    response = client.post(
        'https://httpbin.org/post',
        json_data={'key': 'value'},
        ja3='771,4865-4866...',
        user_agent='Mozilla/5.0...'
    )

    data = response.json()
    print(data)
```

## Examples

Comprehensive examples can be found in the [examples/](examples/) directory:

**Async Examples:**
- `async_basic.py` - Basic async/await usage with all HTTP methods
- `async_concurrent.py` - Concurrent requests, performance comparison, rate limiting
- `async_with_fingerprinting.py` - Async with JA3/JA4R fingerprinting

**Sync Examples:**
- `basic_request.py` - Simple GET/POST requests
- `ja3_fingerprint.py` - JA3 fingerprinting with multiple browsers
- `ja4_fingerprint.py` - JA4R advanced fingerprinting
- `http2_fingerprint.py` - HTTP/2 custom settings
- `http3_request.py` - HTTP/3 and QUIC usage
- `proxy_usage.py` - All proxy types with authentication
- `connection_pooling.py` - Connection reuse examples
- `websocket_client.py` - WebSocket communication
- `sse_client.py` - Server-Sent Events handling
- `binary_upload.py` - Binary data upload/download
- `form_submission.py` - Form data handling
- `advanced_tls.py` - Advanced TLS configuration
- `all_features.py` - Comprehensive feature showcase

## Testing

**With uv:**
```bash
# Run all tests
uv run pytest tests/

# Run specific test categories
uv run pytest tests/test_ja3_fingerprints.py
uv run pytest tests/test_http2.py
uv run pytest tests/test_cookies.py

# Run with verbose output
uv run pytest -v tests/

# Run with coverage
uv run pytest --cov=cycletls tests/
```

**Without uv:**
```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/test_ja3_fingerprints.py
pytest tests/test_http2.py
pytest tests/test_cookies.py

# Run with verbose output
pytest -v tests/

# Run with coverage
pytest --cov=cycletls tests/
```

## Development Setup

If you want to build from source:

**With uv (Recommended):**
```bash
# Clone repository
git clone https://github.com/Danny-Dasilva/cycletls_python.git
cd cycletls_python

# Install dependencies
uv sync                    # Install base dependencies
uv sync --all-extras       # Install with dev/docs/benchmark dependencies

# Build Go binaries
cd golang
./build.sh

# Run tests
uv run pytest tests/

# Run benchmarks
uv run python benchmarks/benchmark_python.py
```

**Without uv:**
```bash
# Clone repository
git clone https://github.com/Danny-Dasilva/cycletls_python.git
cd cycletls_python

# Install dependencies
pip install -e ".[dev]"

# Build Go binaries
cd golang
./build.sh

# Run tests
pytest tests/
```

### Building for Multiple Platforms

The `build.sh` script builds binaries for:
- Linux (AMD64, ARM64)
- macOS (AMD64, ARM64/Apple Silicon)
- Windows (AMD64)

```bash
cd golang
./build.sh
```

## Questions

<details>
<summary>How do I use different JA3 fingerprints?</summary>

```python
from cycletls import CycleTLS

FINGERPRINTS = {
    'chrome_120': '771,4865-4866-4867...',
    'firefox_115': '771,4865-4867-4866...',
    'safari_17': '771,4865-4867-4866...'
}

with CycleTLS() as client:
    response = client.get(
        'https://ja3er.com/json',
        ja3=FINGERPRINTS['chrome_120']
    )
```
</details>

<details>
<summary>How do I handle cookies across requests?</summary>

Use the `Session` class for automatic cookie persistence:

```python
from cycletls import Session

with Session() as session:
    # Login
    session.post('https://example.com/login',
                 json_data={'user': 'admin', 'pass': 'secret'})

    # Cookies automatically included in subsequent requests
    profile = session.get('https://example.com/profile')
```
</details>

<details>
<summary>How do I download images and files?</summary>

```python
from cycletls import CycleTLS

with CycleTLS() as client:
    response = client.get('https://httpbin.org/image/jpeg')

    # Save binary content
    with open('image.jpg', 'wb') as f:
        f.write(response.content)
```
</details>

<details>
<summary>How do I use SOCKS5 proxy with Tor?</summary>

```python
from cycletls import CycleTLS

with CycleTLS() as client:
    response = client.get(
        'https://check.torproject.org',
        proxy='socks5://127.0.0.1:9050'
    )
    print(response.text)
```
</details>

<details>
<summary>How do I combine JA3, JA4R, and HTTP/2 fingerprints?</summary>

```python
from cycletls import CycleTLS

with CycleTLS() as client:
    response = client.get(
        'https://tls.peet.ws/api/all',
        ja3='771,4865-4866-4867...',
        ja4r='t13d1516h2_002f,0035...',
        http2_fingerprint='1:65536;2:0;4:131072...',
        user_agent='Mozilla/5.0 ...'
    )
```
</details>

## License

### GPL3 LICENSE SYNOPSIS

**_TL;DR_** Here's what the GPL3 license entails:

```markdown
1. Anyone can copy, modify and distribute this software.
2. You have to include the license and copyright notice with each and every distribution.
3. You can use this software privately.
4. You can use this software for commercial purposes.
5. Source code MUST be made available when the software is distributed.
6. Any modifications of this code base MUST be distributed with the same license, GPLv3.
7. This software is provided without warranty.
8. The software author or license can not be held liable for any damages inflicted by the software.
```

More information about the [LICENSE can be found here](http://choosealicense.com/licenses/gpl-3.0/)

## Acknowledgments

- Based on [CycleTLS](https://github.com/Danny-Dasilva/CycleTLS) by Danny Dasilva
- Powered by [uTLS](https://github.com/refraction-networking/utls) for TLS fingerprinting
- Built with [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation
