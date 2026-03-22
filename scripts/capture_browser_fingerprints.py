#!/usr/bin/env python3
"""
Capture real browser TLS fingerprints from TrackMe using Playwright.

Discovers all launchable browser targets available in the current runtime
(OS/container), captures TrackMe /api/all for each, and writes normalized
fingerprint data to a JSON file that can be loaded by
``cycletls.fingerprints.load_trackme_fingerprints``.

Output schema:
{
  "schema": "trackme_browser_fingerprints/v1",
  "fingerprints": [
    {
      "name": "firefox_135_0",
      "browser": "firefox",
      "version": "135.0",
      "ja3": "...",
      "ja4_r": "...",
      "http2": "...",
      "ua": "...",
      "header_order": ["host", "user-agent", ...]
    }
  ]
}

Usage:
    python capture_browser_fingerprints.py \
        --url https://trackme:8443 \
        --output /tmp/fingerprints/captured.json \
        [--ignore-https-errors]
"""

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

from playwright.sync_api import sync_playwright


def _extract_header_order(data: dict) -> list[str]:
    """Extract header order from TrackMe response, excluding pseudo-headers."""
    http2 = data.get("http2", {})
    sent_frames = http2.get("sent_frames", [])

    for frame in sent_frames:
        if frame.get("frame_type") != "HEADERS":
            continue
        headers = frame.get("headers")
        if not isinstance(headers, list):
            continue

        ordered: list[str] = []
        for raw_header in headers:
            if not isinstance(raw_header, str):
                continue
            if raw_header.startswith(":"):
                continue
            if ":" not in raw_header:
                continue
            name = raw_header.split(":", 1)[0].strip().lower()
            if name:
                ordered.append(name)
        if ordered:
            return ordered

    return []


def _extract_browser_version(browser_name: str, user_agent: str) -> str:
    """Infer browser version from user-agent for deterministic profile naming."""
    token_map = {
        "chromium": r"(?:HeadlessChrome|Chrome)/([0-9.]+)",
        "chrome": r"(?:HeadlessChrome|Chrome)/([0-9.]+)",
        "chrome-beta": r"(?:HeadlessChrome|Chrome)/([0-9.]+)",
        "msedge": r"Edg/([0-9.]+)",
        "msedge-beta": r"Edg/([0-9.]+)",
        "msedge-dev": r"Edg/([0-9.]+)",
        "firefox": r"Firefox/([0-9.]+)",
        "safari": r"Version/([0-9.]+)",
        "webkit": r"Version/([0-9.]+)",
    }
    pattern = token_map.get(browser_name)
    if not pattern:
        return "unknown"

    match = re.search(pattern, user_agent)
    if not match:
        return "unknown"
    return match.group(1)


def _platform_suffix() -> str:
    """Return a short platform tag for the current OS."""
    if sys.platform == "win32":
        return "_win"
    if sys.platform == "darwin":
        return "_mac"
    return "_linux"


def _profile_name(browser_name: str, version: str) -> str:
    safe_version = re.sub(r"[^0-9A-Za-z]+", "_", version).strip("_") or "unknown"
    return f"{browser_name}_{safe_version}{_platform_suffix()}".lower()


def _candidate_targets() -> list[dict]:
    """Potential launch targets; availability is detected at runtime."""
    return [
        {"type": "chromium", "channel": None, "profile_browser": "chromium", "label": "chromium"},
        {"type": "chromium", "channel": "chrome", "profile_browser": "chrome", "label": "chromium:chrome"},
        {
            "type": "chromium",
            "channel": "chrome-beta",
            "profile_browser": "chrome-beta",
            "label": "chromium:chrome-beta",
        },
        {"type": "chromium", "channel": "msedge", "profile_browser": "msedge", "label": "chromium:msedge"},
        {
            "type": "chromium",
            "channel": "msedge-beta",
            "profile_browser": "msedge-beta",
            "label": "chromium:msedge-beta",
        },
        {
            "type": "chromium",
            "channel": "msedge-dev",
            "profile_browser": "msedge-dev",
            "label": "chromium:msedge-dev",
        },
        # NOTE: Firefox version is tied to the Playwright release — system Firefox cannot be used
        # because Playwright's Firefox driver requires its own Juggler-patched build.
        {"type": "firefox", "channel": None, "profile_browser": "firefox", "label": "firefox"},
        # Playwright's WebKit is our Safari-equivalent capture target.
        {"type": "webkit", "channel": None, "profile_browser": "safari", "label": "webkit:safari"},
    ]


