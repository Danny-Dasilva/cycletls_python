# CycleTLS Python Examples

This directory contains example scripts demonstrating various features of the CycleTLS Python library.

## Advanced Fingerprinting Examples

### 1. **ja4_fingerprint.py** - JA4 Fingerprinting
Advanced JA4 (JA4 raw format) fingerprinting examples:
- JA4R format usage for precise TLS fingerprinting
- `disable_grease` option for exact fingerprint matching
- JA4 vs JA3 comparison
- Modern TLS extensions (ECH, ALPS, Delegated Credentials)
- TLS 1.2 and TLS 1.3 fingerprints

**Run:** `python ja4_fingerprint.py`

Key features demonstrated:
- Firefox and Chrome JA4R fingerprints
- GREASE handling
- Extension parsing and validation
- Browser-specific TLS characteristics

### 2. **http2_fingerprint.py** - HTTP/2 Fingerprinting
HTTP/2 protocol fingerprinting examples:
- Custom HTTP/2 settings using `http2_fingerprint` parameter
- SETTINGS frame configuration (header table size, window size, etc.)
- Priority configuration (pseudo-header ordering)
- Window update values
- Browser-specific HTTP/2 characteristics

**Run:** `python http2_fingerprint.py`

Key features demonstrated:
- Firefox, Chrome, and Safari HTTP/2 fingerprints
- Custom SETTINGS configurations
- Pseudo-header ordering (m,p,a,s vs m,a,s,p)
- Window update value customization
- HTTP/2 with POST requests and custom headers

### 3. **http3_request.py** - HTTP/3 (QUIC) Protocol
HTTP/3 over QUIC examples:
- `force_http3` flag usage
- QUIC fingerprinting (if supported)
- HTTP/3 vs HTTP/2 performance comparison
- Connection reuse and migration
- Error handling and fallback strategies

**Run:** `python http3_request.py`

Key features demonstrated:
- Basic HTTP/3 requests
- Performance benchmarking (HTTP/3 vs HTTP/2)
- Multiple requests with connection reuse
- QUIC fingerprinting parameter
- Protocol detection and negotiation
- Combined HTTP/3 + TLS fingerprinting

## Other Examples

### Basic Usage
- **basic_request.py** - Simple GET and POST requests
- **custom_headers.py** - Custom headers and header ordering

### TLS Fingerprinting
- **ja3_fingerprint.py** - JA3 fingerprinting basics
- **advanced_tls.py** - Advanced TLS configuration

### Connection Management
- **connection_pooling.py** - Connection reuse and pooling
- **proxy_usage.py** - Proxy configuration

### Special Protocols
- **websocket_client.py** - WebSocket connections
- **sse_client.py** - Server-Sent Events (SSE)

### Data Handling
- **binary_upload.py** - Binary data handling
- **form_submission.py** - Form data submission

### Comprehensive
- **all_features.py** - All features in one example

## Requirements

```bash
pip install cycletls
```

## Notes

- HTTP/3 examples require server support (use Cloudflare sites for testing)
- Fingerprinting examples work best with fingerprint detection services
- Some examples may require internet connectivity
- Adjust timeouts based on your network conditions

## Testing Endpoints

Recommended endpoints for testing fingerprints:
- **JA3/JA4**: https://tls.peet.ws/api/all
- **JA3 Hash**: https://ja3er.com/json
- **HTTP/2**: https://tools.scrapfly.io/api/fp/anything
- **HTTP/3**: https://cloudflare-quic.com/

## Documentation

For full API documentation, visit: [CycleTLS Python Documentation](https://github.com/Danny-Dasilva/cycletls_python)
