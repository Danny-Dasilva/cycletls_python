# CycleTLS Python Migration Checklist

**Goal:** Achieve complete feature parity between cycletls_python and CycleTLS (Node.js/TypeScript version)

**Started:** 2025-11-03
**Estimated Effort:** 130-175 hours
**Status:** 🚧 In Progress

---

## Phase 1: Setup & Documentation ✓

- [x] Create comprehensive CHECKLIST.md

---

## Phase 2: Go Code Migration (40-50 hours)

### New Files to Create (6 files)

- [ ] **golang/http2.go** - HTTP/2 fingerprinting support
  - [ ] HTTP2Fingerprint struct
  - [ ] Settings, priority, stream dependency configuration
  - [ ] Fingerprint parsing and application

- [ ] **golang/http3.go** - HTTP/3 + QUIC protocol support
  - [ ] HTTP3Transport implementation
  - [ ] UQuicHTTP3Transport integration
  - [ ] HTTP3RoundTripper
  - [ ] Connection pooling for HTTP/3
  - [ ] UDP packet handling
  - [ ] QUIC fingerprinting

- [ ] **golang/ja4.go** - JA4 fingerprinting
  - [ ] JA4 fingerprint generation
  - [ ] JA4H (HTTP client fingerprinting)
  - [ ] JA4H2 (HTTP/2 fingerprinting)
  - [ ] Hash generation functions
  - [ ] JA4R format support

- [ ] **golang/sse.go** - Server-Sent Events client
  - [ ] SSEClient struct
  - [ ] SSEResponse struct
  - [ ] SSEEvent struct
  - [ ] Event streaming support
  - [ ] Connection management

- [ ] **golang/websocket.go** - WebSocket client
  - [ ] WebSocketClient struct
  - [ ] WebSocketResponse struct
  - [ ] Binary/text message handling
  - [ ] Connection lifecycle management

- [ ] **golang/extensions.go** - Custom TLS extensions framework
  - [ ] Extension base framework
  - [ ] ApplicationSettings (ALPS)
  - [ ] Encrypted Client Hello (ECH)
  - [ ] Post-quantum extensions
  - [ ] GREASE extensions
  - [ ] Extension ID preservation
  - [ ] 20+ extension type implementations

### Existing Files to Update (6 files)

- [ ] **golang/client.go** - Major enhancements
  - [ ] Add JA4r field
  - [ ] Add HTTP2Fingerprint field
  - [ ] Add QUICFingerprint field
  - [ ] Add ServerName (SNI override) field
  - [ ] Add InsecureSkipVerify flag
  - [ ] Add ForceHTTP1 flag
  - [ ] Add ForceHTTP3 flag
  - [ ] Add TLS13AutoRetry flag
  - [ ] Add HeaderOrder support
  - [ ] Add TLSConfig struct
  - [ ] Implement connection pooling (ClientPoolEntry, advancedClientPool)
  - [ ] Add connection reuse management (getOrCreateClient, generateClientKey)
  - [ ] Add protocol enums (HTTP1, HTTP2, HTTP3, WebSocket, SSE)
  - [ ] Add WebSocketConnect method
  - [ ] Add SSEConnect method

- [ ] **golang/index.go** - Request processing updates
  - [ ] Add BodyBytes field for binary data
  - [ ] Add JA4r option
  - [ ] Add HTTP2Fingerprint option
  - [ ] Add QUICFingerprint option
  - [ ] Add DisableGrease option
  - [ ] Add ServerName option
  - [ ] Add InsecureSkipVerify option
  - [ ] Add ForceHTTP1 option
  - [ ] Add ForceHTTP3 option
  - [ ] Add Protocol option
  - [ ] Add TLS13AutoRetry option
  - [ ] Add EnableConnectionReuse option
  - [ ] Implement dispatchWebSocketRequest
  - [ ] Implement dispatchSSERequest
  - [ ] Implement dispatchHTTP3Request
  - [ ] Implement binary frame-based async dispatcher
  - [ ] Add request cancellation support (activeRequests map)
  - [ ] Add streaming body support
  - [ ] Enhance error recovery mechanisms

