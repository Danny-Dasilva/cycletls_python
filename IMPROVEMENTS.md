# CycleTLS Python — Recent Improvements

> **Summary:** Six batches of fixes spanning version hygiene, exception handling, async performance, API ergonomics, hot-path optimizations, and type safety. 19 files changed across the library and test suite, with **75+ new tests** added to cover every change.

---

## 1. Version & License Consolidation

**Commit:** `5419edd` — *fix: consolidate version to single source of truth and fix license conflict*

**Problem:** `__version__` was defined in 4 places (hardcoded `"0.0.2"` in `__init__.py`, `"0.0.3"` in `__version__.py`, plus `pyproject.toml` and the now-removed `setup.py`), with 2 out of sync. The license in `__version__.py` was `"GNU General Public License v3 (GPLv3)"` while `pyproject.toml` declared MIT. A stale `setup.py` listed wrong dependencies. `prepare_changelog.py` referenced a non-existent `my_package` module.

**Changes:**
- `__init__.py` now imports `__version__` from `__version__.py` instead of hardcoding it
- Fixed `__version__.py` license from GPLv3 to MIT (matching `pyproject.toml`)
- Deleted `setup.py` (87 lines) — project uses hatchling, setup.py was stale
- Fixed `scripts/prepare_changelog.py` broken import (`my_package` → `cycletls`)

**Tests added:** 4 tests in `tests/test_version.py` — version attribute exists, valid semver format, `__init__` matches `__version__.py`, license is MIT.

---

## 2. Exception Hierarchy Unification

**Commit:** `6d459d6` — *fix: unify exception hierarchy under CycleTLSError*

**Problem:** FFI errors raised bare `RuntimeError`, making it impossible to catch all CycleTLS errors with a single `except` clause. `WebSocketError` and `SSEError` did not inherit from `CycleTLSError`. Corrupt msgpack data from the Go binary could raise raw `ormsgpack` errors. Base64 decode failure for `BodyBytes` silently returned `None`.

**Changes:**
- `WebSocketError` and `SSEError` now inherit from `CycleTLSError`
- All `RuntimeError` raises in `_ffi.py` replaced with `CycleTLSError`
- All `ormsgpack.unpackb()` calls wrapped to convert decode errors to `CycleTLSError`
- Invalid base64 in `BodyBytes` (`schema.py`) now raises `CycleTLSError` with a descriptive message instead of silently returning `None`

**Tests added:** 20 test functions in `tests/test_exception_hierarchy.py` (30 effective tests with parametrize) — hierarchy verification for all 11 exception classes, unified catching, corrupt msgpack handling, and base64 decode failure.

---

## 3. Callback Async Wired into Public API

**Commit:** `c701e9d` — *feat: wire callback async into public API and fix deprecated event loop calls*

**Problem:** `arequest()` used a slow polling path despite `send_request_async_callback()` being available in the Go FFI. The async path used base64 encoding instead of zero-copy msgpack. `asyncio.get_event_loop()` was used in 9+ locations, which raises `DeprecationWarning` in Python 3.12+. No `aclose()` method existed for httpx-compatible async cleanup.

**Changes:**
- Wired `send_request_async_callback()` into `arequest()` as the default async path, with automatic fallback to polling when callback fails
- Enabled zero-copy (ormsgpack) for the async path via the callback API
- Replaced all `asyncio.get_event_loop()` with `asyncio.get_running_loop()` across `_ffi.py`, `websocket.py`, `sse.py`, and `test_callback_async.py`
- Added `aclose()` method to `CycleTLS` for httpx-compatible async cleanup
- Added `_has_callback_support()` detection function in `_ffi.py`
- Fixed `__aexit__` to use `aclose()` directly, avoiding coroutine warning with `AsyncCycleTLS` subclass
- Simplified `async_api.py` (reduced from ~240 lines of complex polling to thin wrappers)

**Tests added:** 13 tests in `tests/test_async_improvements.py` — basic arequest, convenience methods (aget/apost), aclose lifecycle, concurrent gather, async context manager with cleanup on error, running-loop compatibility.

---

## 4. API UX Improvements

**Commit:** `9f671a9` — *feat: add json= alias, auth= parameter, Session base_url and arequest()*

**Problem:** Users coming from `requests` or `httpx` expected `json=` (not `json_data=`), `auth=` for Basic auth, and `base_url` on sessions. Async `Session.arequest()` silently skipped cookie persistence (cookies from responses were never stored).

