# API Reference

## Module-Level Functions

The simplest way to use CycleTLS. These functions manage a global session
automatically -- no setup or teardown required.

### Making Requests

```python
import cycletls

response = cycletls.get("https://example.com")
response = cycletls.post("https://example.com", json={"key": "value"})
response = cycletls.put("https://example.com", json={"key": "value"})
response = cycletls.patch("https://example.com", json={"field": "new"})
response = cycletls.delete("https://example.com")
response = cycletls.head("https://example.com")
response = cycletls.options("https://example.com")

# Generic method
response = cycletls.request("GET", "https://example.com")
```

### Async Variants

Every sync function has an `a`-prefixed async counterpart:

```python
import asyncio
import cycletls

async def main():
    response = await cycletls.aget("https://example.com")
    response = await cycletls.apost("https://example.com", json={"key": "value"})
    response = await cycletls.aput("https://example.com", json={"key": "value"})
    response = await cycletls.apatch("https://example.com", json={"field": "new"})
    response = await cycletls.adelete("https://example.com")
    response = await cycletls.ahead("https://example.com")
    response = await cycletls.aoptions("https://example.com")

asyncio.run(main())
```

### Configuration

```python
import cycletls

# Set defaults that apply to all subsequent requests
cycletls.set_default(
    proxy="socks5://127.0.0.1:9050",
    timeout=10,
    ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
)

# Read a default back
timeout = cycletls.get_default("timeout")  # 10

# Reset all defaults
cycletls.reset_defaults()

# Manually close the global session (useful in notebooks)
cycletls.close_global_session()
```

## Request Parameters

All request methods (`get`, `post`, etc.) accept these keyword arguments:

| Parameter | Type | Description |
|---|---|---|
| `headers` | `dict` | HTTP headers to send |
| `cookies` | `dict` or `CookieJar` | Cookies to include |
| `params` | `dict` | Query parameters appended to the URL |
| `data` | `dict`, `str`, or `bytes` | Form-encoded or raw body |
| `json` | `dict` | JSON body (alias for `json_data`) |
| `json_data` | `dict` | JSON body (auto-serialized, sets Content-Type) |
| `files` | `dict` | File uploads as multipart/form-data |
| `auth` | `(user, password)` | HTTP Basic authentication tuple |
| `proxy` | `str` | Proxy URL (`http://`, `socks5://`, etc.) |
| `timeout` | `int` | Request timeout in seconds |
| `ja3` | `str` | JA3 TLS fingerprint string |
| `ja4r` | `str` | JA4R fingerprint (raw format) |
| `http2_fingerprint` | `str` | HTTP/2 fingerprint string |
| `quic_fingerprint` | `str` | QUIC fingerprint string |
| `fingerprint` | `str` or `TLSFingerprint` | Named browser profile |
| `user_agent` | `str` | User-Agent header |
| `disable_grease` | `bool` | Disable GREASE extensions |
| `force_http1` | `bool` | Force HTTP/1.1 |
| `force_http3` | `bool` | Force HTTP/3 |
| `insecure_skip_verify` | `bool` | Skip TLS certificate verification |
| `disable_redirect` | `bool` | Disable automatic redirects |
| `header_order` | `list[str]` | Custom header ordering |
| `order_headers_as_provided` | `bool` | Preserve header insertion order |
| `enable_connection_reuse` | `bool` | Enable connection pooling |
| `server_name` | `str` | Custom SNI (Server Name Indication) |

## Response Object

Every request returns a `Response` object:

```python
response = cycletls.get("https://httpbin.org/get")

# Status
response.status_code   # 200
response.ok            # True (status 200-399)
response.is_error      # False
response.reason        # "OK"

# Body
response.text          # Response body as str
response.content       # Response body as bytes
response.json()        # Parse body as JSON

# Headers (case-insensitive)
response.headers["Content-Type"]
response.headers.get("content-type")  # same key, case-insensitive

# Cookies
response.cookies["session_id"]

# URL after redirects
response.url

# Encoding
response.encoding      # "utf-8"

# Raise on error status
response.raise_for_status()  # raises HTTPError if status >= 400
```

## CycleTLS Client

For explicit client lifetime management:

```python
from cycletls import CycleTLS

# Context manager (recommended)
with CycleTLS() as client:
    response = client.get("https://example.com")
    response = client.post("https://example.com", json={"key": "value"})

# Async context manager
async with CycleTLS() as client:
    response = await client.arequest("GET", "https://example.com")
    await client.aclose()
```

### Methods

| Method | Description |
|---|---|
| `request(method, url, **kwargs)` | Send a request with an explicit HTTP method |
| `get(url, **kwargs)` | GET request |
| `post(url, data=, json=, json_data=, **kwargs)` | POST request |
| `put(url, data=, json=, json_data=, **kwargs)` | PUT request |
| `patch(url, data=, json=, json_data=, **kwargs)` | PATCH request |
| `delete(url, **kwargs)` | DELETE request |
| `head(url, **kwargs)` | HEAD request |
| `options(url, **kwargs)` | OPTIONS request |
| `arequest(method, url, **kwargs)` | Async request |
| `close()` | Close the client |
| `aclose()` | Async close (httpx-compatible) |

## Session

`Session` extends `CycleTLS` with persistent cookies, headers, base URL, and
authentication:

```python
from cycletls import Session

with Session(base_url="https://api.example.com", auth=("user", "pass")) as s:
    # Persistent headers
    s.headers["X-Custom"] = "value"

    # Login -- response cookies are saved automatically
    s.post("/login", json={"user": "admin"})

    # Subsequent requests include saved cookies and headers
    profile = s.get("/profile")

    # Per-request auth overrides session auth
    admin = s.get("/admin", auth=("admin", "admin_pass"))
```