- [ ] **golang/roundtripper.go** - Core HTTP engine updates
  - [ ] Update from gitlab.com/yawning/utls to github.com/refraction-networking/utls
  - [ ] Add JA4r support (JA4RStringToSpec function)
  - [ ] Add HTTP2Fingerprint support
  - [ ] Add QUICFingerprint support
  - [ ] Add USpec field for QUIC specifications
  - [ ] Add DisableGrease flag
  - [ ] Implement HTTP/3 round tripping (makeHTTP3Request, ghttp3Dial, uhttp3Dial)
  - [ ] Implement TLS 1.3 auto-retry logic (retryWithTLS13CompatibleCurves)
  - [ ] Implement TLS 1.2 fallback logic (retryWithOriginalTLS12JA3)
  - [ ] Add address-specific mutexes for concurrent safety
  - [ ] Enhance connection reuse (CloseIdleConnections with selective close)
  - [ ] Apply HTTP/2 settings from fingerprint

- [ ] **golang/utils.go** - Parsing and conversion utilities
  - [ ] Add JA4 parsing (ParseJA4String, ParseJA4RString, ParseJA4HString)
  - [ ] Add JA4 to spec conversion (JA4RStringToSpec with components struct)
  - [ ] Add TLS 1.3 compatibility helpers (StringToTLS13CompatibleSpec, convertJA3ForTLS13, isTLS13CompatibleCurve)
  - [ ] Add QUIC fingerprinting (QUICStringToSpec, CreateUQuicSpecFromFingerprint, CreateUQuicSpecFromJA4)
  - [ ] Add header conversion utilities (ConvertFhttpHeader, ConvertHttpHeader, ConvertUtlsConfig)
  - [ ] Add extension framework (CreateExtensionFromID, genMap with 20+ extensions)
  - [ ] Add cipher suite mappings (cipherSuiteMap with 25+ suites)
  - [ ] Add signature algorithm mappings
  - [ ] Add MarshalHeader for header ordering

- [ ] **golang/errors.go** - Enhanced error handling
  - [ ] Add certificate error codes (495)
  - [ ] Add connection error codes (502)
  - [ ] Improve timeout detection
  - [ ] Add protocol-specific error messages

- [ ] **golang/connect.go** - Proxy enhancements
  - [ ] Review and merge any improvements from CycleTLS version
  - [ ] Ensure compatibility with new protocols (HTTP/3, WebSocket, SSE)

### Go Dependencies

- [ ] **Update go.mod**
  - [ ] Update to github.com/refraction-networking/utls (from gitlab.com/yawning/utls)
  - [ ] Add github.com/quic-go/quic-go
  - [ ] Add github.com/refraction-networking/uquic
  - [ ] Add github.com/gorilla/websocket (if not present)
  - [ ] Update all dependency versions

---

## Phase 3: Python API Modernization (8-10 hours)

### Schema Updates

- [ ] **cycletls/schema.py** - Request model enhancements
  - [ ] Add ja4r field (str, optional)
  - [ ] Add http2_fingerprint field (str, optional)
  - [ ] Add quic_fingerprint field (str, optional)
  - [ ] Add body_bytes field (bytes, optional)
  - [ ] Add server_name field (str, optional) - SNI override
  - [ ] Add insecure_skip_verify field (bool, default=False)
  - [ ] Add force_http1 field (bool, default=False)
  - [ ] Add force_http3 field (bool, default=False)
  - [ ] Add protocol field (str, optional)
  - [ ] Add tls13_auto_retry field (bool, default=True)
  - [ ] Add enable_connection_reuse field (bool, default=True)
  - [ ] Add disable_grease field (bool, default=False)

- [ ] **cycletls/schema.py** - Response model enhancements
  - [ ] Add body_bytes field (bytes, optional)
  - [ ] Add cookies field (List[Cookie], optional)
  - [ ] Add final_url field (str, optional)

