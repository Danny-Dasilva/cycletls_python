# Advanced Usage

## Async Patterns

### Concurrent Requests with `asyncio.gather`

The biggest advantage of async is running many requests in parallel:

```python
import asyncio
import cycletls

async def main():
    # 10 requests execute concurrently
    responses = await asyncio.gather(*[
        cycletls.aget(f"https://httpbin.org/get?id={i}")
        for i in range(10)
    ])
    for r in responses:
        print(r.status_code)

asyncio.run(main())
```

### Rate Limiting with Semaphore

Control how many requests run at once:

```python
import asyncio
import cycletls

async def main():
    semaphore = asyncio.Semaphore(5)  # max 5 concurrent

    async def limited(url):
        async with semaphore:
            return await cycletls.aget(url)

    responses = await asyncio.gather(*[
        limited(f"https://httpbin.org/get?id={i}")
        for i in range(100)
    ])

asyncio.run(main())
```

### Error Handling in Async

```python
import asyncio
import cycletls
from cycletls import CycleTLSError

async def main():
    results = await asyncio.gather(
        cycletls.aget("https://httpbin.org/status/200"),
        cycletls.aget("https://httpbin.org/status/404"),
        return_exceptions=True,
    )

    for result in results:
        if isinstance(result, Exception):
            print(f"Error: {result}")
        else:
            print(f"OK: {result.status_code}")

asyncio.run(main())
```

## Custom TLS Fingerprints

### JA3 Fingerprinting

JA3 captures the TLS Client Hello parameters as a single string. Format:

```
TLSVersion,Ciphers,Extensions,EllipticCurves,EllipticCurvePointFormats
```

Example with a Chrome 83 JA3:

```python
import cycletls

response = cycletls.get(
    "https://ja3er.com/json",
    ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36",
)
print(response.json()["ja3_hash"])
```

### JA4R Fingerprinting

JA4R provides more granular control than JA3. Use `ja4r=` (raw format) to
configure fingerprints. JA4 hashes are observation-only and cannot be used as
input.

```python
from cycletls import CycleTLS

with CycleTLS() as client:
    response = client.get(
        "https://tls.peet.ws/api/all",
        ja4r="t13d1516h2_002f,0035,009c,009d,1301,1302,1303,c013,c014,c02b,c02c,c02f,c030,cca8,cca9_0000,0005,000a,000b,000d,0012,0017,001b,0023,002b,002d,0033,44cd,fe0d,ff01_0403,0804,0401,0503,0805,0501,0806,0601",
        disable_grease=False,
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    )
    data = response.json()
    print(f"JA4:   {data['tls']['ja4']}")
    print(f"JA4_r: {data['tls']['ja4_r']}")
```

JA4R format breakdown:

```
t13d1516h2_<ciphers>_<extensions>_<signature_algorithms>
```

- `t` = transport (TCP)
- `13` = TLS 1.3
- `d` = SNI present
- `15` = cipher count
- `16` = extension count
- `h2` = ALPN (HTTP/2)

### HTTP/2 Fingerprinting

Different browsers send different HTTP/2 SETTINGS frames. Match them:

```python
from cycletls import CycleTLS

with CycleTLS() as client:
    # Firefox HTTP/2 fingerprint
    response = client.get(
        "https://tls.peet.ws/api/all",
        http2_fingerprint="1:65536;2:0;4:131072;5:16384|12517377|0|m,p,a,s",
        ja3="771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0",
        user_agent="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0",
    )
```

HTTP/2 fingerprint format:

```
<settings>|<window_update>|<priority>|<pseudo_header_order>
```

Common browser fingerprints:

| Browser | HTTP/2 Fingerprint |
|---|---|
| Firefox | `1:65536;2:0;4:131072;5:16384\|12517377\|0\|m,p,a,s` |
| Chrome | `1:65536;2:0;4:6291456;6:262144\|15663105\|0\|m,a,s,p` |

### Creating Custom Profiles

Bundle JA3, HTTP/2, and User-Agent into a reusable profile:

```python
from cycletls import TLSFingerprint, FingerprintRegistry

my_profile = TLSFingerprint(
    name="custom_chrome",
    ja3="771,4865-4866-4867-49195...",
    http2_fingerprint="1:65536;2:0;4:6291456;6:262144|15663105|0|m,a,s,p",
    user_agent="Mozilla/5.0 ...",
)

# Register for lookup by name
registry = FingerprintRegistry()
registry.register(my_profile)

# Use anywhere
response = cycletls.get("https://example.com", fingerprint=my_profile)
# or by name:
response = cycletls.get("https://example.com", fingerprint="custom_chrome")
```

### Loading Profiles from Files

Store profiles as JSON and load them at startup:

```json
{
    "name": "chrome_125",
    "ja3": "771,4865-4866-4867-49195...",
    "user_agent": "Mozilla/5.0 ...",
    "http2_fingerprint": "1:65536;2:0;4:6291456..."
}
```

