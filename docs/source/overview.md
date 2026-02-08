# Overview

CycleTLS is a Python HTTP client that impersonates real browsers at the TLS
layer. It wraps a Go shared library via FFI so that every TLS handshake --
cipher suites, extensions, elliptic curves, and HTTP/2 settings -- exactly
matches a target browser profile.

## Why CycleTLS?

Many websites fingerprint incoming TLS connections to distinguish bots from
real users. Standard Python HTTP libraries (`requests`, `httpx`, `urllib3`)
produce TLS handshakes that look nothing like a browser, making them trivial
to block.

CycleTLS solves this by delegating TLS to a Go binary that supports:

- **JA3 fingerprinting** -- control the exact cipher suites, extensions, and
  curves advertised during the TLS Client Hello.
- **JA4R fingerprinting** -- fine-grained control over signature algorithms
  and extension ordering.
- **HTTP/2 fingerprinting** -- match browser-specific SETTINGS frames, window
  sizes, and pseudo-header ordering.
- **HTTP/3 and QUIC** -- modern protocol support with QUIC fingerprinting.

## Architecture

```
Python (your code)
    |
    v
cycletls Python package
    |  Pydantic models, session management,
    |  cookie jar, async support
    v
FFI boundary (ctypes / ormsgpack)
    |
    v
Go shared library (.so / .dylib / .dll)
    |  utls (uTLS) for TLS fingerprinting
    |  net/http for HTTP/1.1, HTTP/2, HTTP/3
    v
Target server
```

The Go library is bundled inside the Python wheel, so `pip install cycletls`
is all you need -- no Go toolchain required at runtime.

## Comparison with Alternatives

| Feature | CycleTLS | requests | httpx | curl-cffi |
|---|---|---|---|---|
| JA3 fingerprinting | Yes | No | No | Yes |
| JA4R fingerprinting | Yes | No | No | No |
| HTTP/2 fingerprinting | Yes | No | Partial | Yes |
| HTTP/3 / QUIC | Yes | No | No | Partial |
| Browser profiles | Built-in | No | No | Built-in |
| Async support | Yes | No | Yes | Yes |
| Session / cookies | Yes | Yes | Yes | Yes |
| WebSocket | Yes | No | No | No |
| SSE (Server-Sent Events) | Yes | No | Yes | No |
| Binary uploads | Yes | Yes | Yes | Yes |
| Connection pooling | Yes | Yes | Yes | Yes |
| Pure Python install | Yes (bundled Go binary) | Yes | Yes | No (needs libcurl) |

## Three Usage Patterns

CycleTLS supports three patterns to fit different needs:

### Pattern 1: Simple API (zero boilerplate)

```python
import cycletls

response = cycletls.get("https://example.com")
print(response.status_code)
```

Module-level functions (`get`, `post`, `put`, `patch`, `delete`, `head`,
`options`) manage a global session automatically. Configure defaults once with
`cycletls.set_default(...)` and every subsequent call inherits them.

### Pattern 2: Manual client

```python
from cycletls import CycleTLS

with CycleTLS() as client:
    response = client.get("https://example.com")
```

Gives you an explicit client lifetime via context manager.

### Pattern 3: Session (persistent cookies and headers)

```python
from cycletls import Session

with Session(base_url="https://api.example.com") as s:
    s.headers["Authorization"] = "Bearer token"
    s.post("/login", json={"user": "admin", "pass": "secret"})
    profile = s.get("/profile")  # cookies and headers persist
```

`Session` extends `CycleTLS` with a cookie jar, persistent headers, optional
`base_url`, and `auth=(user, password)` for HTTP Basic authentication.

## Key Concepts

### TLS Fingerprints

A TLS fingerprint is a compact description of the parameters a client
advertises during the TLS handshake. CycleTLS lets you supply these as
strings (`ja3=`, `ja4r=`, `http2_fingerprint=`) or as a named
`TLSFingerprint` profile object (`fingerprint=CHROME_120`).

### Browser Fingerprint Profiles

Built-in profiles bundle JA3, HTTP/2 fingerprint, and User-Agent into a
single reusable object:

```python
from cycletls import CHROME_120, FIREFOX_121, SAFARI_17

response = cycletls.get("https://example.com", fingerprint=CHROME_120)
```

Available built-in profiles: `CHROME_120`, `CHROME_121`, `FIREFOX_121`,
`SAFARI_17`, `EDGE_120`, `CHROME_ANDROID`, `SAFARI_IOS`.

You can also create custom profiles, load them from JSON files, or register
them in a directory. See the {doc}`advanced` guide for details.

### Async Support

Every sync method has an async counterpart prefixed with `a`:

```python
import asyncio
import cycletls

async def main():
    response = await cycletls.aget("https://example.com")
    print(response.status_code)

asyncio.run(main())
```

Async requests use a callback-based FFI path for lower latency and support
`asyncio.gather` for concurrent execution.