- [ ] **cycletls/schema.py** - New models
  - [ ] Create full Cookie model (name, value, path, domain, expires, max_age, secure, http_only, same_site)
  - [ ] Create Protocol enum (HTTP1, HTTP2, HTTP3, WEBSOCKET, SSE)
  - [ ] Create WebSocketMessage model (type, message_type, data)
  - [ ] Create SSEEvent model (event, data, id, retry)

### API Updates

- [ ] **cycletls/api.py** - Communication layer enhancements
  - [ ] Implement platform-specific binary detection (Linux/macOS/Windows)
  - [ ] Update WebSocket protocol for new message types
  - [ ] Add binary data encoding/decoding (base64 vs raw)
  - [ ] Add streaming response support
  - [ ] Add WebSocket message handling
  - [ ] Add SSE event handling
  - [ ] Add protocol version negotiation
  - [ ] Improve error handling for new features

---

## Phase 4: Test Implementation (60-80 hours)

### Critical Tests (10 tests) - Core Functionality

- [ ] **test_ja3_fingerprints.py** - JA3 validation
  - [ ] Chrome 58 fingerprint test
  - [ ] Chrome 62 fingerprint test
  - [ ] Chrome 70 fingerprint test
  - [ ] Chrome 72 fingerprint test
  - [ ] Chrome 83 fingerprint test
  - [ ] Firefox 55 fingerprint test
  - [ ] Firefox 56 fingerprint test
  - [ ] Firefox 63 fingerprint test
  - [ ] Firefox 65 fingerprint test
  - [ ] iOS 11 Safari fingerprint test
  - [ ] iOS 12 Safari fingerprint test
  - [ ] iOS 17 Safari fingerprint test
  - [ ] macOS Safari fingerprint test

- [ ] **test_http2.py** - HTTP/2 protocol
  - [ ] Basic HTTP/2 request
  - [ ] HTTP/2 with custom settings
  - [ ] HTTP/2 priority testing
  - [ ] HTTP/2 vs HTTP/1.1 comparison

- [ ] **test_connection_reuse.py** - Connection pooling
  - [ ] Multiple requests with connection reuse enabled
  - [ ] Connection reuse disabled
  - [ ] Connection pool limits
  - [ ] Concurrent requests with pooling

- [ ] **test_timeout.py** - Request timeout handling
  - [ ] Basic timeout test
  - [ ] Custom timeout values
  - [ ] Read timeout vs connection timeout
  - [ ] Timeout error handling

- [ ] **test_proxy.py** - Proxy support
  - [ ] HTTP proxy
  - [ ] HTTPS proxy
  - [ ] SOCKS4 proxy
  - [ ] SOCKS5 proxy
  - [ ] Proxy authentication
  - [ ] Proxy error handling

- [ ] **test_cookies.py** - Cookie handling
  - [ ] Send cookies with request
  - [ ] Receive cookies from response
  - [ ] Cookie attributes (domain, path, secure, httponly)
  - [ ] Cookie expiration

- [ ] **test_headers.py** - Header handling
  - [ ] Custom header ordering
  - [ ] order_headers_as_provided flag
  - [ ] Header case sensitivity
  - [ ] Special headers (User-Agent, Accept, etc.)

- [ ] **test_methods.py** - HTTP methods
  - [ ] GET request
  - [ ] POST request
  - [ ] PUT request
  - [ ] PATCH request
  - [ ] DELETE request
  - [ ] HEAD request
  - [ ] OPTIONS request

- [ ] **test_redirects.py** - Redirect control
  - [ ] Follow redirects (default)
  - [ ] Disable redirects
  - [ ] Redirect limit
  - [ ] Final URL tracking

- [ ] **test_integration.py** - Basic integration suite
  - [ ] User-agent setting
  - [ ] Response headers parsing
  - [ ] HTML response handling
  - [ ] Status code validation
  - [ ] Error responses

### High Priority Tests (7 tests) - New Features

- [ ] **test_ja4_fingerprints.py** - JA4 validation
  - [ ] JA4 fingerprint generation
  - [ ] JA4R raw format parsing
  - [ ] JA4H HTTP fingerprinting
  - [ ] JA4H2 HTTP/2 fingerprinting
  - [ ] JA4 vs JA3 comparison