def _discover_available_targets(playwright_instance) -> tuple[list[dict], dict[str, str]]:
    available: list[dict] = []
    unavailable: dict[str, str] = {}

    for target in _candidate_targets():
        browser_type = getattr(playwright_instance, target["type"], None)
        if browser_type is None:
            unavailable[target["label"]] = "browser type not available"
            continue

        launch_kwargs = {"headless": True}
        if target["channel"]:
            launch_kwargs["channel"] = target["channel"]
        if target.get("executable_path"):
            launch_kwargs["executable_path"] = target["executable_path"]

        try:
            browser = browser_type.launch(**launch_kwargs)
            browser.close()
            available.append(target)
            print(f"[discover] available: {target['label']}", flush=True)
        except Exception as exc:  # noqa: BLE001
            unavailable[target["label"]] = str(exc)
            print(f"[discover] unavailable: {target['label']} ({exc})", flush=True)

    return available, unavailable


def capture_fingerprint(playwright_instance, target: dict, url: str, ignore_https_errors: bool) -> dict:
    browser_type = getattr(playwright_instance, target["type"])
    launch_kwargs = {"headless": True}
    if target["channel"]:
        launch_kwargs["channel"] = target["channel"]
    if target.get("executable_path"):
        launch_kwargs["executable_path"] = target["executable_path"]

    browser = browser_type.launch(**launch_kwargs)
    context = browser.new_context(ignore_https_errors=ignore_https_errors)
    page = context.new_page()

    api_url = f"{url}/api/all"
    print(f"[{target['label']}] Fetching {api_url} ...", flush=True)

    response = page.goto(api_url, wait_until="domcontentloaded", timeout=30_000)
    if response is None or response.status != 200:
        status = response.status if response else "no response"
        raise RuntimeError(f"[{target['label']}] GET {api_url} returned status {status}")

    body = page.inner_text("body")
    data = json.loads(body)

    browser.close()

    tls = data.get("tls", {})
    http2 = data.get("http2", {})
    user_agent = data.get("user_agent") or ""

    profile_browser = target["profile_browser"]
    version = _extract_browser_version(profile_browser, user_agent)

    result = {
        "name": _profile_name(profile_browser, version),
        "browser": profile_browser,
        "version": version,
        "ja3": tls.get("ja3"),
        "ja4_r": tls.get("ja4_r"),
        "http2": http2.get("akamai_fingerprint"),
        "ua": user_agent,
        "header_order": _extract_header_order(data),
    }

    print(
        f"[{target['label']}] name={result['name']} ja3={bool(result['ja3'])} "
        f"http2={bool(result['http2'])} headers={len(result['header_order'])}",
        flush=True,
    )
    return result


def _capture_android_device(device, url: str, ignore_https_errors: bool) -> dict:
    """Capture TLS fingerprint from a single connected Android device via ADB."""
    print(f"[android:{device.serial}] Launching Chrome ...", flush=True)
    context = device.launch_browser(ignore_https_errors=ignore_https_errors)
    page = context.new_page()

    api_url = f"{url}/api/all"
    print(f"[android:{device.serial}] Fetching {api_url} ...", flush=True)

    response = page.goto(api_url, wait_until="domcontentloaded", timeout=60_000)
    if response is None or response.status != 200:
        status = response.status if response else "no response"
        raise RuntimeError(f"GET {api_url} returned status {status}")

    body = page.inner_text("body")
    data = json.loads(body)
    context.close()

    tls = data.get("tls", {})
    http2 = data.get("http2", {})
    user_agent = data.get("user_agent") or ""

    version = _extract_browser_version("chrome", user_agent)
    safe_version = re.sub(r"[^0-9A-Za-z]+", "_", version).strip("_") or "unknown"

    result = {
        "name": f"chrome_android_{safe_version}_android",
        "browser": "chrome_android",
        "version": version,
        "ja3": tls.get("ja3"),
        "ja4_r": tls.get("ja4_r"),
        "http2": http2.get("akamai_fingerprint"),
        "ua": user_agent,
        "header_order": _extract_header_order(data),
    }
    print(
        f"[android:{device.serial}] name={result['name']} ja3={bool(result['ja3'])} "
        f"http2={bool(result['http2'])} headers={len(result['header_order'])}",
        flush=True,
    )
    return result


