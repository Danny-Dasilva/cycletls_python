# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.4] - 2026-10-12

### Added
- Opt-in `CYCLETLS_BACKEND=subprocess` for isolated sync, async and batch HTTP requests, with `CycleTLSWorkerDied` and worker restart after a crash.
- `local_address` parameter to bind outgoing TCP connections to a specific local IP for outbound interface/IP selection (#65)

### Fixed
- Recover Go request panics at the FFI boundary and release async handles on cancellation or timeout.
- Give Go ownership of notification descriptors and use event-loop pipe readers instead of blocking executor threads.
- Preserve shared-library debug symbols in release builds for crash investigation.
- `Do()` dropped `ServerName`, `TLS13AutoRetry`, and `DisableGrease` request fields when constructing the underlying request (#65)
- `TLS13AutoRetry` proactive upgrade corrupted JA3 `supported_groups`; the original JA3 ordering is now preserved across the retry (#65)
- `dispatchSSEAsync` could enter an infinite loop on stream cancel/EOF (#65)