- [ ] **test_http3.py** - HTTP/3 + QUIC
  - [ ] Basic HTTP/3 request
  - [ ] QUIC fingerprinting
  - [ ] HTTP/3 vs HTTP/2 comparison
  - [ ] UDP transport validation
  - [ ] Force HTTP/3 flag

- [ ] **test_websocket.py** - WebSocket client
  - [ ] WebSocket connection
  - [ ] Send text messages
  - [ ] Send binary messages
  - [ ] Receive messages
  - [ ] Close connection
  - [ ] Error handling

- [ ] **test_sse.py** - Server-Sent Events
  - [ ] SSE connection
  - [ ] Receive events
  - [ ] Event types
  - [ ] Event ID tracking
  - [ ] Retry mechanism
  - [ ] Connection close

- [ ] **test_binary_data.py** - Binary data handling
  - [ ] Send binary request body (body_bytes)
  - [ ] Receive binary response (body_bytes)
  - [ ] Binary vs text detection
  - [ ] Large binary files

- [ ] **test_tls13.py** - TLS 1.3 support
  - [ ] TLS 1.3 connection
  - [ ] Auto-retry with compatible curves
  - [ ] TLS 1.2 fallback
  - [ ] Curve compatibility testing

- [ ] **test_http2_fingerprint.py** - HTTP/2 fingerprinting
  - [ ] Custom HTTP/2 settings
  - [ ] Priority configuration
  - [ ] Stream dependency
  - [ ] Fingerprint validation

### Medium Priority Tests (10 tests) - Advanced Features

- [ ] **test_insecure_skip_verify.py** - Certificate verification
  - [ ] Skip verification enabled
  - [ ] Invalid certificate acceptance
  - [ ] Self-signed certificates
  - [ ] Expired certificates

- [ ] **test_force_http1.py** - Protocol forcing
  - [ ] Force HTTP/1.1 on HTTP/2 server
  - [ ] Verify protocol used
  - [ ] Performance comparison

- [ ] **test_encoding.py** - Content encoding
  - [ ] Gzip decompression
  - [ ] Deflate decompression
  - [ ] Brotli decompression
  - [ ] Multiple encodings
  - [ ] Invalid encoding handling

- [ ] **test_multipart_form.py** - Multipart form data
  - [ ] File upload
  - [ ] Multiple files
  - [ ] Mixed form fields and files
  - [ ] Large file handling

- [ ] **test_urlencoded_form.py** - URL-encoded forms
  - [ ] Basic form submission
  - [ ] Special characters in values
  - [ ] Array/list values
  - [ ] Nested data structures

- [ ] **test_concurrent_requests.py** - Concurrent operations
  - [ ] Multiple simultaneous requests
  - [ ] Thread safety
  - [ ] Connection pool under load
  - [ ] Error isolation

- [ ] **test_images.py** - Image file handling
  - [ ] JPEG download
  - [ ] PNG download
  - [ ] GIF download
  - [ ] WebP download
  - [ ] SVG download
  - [ ] Binary integrity validation

- [ ] **test_custom_timeout.py** - Advanced timeout
  - [ ] Per-request timeout override
  - [ ] Very short timeouts (<1s)
  - [ ] Very long timeouts (>60s)
  - [ ] Timeout inheritance

- [ ] **test_cookiejar.py** - Cookie jar functionality
  - [ ] Persistent cookie storage
  - [ ] Cookie sharing across requests
  - [ ] Domain-based cookie filtering
  - [ ] Path-based cookie filtering

- [ ] **test_sni_override.py** - SNI customization
  - [ ] Custom SNI value
  - [ ] SNI different from hostname
  - [ ] SNI validation

### Low Priority Tests (6 tests) - Edge Cases

- [ ] **test_panic_regression.py** - Panic prevention
  - [ ] Invalid input handling
  - [ ] Malformed responses
  - [ ] Concurrent modification safety
  - [ ] Resource cleanup