**Changes:**
- Added `json=` as alias for `json_data=` on `_prepare_request`, `request`, `arequest`, and all convenience methods (`post`, `put`, `patch`, `apost`, `aput`, `apatch`), with a `ValueError` if both are passed
- Added `auth=(user, pass)` tuple for HTTP Basic authentication across all methods
- Added `Session(base_url=)` to prepend base URL to relative paths (absolute URLs bypass it)
- Added `Session(auth=)` for session-level default authentication (per-request `auth=` overrides)
- Overrode `Session.arequest()` with full cookie persistence (matching sync behavior)
- Extracted `_prepare_url`, `_merge_session_state`, `_update_cookies_from_response` helpers in `Session` for DRY sync/async paths

**Tests added:** 13 tests in `tests/test_api_ux.py` — json alias sends body and sets Content-Type, conflict raises ValueError, auth adds Basic header on GET/POST, base_url prepends/skips/handles trailing slash, session auth applies to all requests, per-request auth overrides session auth, async cookie persistence and base_url.

---

## 5. Performance Hot-Path Optimizations

**Commit:** `0d26dec` — *perf: optimize hot-path serialization, error checking, and imports*

**Problem:** `json.dumps()` was used for request body serialization (slower than orjson). `_raise_for_error_response()` ran expensive `.lower()` string comparisons on every response including successful ones. `import math` was inside a method body (per-call overhead). `_STATUS_PHRASES` dict was recreated on every property access. `Response.json()` called `.encode()` unnecessarily on the body string.

**Changes:**
- Replaced `json.dumps()` with `orjson.dumps()` for JSON body serialization (exposed as `_json_dumps`)
- Short-circuit `_raise_for_error_response()` for 2xx/3xx status codes (returns immediately, skips all `.lower()` checks)
- Moved `import math` to module level in `schema.py`
- Cached `_STATUS_PHRASES` as a module-level `_STATUS_PHRASES` constant dict
- Fixed `Response.json()` to pass body string directly to `orjson.loads()` without unnecessary `.encode()`

**Tests added:** 25 tests in `tests/test_performance_fixes.py` — short-circuit for 200/201/301/399, error cases still raise (timeout, DNS, generic), Response.json() with various payloads, timeout rounding via math.ceil, orjson serialization with nested/special chars, batch payload serialization, _STATUS_PHRASES module-level cache verification, math module-level import check.

---

## 6. PEP 561 Type Marker (In Progress)

**Changes so far:**
- Added `cycletls/py.typed` marker file for PEP 561 compliance
- Type annotation work on public API methods in progress

---

## Test Coverage Summary

| Test File | Tests | Covers |
|-----------|------:|--------|
| `test_version.py` | 4 | Version consistency, semver format, license |
| `test_exception_hierarchy.py` | 20 (30 effective) | All 11 exception classes, unified catching, corrupt data |
| `test_async_improvements.py` | 13 | arequest, aclose, gather, context manager, event loop |
| `test_performance_fixes.py` | 25 | Short-circuit, orjson, math import, status cache |
| `test_api_ux.py` | 13 | json=, auth=, base_url, session cookies async |
| **Total** | **75+ tests** | |

All new tests use `pytest` with `unittest.mock.patch` for FFI isolation (no Go binary needed) and `pytest-asyncio` for async tests.

---

## Files Changed

**Modified (11):**
- `cycletls/__init__.py` — version import, async convenience methods
- `cycletls/__version__.py` — license fix (GPLv3 → MIT)
- `cycletls/_ffi.py` — CycleTLSError for all FFI errors, callback support detection, get_running_loop
- `cycletls/api.py` — orjson serialization, json=/auth= params, arequest callback path, aclose
- `cycletls/async_api.py` — simplified to thin wrappers over callback async
- `cycletls/schema.py` — short-circuit error check, module-level imports/constants, base64 error handling
- `cycletls/sessions.py` — base_url, session auth, async cookie persistence, helper extraction
- `cycletls/sse.py` — SSEError inherits CycleTLSError, get_running_loop
- `cycletls/websocket.py` — WebSocketError inherits CycleTLSError, get_running_loop
- `pyproject.toml` — version sync
- `scripts/prepare_changelog.py` — fixed broken import

**Deleted (1):**
- `setup.py` — stale, project uses hatchling

**Added (6):**
- `cycletls/py.typed` — PEP 561 marker
- `tests/test_version.py`
- `tests/test_exception_hierarchy.py`
- `tests/test_async_improvements.py`
- `tests/test_performance_fixes.py`
- `tests/test_api_ux.py`

**Net change:** +1,511 lines / -528 lines across 19 files.