```python
from cycletls import load_fingerprint_from_file, load_fingerprints_from_dir

# Single file
profile = load_fingerprint_from_file("profiles/chrome_125.json")

# Entire directory (auto-registers all found profiles)
load_fingerprints_from_dir("profiles/")
```

Set the `CYCLETLS_FINGERPRINT_DIR` environment variable to auto-load a
directory of profiles:

```python
from cycletls import load_fingerprints_from_env
load_fingerprints_from_env()  # reads CYCLETLS_FINGERPRINT_DIR
```

## Proxy Configuration

CycleTLS supports HTTP, HTTPS, SOCKS4, SOCKS5, and SOCKS5h proxies.

### Per-Request Proxy

```python
import cycletls

response = cycletls.get(
    "https://httpbin.org/ip",
    proxy="socks5://127.0.0.1:9050",
)
```

### Default Proxy for All Requests

```python
import cycletls

cycletls.set_default(proxy="socks5://user:pass@proxy.example.com:1080")

# All requests now go through the proxy
response = cycletls.get("https://httpbin.org/ip")
```

### Supported Proxy Protocols

| Protocol | URL Format |
|---|---|
| HTTP | `http://host:port` |
| HTTPS | `https://host:port` |
| SOCKS4 | `socks4://host:port` |
| SOCKS5 | `socks5://host:port` |
| SOCKS5 with DNS | `socks5h://host:port` |

All protocols support `user:password@` authentication in the URL.

## HTTP/3 and QUIC

Force HTTP/3 for servers that support it:

```python
from cycletls import CycleTLS

with CycleTLS() as client:
    response = client.get(
        "https://cloudflare-quic.com/",
        force_http3=True,
        insecure_skip_verify=True,
    )
    print(f"Response over HTTP/3: {response.status_code}")
```

## Error Handling

### Checking Response Status

```python
import cycletls

response = cycletls.get("https://httpbin.org/status/404")

# Boolean checks
if response.is_error:
    print(f"Error: {response.status_code}")

if not response.ok:
    print(f"Not OK: {response.reason}")
```

### Raising Exceptions

```python
from cycletls import CycleTLSError, HTTPError

try:
    response = cycletls.get("https://httpbin.org/status/500")
    response.raise_for_status()
except HTTPError as e:
    print(f"HTTP {e.response.status_code}: {e}")
```

### Catching All CycleTLS Errors

Every CycleTLS exception inherits from `CycleTLSError`:

```python
from cycletls import CycleTLSError

try:
    response = cycletls.get("https://invalid-host.example")
except CycleTLSError as e:
    print(f"CycleTLS error: {e}")
```

## WebSocket Support

CycleTLS includes a WebSocket client with TLS fingerprinting:

```python
from cycletls import WebSocketConnection

ws = WebSocketConnection(
    "wss://echo.websocket.org",
    ja3="771,4865-4866-4867-49195...",
    user_agent="Mozilla/5.0 ...",
)

ws.connect()
ws.send("Hello, WebSocket!")

message = ws.receive()
print(message.data)

ws.close()
```

## Server-Sent Events (SSE)

Stream server-sent events:

```python
from cycletls import SSEConnection

sse = SSEConnection("https://example.com/events")

for event in sse.connect():
    print(f"Event: {event.event}")
    print(f"Data:  {event.data}")
    print(f"ID:    {event.id}")
```

## Logging

CycleTLS uses Python's standard `logging` module. Enable debug logging to
see request and response details:

```python
import logging
import cycletls

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

response = cycletls.get("https://httpbin.org/get")
```

Output:

```
DEBUG:cycletls.api:Sending GET request to https://httpbin.org/get
DEBUG:cycletls.api:Request headers: {...}
DEBUG:cycletls._ffi:Calling Go shared library getRequest()
DEBUG:cycletls._ffi:Received response from Go (size: 1234 bytes)
DEBUG:cycletls.api:Received response: 200 OK
```

Log levels:

| Level | What is logged |
|---|---|
| `DEBUG` | Request/response details, headers, FFI calls, response sizes |
| `INFO` | Library loading events |
| `ERROR` | Request failures, parsing errors |

## Binary Data

### Downloading Binary Content

```python
import cycletls

response = cycletls.get("https://example.com/image.png")
with open("image.png", "wb") as f:
    f.write(response.content)
```

### Uploading Files

```python
import cycletls

response = cycletls.post(
    "https://httpbin.org/post",
    files={"file": ("report.pdf", open("report.pdf", "rb"), "application/pdf")},
)
```

## Cookie Handling

### With Session (automatic persistence)

```python
from cycletls import Session

with Session() as s:
    # Login sets cookies
    s.post("https://example.com/login", json={"user": "admin", "pass": "secret"})

    # Cookies are sent automatically on subsequent requests
    response = s.get("https://example.com/dashboard")

    # Inspect cookies
    print(s.cookies)  # {'session_id': 'abc123', ...}
    "session_id" in s.cookies  # True
```

### Per-Request Cookies

```python
import cycletls

response = cycletls.get(
    "https://example.com",
    cookies={"session_id": "abc123", "pref": "dark_mode"},
)
```