### Constructor

```python
Session(base_url=None, auth=None)
```

| Parameter | Type | Description |
|---|---|---|
| `base_url` | `str` or `None` | Prepended to relative URLs (e.g. `"/path"` becomes `"https://api.example.com/path"`) |
| `auth` | `(user, password)` or `None` | Default HTTP Basic auth for all requests |

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `cookies` | `CookieJar` | Persistent cookie jar |
| `headers` | `CaseInsensitiveDict` | Persistent headers sent with every request |
| `base_url` | `str` or `None` | Base URL for relative paths |
| `auth` | `(str, str)` or `None` | Default Basic auth credentials |

### Async Session

`Session` also supports async methods:

```python
import asyncio
from cycletls import Session

async def main():
    async with Session(base_url="https://api.example.com") as s:
        response = await s.arequest("GET", "/users")
        # Cookies from async responses are persisted too

asyncio.run(main())
```

## AsyncCycleTLS

A dedicated async client class:

```python
import asyncio
from cycletls import AsyncCycleTLS

async def main():
    async with AsyncCycleTLS() as client:
        response = await client.get("https://example.com")
        print(response.status_code)

asyncio.run(main())
```

## Browser Fingerprint Profiles

### Built-in Profiles

```python
from cycletls import (
    CHROME_120,
    CHROME_121,
    CHROME_ANDROID,
    EDGE_120,
    FIREFOX_121,
    SAFARI_17,
    SAFARI_IOS,
)

response = cycletls.get("https://example.com", fingerprint=CHROME_120)
```

### TLSFingerprint

Create custom fingerprint profiles:

```python
from cycletls import TLSFingerprint

profile = TLSFingerprint(
    name="my_browser",
    ja3="771,4865-4866-4867-49195...",
    user_agent="Mozilla/5.0 ...",
    http2_fingerprint="1:65536;2:0;4:131072;5:16384|12517377|0|m,p,a,s",
)
```

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Unique identifier |
| `ja3` | `str` | JA3 fingerprint string |
| `ja4r` | `str` or `None` | JA4R fingerprint |
| `http2_fingerprint` | `str` or `None` | HTTP/2 fingerprint |
| `quic_fingerprint` | `str` or `None` | QUIC fingerprint |
| `user_agent` | `str` or `None` | User-Agent header |
| `header_order` | `list[str]` or `None` | Header ordering |
| `disable_grease` | `bool` | Disable GREASE extensions |
| `force_http1` | `bool` | Force HTTP/1.1 |
| `force_http3` | `bool` | Force HTTP/3 |

### FingerprintRegistry

Manage and look up profiles by name:

```python
from cycletls import FingerprintRegistry, TLSFingerprint

registry = FingerprintRegistry()

# Register a custom profile
registry.register(my_profile)

# Look up by name
profile = FingerprintRegistry.get("chrome_120")

# List all registered profile names
for name in registry.all():
    print(name)
```

### Loading Profiles from Files

```python
from cycletls import (
    load_fingerprint_from_file,
    load_fingerprints_from_dir,
    load_fingerprints_from_env,
)

# Load a single profile from a JSON file
profile = load_fingerprint_from_file("profiles/chrome_125.json")

# Load all profiles from a directory (auto-registers them)
load_fingerprints_from_dir("profiles/")

# Load from CYCLETLS_FINGERPRINT_DIR environment variable
load_fingerprints_from_env()
```

## Exceptions

All CycleTLS exceptions inherit from `CycleTLSError`, so you can catch
everything with a single `except` clause:

```python
from cycletls import CycleTLSError

try:
    response = cycletls.get("https://example.com")
except CycleTLSError as e:
    print(f"Request failed: {e}")
```

### Exception Hierarchy

```
CycleTLSError
  +-- RequestException
  |     +-- HTTPError            # 4xx/5xx status (from raise_for_status())
  |     +-- ConnectionError      # Network connectivity failures
  |     +-- Timeout              # Request exceeded timeout
  |     |     +-- ConnectTimeout  # (alias)
  |     |     +-- ReadTimeout     # (alias)
  |     +-- TooManyRedirects     # Redirect limit exceeded
  |     +-- InvalidURL           # Malformed URL
  |     +-- TLSError             # TLS/SSL errors
  |     +-- ProxyError           # Proxy connection errors
  |     +-- InvalidHeader        # Invalid header name or value
  +-- WebSocketError             # WebSocket-specific errors
  +-- SSEError                   # Server-Sent Events errors
```

## WebSocket Client

```python
from cycletls import WebSocketConnection

ws = WebSocketConnection("wss://echo.websocket.org")
ws.connect()
ws.send("hello")
message = ws.receive()
ws.close()
```

## Server-Sent Events (SSE)

```python
from cycletls import SSEConnection

sse = SSEConnection("https://example.com/events")
for event in sse.connect():
    print(f"{event.event}: {event.data}")
```

## Data Structures

### CaseInsensitiveDict

A dictionary subclass for HTTP headers that allows case-insensitive key
access:

```python
from cycletls import CaseInsensitiveDict

headers = CaseInsensitiveDict({"Content-Type": "application/json"})
headers["content-type"]  # "application/json"
```

### CookieJar

A container for cookies with Python collection protocols:

```python
from cycletls import CookieJar

jar = CookieJar([...])
"session_id" in jar      # True/False
len(jar)                 # number of cookies
repr(jar)                # <CookieJar(3 cookies)>
```