- [ ] **test_frame_headers.py** - HTTP/2 frame validation
  - [ ] Frame header parsing
  - [ ] Frame types
  - [ ] Frame flags
  - [ ] Stream IDs

- [ ] **test_multiple_instances.py** - Multiple clients
  - [ ] Create multiple CycleTLS instances
  - [ ] Isolated state
  - [ ] Concurrent operations
  - [ ] Resource cleanup

- [ ] **test_streaming.py** - Streaming responses
  - [ ] Large response streaming
  - [ ] Chunked transfer encoding
  - [ ] Partial response handling
  - [ ] Stream cancellation

- [ ] **test_response_methods.py** - Response parsing
  - [ ] JSON parsing
  - [ ] Text extraction
  - [ ] Headers parsing
  - [ ] Status validation

- [ ] **test_edge_cases.py** - Various edge cases
  - [ ] Empty response
  - [ ] No content response (204)
  - [ ] Redirect loops
  - [ ] Invalid URLs
  - [ ] DNS failures
  - [ ] Connection refused

### Test Infrastructure

- [ ] **conftest.py** - pytest configuration
  - [ ] Shared fixtures
  - [ ] Test server setup (if needed)
  - [ ] Mock servers for WebSocket/SSE
  - [ ] Cleanup hooks

- [ ] **test_utils.py** - Test utilities
  - [ ] Helper functions
  - [ ] Assertion utilities
  - [ ] Mock data generators
  - [ ] Validation helpers

---

## Phase 5: Build System (10-15 hours)

### Go Build Configuration

- [ ] **Create build.sh** - Multi-platform build script
  - [ ] Linux AMD64 build
  - [ ] Linux ARM64 build
  - [ ] macOS AMD64 build
  - [ ] macOS ARM64 (Apple Silicon) build
  - [ ] Windows AMD64 build
  - [ ] Binary compression/stripping
  - [ ] Build validation

### Python Packaging

- [ ] **Update setup.py**
  - [ ] Include platform-specific binaries
  - [ ] Binary distribution (bdist)
  - [ ] Source distribution (sdist)
  - [ ] Platform classifiers
  - [ ] Dependency specifications

- [ ] **Update pyproject.toml**
  - [ ] Modern build backend configuration
  - [ ] Development dependencies
  - [ ] Tool configurations (pytest, mypy, black)
  - [ ] Build requirements

- [ ] **Update MANIFEST.in**
  - [ ] Include all binary files
  - [ ] Include test files
  - [ ] Include documentation
  - [ ] Exclude unnecessary files

### Platform Detection

- [ ] **Enhance api.py binary detection**
  - [ ] Detect OS (Linux/macOS/Windows)
  - [ ] Detect architecture (AMD64/ARM64)
  - [ ] Select correct binary
  - [ ] Fallback mechanisms
  - [ ] Error handling for missing binaries

### CI/CD

- [ ] **Update GitHub Actions (if exists)**
  - [ ] Multi-platform builds
  - [ ] Test execution on all platforms
  - [ ] Binary artifact storage
  - [ ] Release automation

---

## Phase 6: Documentation & Polish (15-20 hours)

### Documentation

- [ ] **Update README.md**
  - [ ] Feature overview
  - [ ] Installation instructions
  - [ ] Quick start guide
  - [ ] All new features documented
  - [ ] Migration guide from old API
  - [ ] Platform-specific notes

- [ ] **Create API_REFERENCE.md**
  - [ ] Request parameters documentation
  - [ ] Response fields documentation
  - [ ] All options and flags
  - [ ] Protocol-specific features
  - [ ] Error codes and handling

- [ ] **Create MIGRATION_GUIDE.md**
  - [ ] Breaking changes list
  - [ ] Before/after code examples
  - [ ] Deprecated features
  - [ ] New recommended patterns

### Examples

