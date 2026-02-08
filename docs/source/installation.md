# Installation

**cycletls** supports Python >= 3.8 on Linux, macOS, and Windows.

## Installing with pip

cycletls is available [on PyPI](https://pypi.org/project/cycletls/). Install
it with pip:

```bash
pip install cycletls
```

Or with [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv add cycletls
```

The wheel ships with a pre-built Go shared library for your platform, so no
Go toolchain is needed at runtime.

## Supported Platforms

| Platform | Architecture | Binary |
|---|---|---|
| Linux | x86_64 | `cycletls.so` |
| Linux | aarch64 | `cycletls.so` |
| macOS | x86_64 (Intel) | `cycletls.dylib` |
| macOS | arm64 (Apple Silicon) | `cycletls.dylib` |
| Windows | x86_64 | `cycletls.dll` |

## Installing from Source

To install from source (requires Go >= 1.21 for building the shared library):

```bash
git clone https://github.com/Danny-Dasilva/cycletls_python.git
cd cycletls_python
pip install -e .
```

## Quick Start

Verify your installation works:

```python
import cycletls

# Make a simple GET request
response = cycletls.get("https://httpbin.org/get")
print(response.status_code)  # 200
print(response.json())       # {"args": {}, "headers": {...}, ...}
```

### With TLS fingerprinting

```python
import cycletls

response = cycletls.get(
    "https://tls.peet.ws/api/all",
    ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36",
)
print(response.json()["tls"]["ja3_hash"])
```

### With a browser profile

```python
import cycletls
from cycletls import CHROME_120

response = cycletls.get("https://example.com", fingerprint=CHROME_120)
print(response.status_code)
```

### Async usage

```python
import asyncio
import cycletls

async def main():
    response = await cycletls.aget("https://httpbin.org/get")
    print(response.status_code)

asyncio.run(main())
```

## Dependencies

cycletls has minimal Python dependencies:

- [pydantic](https://docs.pydantic.dev/) -- data validation and settings
- [ormsgpack](https://github.com/aviramha/ormsgpack) -- fast MessagePack for FFI communication
- [orjson](https://github.com/ijl/orjson) -- fast JSON serialization (optional, falls back to stdlib `json`)

All dependencies are installed automatically by pip.

## Troubleshooting

### `OSError: cannot load shared library`

The Go shared library for your platform may not be bundled in the wheel. Check
that your OS and architecture are in the supported platforms table above. If
building from source, make sure Go >= 1.21 is installed and run `make build`
before `pip install -e .`.

### Import errors after upgrade

If you see import errors after upgrading, try a clean reinstall:

```bash
pip uninstall cycletls && pip install cycletls
```