def _main_android(args, output_path: Path) -> int:
    """Capture fingerprints from connected Android devices via ADB."""
    fingerprints: list[dict] = []
    errors: dict[str, str] = {}

    with sync_playwright() as pw:
        try:
            devices = pw.android.devices()
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: Android device discovery failed: {exc}", file=sys.stderr, flush=True)
            devices = []
            errors["android_discovery"] = str(exc)

        if not devices:
            if "android_discovery" not in errors:
                errors["android_discovery"] = "No Android devices found via ADB"
                print("ERROR: no Android devices found via ADB", file=sys.stderr, flush=True)
        else:
            for device in devices:
                label = f"android:{device.serial}"
                try:
                    fp = _capture_android_device(device, args.url, args.ignore_https_errors)
                    fingerprints.append(fp)
                except Exception as exc:  # noqa: BLE001
                    print(f"ERROR capturing {label}: {exc}", file=sys.stderr, flush=True)
                    errors[label] = str(exc)
                finally:
                    try:
                        device.close()
                    except Exception:  # noqa: BLE001
                        pass

    payload = {
        "schema": "trackme_browser_fingerprints/v1",
        "captured_at": datetime.now(UTC).isoformat(),
        "source": {
            "type": "trackme",
            "url": args.url,
            "discovery": {"type": "android_adb"},
        },
        "fingerprints": fingerprints,
    }
    if errors:
        payload["errors"] = errors

    output_path.write_text(json.dumps(payload, indent=2))
    print(f"\nWrote Android fingerprints to {output_path}", flush=True)

    if errors:
        print(f"Android capture errors: {sorted(errors)}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture browser fingerprints via Playwright")
    parser.add_argument("--url", default="https://localhost:8443", help="TrackMe base URL")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument(
        "--android-only",
        action="store_true",
        help="Capture from connected Android devices via ADB only (skips desktop browsers). "
        "Use --url https://10.0.2.2:8443 when targeting an Android emulator.",
    )
    parser.add_argument(
        "--discover-only",
        action="store_true",
        help="Only detect available browser targets; do not call TrackMe",
    )
    parser.add_argument(
        "--require-browsers",
        default="",
        help="Comma-separated profile browser names required to be available "
        "(e.g. chrome,msedge,safari)",
    )
    parser.add_argument(
        "--ignore-https-errors",
        action="store_true",
        default=True,
        help="Ignore HTTPS certificate errors (default: True for self-signed certs)",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.android_only:
        return _main_android(args, output_path)

    fingerprints: list[dict] = []
    errors: dict[str, str] = {}

    with sync_playwright() as pw:
        available_targets, unavailable_targets = _discover_available_targets(pw)
        if not available_targets:
            print("ERROR: no playable browser targets found", file=sys.stderr, flush=True)
            payload = {
                "schema": "trackme_browser_fingerprints/v1",
                "captured_at": datetime.now(UTC).isoformat(),
                "source": {"type": "trackme", "url": args.url},
                "fingerprints": [],
                "errors": unavailable_targets,
            }
            output_path.write_text(json.dumps(payload, indent=2))
            return 1

        available_browsers = sorted({t["profile_browser"] for t in available_targets})
        required = [
            item.strip().lower()
            for item in args.require_browsers.split(",")
            if item.strip()
        ]
        missing_required = sorted(set(required) - set(available_browsers))
        if missing_required:
            errors["required_browsers"] = (
                f"Missing required browsers: {missing_required}; available={available_browsers}"
            )

        if args.discover_only:
            payload = {
                "schema": "trackme_browser_fingerprints/v1",
                "captured_at": datetime.now(UTC).isoformat(),
                "source": {
                    "type": "playwright-discovery",
                    "url": args.url,
                    "discovery": {
                        "available_targets": [t["label"] for t in available_targets],
                        "available_browsers": available_browsers,
                    },
                },
                "fingerprints": [],
            }
            if unavailable_targets:
                payload["unavailable_targets"] = unavailable_targets
            if errors:
                payload["errors"] = errors
            output_path.write_text(json.dumps(payload, indent=2))
            print(f"\nWrote discovery results to {output_path}", flush=True)
            return 1 if errors else 0

        for target in available_targets:
            label = target["label"]
            try:
                fp = capture_fingerprint(pw, target, args.url, args.ignore_https_errors)
                fingerprints.append(fp)
            except Exception as exc:  # noqa: BLE001
                print(f"ERROR capturing {label}: {exc}", file=sys.stderr, flush=True)
                errors[label] = str(exc)

    payload = {
        "schema": "trackme_browser_fingerprints/v1",
        "captured_at": datetime.now(UTC).isoformat(),
        "source": {
            "type": "trackme",
            "url": args.url,
            "discovery": {
                "available_targets": [t["label"] for t in available_targets],
                "failed_targets": sorted(set(errors) | set(unavailable_targets)),
            },
        },
        "fingerprints": fingerprints,
    }
    if unavailable_targets:
        payload["unavailable_targets"] = unavailable_targets
    if errors:
        payload["errors"] = errors

    output_path.write_text(json.dumps(payload, indent=2))
    print(f"\nWrote fingerprints to {output_path}", flush=True)

    if errors:
        print(f"Failed captures: {sorted(errors)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