- [ ] **examples/basic_request.py** - Simple GET request
- [ ] **examples/ja3_fingerprint.py** - JA3 fingerprinting
- [ ] **examples/ja4_fingerprint.py** - JA4 fingerprinting
- [ ] **examples/http2_fingerprint.py** - HTTP/2 custom settings
- [ ] **examples/http3_request.py** - HTTP/3 usage
- [ ] **examples/websocket_client.py** - WebSocket example
- [ ] **examples/sse_client.py** - SSE streaming example
- [ ] **examples/proxy_usage.py** - Proxy configuration
- [ ] **examples/connection_pooling.py** - Connection reuse
- [ ] **examples/binary_upload.py** - Binary data handling
- [ ] **examples/form_submission.py** - Form data (multipart & urlencoded)
- [ ] **examples/advanced_tls.py** - TLS customization

### Testing & Validation

- [ ] **Run full test suite**
  - [ ] All tests passing
  - [ ] Coverage report (aim for >80%)
  - [ ] Performance benchmarks
  - [ ] Memory leak checks

- [ ] **Cross-platform testing**
  - [ ] Test on Linux
  - [ ] Test on macOS
  - [ ] Test on Windows
  - [ ] Test on different Python versions (3.8, 3.9, 3.10, 3.11, 3.12)

### Performance

- [ ] **Benchmark critical paths**
  - [ ] Connection establishment time
  - [ ] Request throughput
  - [ ] Memory usage
  - [ ] Connection pooling efficiency
  - [ ] Compare with Node.js version

- [ ] **Optimize bottlenecks**
  - [ ] Profile slow operations
  - [ ] Reduce unnecessary allocations
  - [ ] Optimize binary communication
  - [ ] Connection pool tuning

### Final Checks

- [ ] **Code quality**
  - [ ] Run linter (flake8/pylint)
  - [ ] Run type checker (mypy)
  - [ ] Format code (black)
  - [ ] Remove debug code
  - [ ] Add docstrings

- [ ] **Security review**
  - [ ] No credential leaks
  - [ ] Input validation
  - [ ] Injection prevention
  - [ ] Dependency audit

---

## Progress Summary

### Overall Progress
- **Phase 1 (Setup):** ✅ Complete (1/1)
- **Phase 2 (Go Code):** ⬜ Not Started (0/12)
- **Phase 3 (Python API):** ⬜ Not Started (0/4)
- **Phase 4 (Tests):** ⬜ Not Started (0/33)
- **Phase 5 (Build):** ⬜ Not Started (0/8)
- **Phase 6 (Documentation):** ⬜ Not Started (0/23)

### Total Tasks
- **Completed:** 1
- **In Progress:** 0
- **Remaining:** 80
- **Total:** 81

---

## Notes & Decisions

### Architecture Decisions
- ✅ Using WebSocket subprocess communication (not cffi)
- ✅ Breaking changes acceptable for API improvements
- ✅ pytest for testing framework
- ✅ Complete feature parity as goal

### Key Dependencies
- github.com/refraction-networking/utls (replaces gitlab.com/yawning/utls)
- github.com/quic-go/quic-go
- github.com/refraction-networking/uquic
- github.com/gorilla/websocket

### Known Challenges
- HTTP/3 requires QUIC protocol (complex networking)
- Binary data encoding over WebSocket (base64 overhead)
- Platform-specific binary distribution
- TLS 1.3 compatibility edge cases
- Connection pooling thread safety

---

## Quick Reference

### File Counts
- **New Go files:** 6
- **Updated Go files:** 6
- **New Python files:** ~15 (tests + examples)
- **Updated Python files:** 3-4
- **Documentation files:** 3-4

### Test Counts by Priority
- **Critical:** 10 test files (~65 test cases)
- **High:** 7 test files (~35 test cases)
- **Medium:** 10 test files (~40 test cases)
- **Low:** 6 test files (~20 test cases)
- **Total:** 33 test files (~160 test cases)

### Estimated Hours by Phase
- Phase 1: 2 hours ✅
- Phase 2: 40-50 hours
- Phase 3: 8-10 hours
- Phase 4: 60-80 hours
- Phase 5: 10-15 hours
- Phase 6: 15-20 hours
- **Total:** 135-177 hours
