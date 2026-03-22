"""Integration tests that validate TrackMe-captured browser profiles."""

import json
import os
from pathlib import Path

import pytest

from cycletls import CycleTLS, FingerprintRegistry, load_trackme_fingerprints
from cycletls.fingerprints import DEFAULT_FINGERPRINTS_FILE

_TRACKME_URL = os.environ.get("TRACKME_URL", "https://localhost:8443")
_FINGERPRINT_FILE = os.environ.get("FINGERPRINT_FILE", "/fingerprints/captured.json")
_REGISTRY_FILE = Path(
    os.environ.get("FINGERPRINTS_JSON_FILE", str(DEFAULT_FINGERPRINTS_FILE))
).resolve()

pytestmark = pytest.mark.fingerprint


def _extract_header_order_from_trackme(response: dict) -> list[str]:
    http2 = response.get("http2", {})
    sent_frames = http2.get("sent_frames", [])
    if not isinstance(sent_frames, list):
        return []

    for frame in sent_frames:
        if not isinstance(frame, dict):
            continue
        if frame.get("frame_type") != "HEADERS":
            continue

        headers = frame.get("headers")
        if not isinstance(headers, list):
            continue

        ordered: list[str] = []
        for header in headers:
            if not isinstance(header, str):
                continue
            if header.startswith(":") or ":" not in header:
                continue
            name = header.split(":", 1)[0].strip().lower()
            if name:
                ordered.append(name)
        if ordered:
            return ordered

    return []


@pytest.fixture(scope="module")
def captured_file_path() -> Path:
    path = Path(_FINGERPRINT_FILE)
    if not path.exists():
        pytest.skip(
            f"Captured fingerprint file not found: {path}. "
            "Run the playwright-capture service first."
        )
    return path


@pytest.fixture(scope="module")
def captured_fingerprints(captured_file_path: Path) -> list[dict]:
    payload = json.loads(captured_file_path.read_text())
    fingerprints = payload.get("fingerprints", [])
    if not isinstance(fingerprints, list) or not fingerprints:
        pytest.skip(f"No captured fingerprints found in {captured_file_path}")
    return fingerprints


@pytest.fixture(scope="module", autouse=True)
def register_captured_fingerprints(captured_file_path: Path):
    loaded = load_trackme_fingerprints(captured_file_path, persist_path=_REGISTRY_FILE)
    if not loaded:
        pytest.skip(f"No valid fingerprint profiles could be loaded from {captured_file_path}")
    return loaded


@pytest.fixture(scope="module")
def cycle_client():
    client = CycleTLS()
    yield client
    client.close()


@pytest.fixture(scope="module")
def observed_by_name(cycle_client, captured_fingerprints) -> dict[str, dict]:
    observed: dict[str, dict] = {}
    for fp in captured_fingerprints:
        name = fp.get("name")
        if not name:
            pytest.fail(f"Captured fingerprint missing name: {fp}")
        response = cycle_client.get(
            f"{_TRACKME_URL}/api/all",
            fingerprint=name,
            timeout=30,
            enable_connection_reuse=False,
            insecure_skip_verify=True,
        )
        assert response.status_code == 200, f"TrackMe returned {response.status_code} for {name}"
        observed[name] = response.json()
    return observed


def test_captured_profiles_registered(register_captured_fingerprints):
    for profile in register_captured_fingerprints:
        assert FingerprintRegistry.get_or_none(profile.name) is not None, (
            f"Profile '{profile.name}' should be registered"
        )


def test_captured_profiles_persisted_to_registry_json(captured_fingerprints):
    payload = json.loads(_REGISTRY_FILE.read_text())
    entries = payload.get("fingerprints", [])
    names = {entry.get("name") for entry in entries if isinstance(entry, dict)}
    for fp in captured_fingerprints:
        assert fp.get("name") in names, (
            f"Captured profile '{fp.get('name')}' should be persisted to {_REGISTRY_FILE}"
        )


def test_trackme_output_matches_captured_ua_and_ja4r(captured_fingerprints, observed_by_name):
    for fp in captured_fingerprints:
        name = fp.get("name")
        data = observed_by_name[name]
        tls = data.get("tls", {})

        expected_ua = fp.get("ua")
        if expected_ua:
            assert data.get("user_agent") == expected_ua, (
                f"{name}: user-agent mismatch\n"
                f"  expected: {expected_ua}\n"
                f"  got:      {data.get('user_agent')}"
            )

        expected_ja4_r = fp.get("ja4_r")
        if expected_ja4_r:
            assert tls.get("ja4_r") == expected_ja4_r, (
                f"{name}: ja4_r mismatch\n"
                f"  expected: {expected_ja4_r}\n"
                f"  got:      {tls.get('ja4_r')}"
            )


@pytest.mark.xfail(
    strict=False,
    reason=(
        "CycleTLS normalizes TLS internals and currently does not round-trip "
        "browser-captured JA3 strings exactly."
    ),
)
def test_trackme_output_matches_captured_ja3(captured_fingerprints, observed_by_name):
    for fp in captured_fingerprints:
        name = fp.get("name")
        expected_ja3 = fp.get("ja3")
        if not expected_ja3:
            continue
        observed = observed_by_name[name].get("tls", {}).get("ja3")
        assert observed == expected_ja3, (
            f"{name}: ja3 mismatch\n"
            f"  expected: {expected_ja3}\n"
            f"  got:      {observed}"
        )


@pytest.mark.xfail(
    strict=False,
    reason=(
        "CycleTLS currently sends a reduced browser header set and augments HTTP/2 "
        "behavior, so http2/header_order do not exactly match Playwright captures."
    ),
)
def test_trackme_output_matches_captured_http2_and_header_order(captured_fingerprints, observed_by_name):
    for fp in captured_fingerprints:
        name = fp.get("name")
        data = observed_by_name[name]
        http2 = data.get("http2", {})

        expected_http2 = fp.get("http2")
        if expected_http2:
            assert http2.get("akamai_fingerprint") == expected_http2, (
                f"{name}: http2 akamai fingerprint mismatch\n"
                f"  expected: {expected_http2}\n"
                f"  got:      {http2.get('akamai_fingerprint')}"
            )

        expected_header_order = fp.get("header_order") or []
        if expected_header_order:
            observed_header_order = _extract_header_order_from_trackme(data)
            assert observed_header_order == expected_header_order, (
                f"{name}: header order mismatch\n"
                f"  expected: {expected_header_order}\n"
                f"  got:      {observed_header_order}"
            )
