# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.9] - 2026-08-31

### Fixed
- `Request.to_dict()` no longer suppresses `ja3` when `http2_fingerprint` or `quic_fingerprint` is set, so built-in `fingerprint="..."` profiles now send their stored JA3.

### Changed
- Bumped `golang.org/x/net` from 0.56.0 to 0.57.0 to 0.58.0 in the Go backend.
- Bumped `github.com/quic-go/quic-go` to the latest version in the Go backend.
- Bumped `github.com/valyala/fasthttp` to the latest version in the benchmarks.
- Bumped `github/codeql-action` from 4 to 4.37.4 to 4.37.6 to 4.37.8.
- Bumped `astral-sh/setup-uv` from 8.3.0 to 8.3.1 to 8.3.2 to 9.0.0 to 10.0.1.
- Bumped `actions/setup-go` from 6 to 7.
- Bumped `actions/setup-python` from 6 to 7.

### Updated
- Built-in browser fingerprint registry updated from multiple scheduled CI captures.

## [0.0.8] - 2026-07-08

### Fixed
- Brotli decompression no longer fails when servers append trailing bytes after a valid Brotli stream (e.g. Brave Search over HTTP/2).
- Added regression test for Brotli responses with trailing bytes.

## [0.0.7] - 2026-07-06

### Added
- PEP 503 package index deployed to GitHub Pages (including a root `index.html` and a stable repository URL).
- Default headers added to fingerprint profiles and the configuration system.

### Changed
- Live and CI fingerprint tests now use `tlsfingerprint.com` instead of `tls.peet.ws`.
- Dependency upgrades across Python, Go, and GitHub Actions.
- Bumped `astral-sh/setup-uv` from 8.2.0 to 8.3.0.

### Fixed
- Removed broken connection aliveness check and prevented `errProtocolNegotiated` leakage.
- Enforced request timeouts to prevent indefinite hangs.
- `hatch_build.py` now accepts generic library names and aligns `release.yml` Go output with arch-tagged names.
- Improved GitHub Pages deployment reliability.

### CI
- Fingerprint test workflow runs against a local `tlsfingerprint.com` instance and tolerates macOS/Windows failures.
- Removed GitHub Packages publish job (GitHub Packages does not support Python).
- Disabled PyPI publishing on forks and fixed the GitHub Packages upload URL.

## [0.0.6] - 2026-05-27

### Added
- `local_address` parameter to bind outgoing TCP connections to a specific local IP for outbound interface/IP selection.
- 14 new browser fingerprint profiles (21 total).
- Request batching via a new FFI path.
- Browser family and platform enums with OS-tagged profiles and a CI capture pipeline.
- WebSocket/SSE Go exports and Python API support.
- `json=` alias, `auth=` parameter, `Session` base URL, and `arequest()` support.

### Changed
- Upgraded to Go 1.26 for reduced CGO overhead.
- Deduplicated fingerprint strings and simplified `schema`/`config`.
- Optimized hot-path serialization, error checking, and imports.
- Unified exception hierarchy under `CycleTLSError`.

### Fixed
- `Do()` no longer drops `ServerName`, `TLS13AutoRetry`, and `DisableGrease` request fields.
- `TLS13AutoRetry` proactive upgrade no longer corrupts JA3 `supported_groups`; the original JA3 ordering is preserved.
- `dispatchSSEAsync` no longer enters an infinite loop on stream cancel/EOF.
- Added `uint16` bounds on `StatusCode` before byte conversion (CodeQL).
- Consolidated version to a single source of truth and resolved a license conflict.
