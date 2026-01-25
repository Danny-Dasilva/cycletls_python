"""
TLS Fingerprint integration tests against tlsfingerprint.com.

This package mirrors the TypeScript tests in tests/tlsfingerprint/:
- test_basic.py       -> basic.test.ts
- test_compression.py -> compression.test.ts
- test_cookies.py     -> cookies.test.ts
- test_redirect.py    -> redirect.test.ts
- conftest.py         -> helpers.ts

Run all tlsfingerprint tests:
    pytest tests/tlsfingerprint/ -v

Tests require network access to tlsfingerprint.com.
Tests will be skipped if the service is unavailable (521 Cloudflare error).
"""
