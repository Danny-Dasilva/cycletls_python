#!/usr/bin/env python3
"""
Capture real browser TLS fingerprints from tlsfingerprint.com using Playwright.

Discovers all launchable browser targets available in the current runtime
(OS/container), captures tlsfingerprint.com /api/all for each, and writes
normalized fingerprint data to a JSON file that can be loaded by
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
      "header_order": ["host", "user-agent", ...],
      "headers": {"host": "...", "user-agent": "...", ...}
    }
  ]
}

Usage:
    python capture_browser_fingerprints.py \
        --url https://tlsfingerprint \
        --output /tmp/fingerprints/captured.json \
        [--ignore-https-errors]
"""

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

_CHROME_PACKAGE = "com.android.chrome"
_CHROME_ACTIVITY = "com.google.android.apps.chrome.Main"
_BROWSER_LAUNCH_TIMEOUT_MS = 30_000


def _adb_base_command() -> list[str]:
    override = os.environ.get("ADB_BIN")
    if override:
        return shlex.split(override)
    return ["adb"]


def _adb_command(*args: str) -> list[str]:
    return [*_adb_base_command(), *args]


def _maybe_expose_cdp_port(local_port: int) -> None:
    expose_cmd = os.environ.get("ANDROID_CDP_EXPOSE_CMD")
    if not expose_cmd:
        return
    exposed_port = os.environ.get("ANDROID_CDP_HOST_PORT", "9222")
    subprocess.run(
        [*shlex.split(expose_cmd), exposed_port, str(local_port)],
        check=True,
        timeout=15,
        capture_output=True,
    )


def _configure_adb_reverse(serial: str) -> None:
    ports = os.environ.get("ADB_REVERSE_TCP_PORTS", "").strip()
    if not ports:
        return
    for item in [item.strip() for item in ports.split(",") if item.strip()]:
        if ":" in item:
            local_port, remote_port = item.split(":", 1)
        else:
            local_port = remote_port = item
        subprocess.run(
            _adb_command("-s", serial, "reverse", f"tcp:{local_port}", f"tcp:{remote_port}"),
            check=True,
            timeout=10,
            capture_output=True,
        )


def _parse_sent_headers(data: dict) -> tuple[list[str], dict[str, str]]:
    """Extract header order and header values from HTTP/2 HEADERS frames."""
    http2 = data.get("http2", {})
    sent_frames = http2.get("sent_frames", [])

    for frame in sent_frames:
        if not isinstance(frame, dict) or frame.get("frame_type") != "HEADERS":
            continue
        headers = frame.get("headers")
        if not isinstance(headers, list):
            continue

        ordered: list[str] = []
        headers_dict: dict[str, str] = {}
        for raw_header in headers:
            if not isinstance(raw_header, str):
                continue
            if raw_header.startswith(":"):
                continue
            if ":" not in raw_header:
                continue
            name, value = raw_header.split(":", 1)
            name = name.strip().lower()
            value = value.strip()
            if not name:
                continue
            ordered.append(name)
            # Keep the last value if a header appears more than once.
            headers_dict[name] = value
        if ordered:
            return ordered, headers_dict

    return [], {}


def _extract_header_order(data: dict) -> list[str]:
    """Extract header order from TrackMe response, excluding pseudo-headers."""
    return _parse_sent_headers(data)[0]


def _extract_headers(data: dict) -> dict[str, str]:
    """Extract request headers from TrackMe response, excluding pseudo-headers."""
    return _parse_sent_headers(data)[1]


def _sanitize_header_values(headers: dict[str, str]) -> dict[str, str]:
    """Remove headers whose values are dynamic or are stored elsewhere.

    sec-ch-ua*, user-agent and cookie are generated at request time
    (sec-ch-ua from the user_agent field, user-agent from the Go client).
    """
    return {
        k: v
        for k, v in headers.items()
        if k not in {"sec-ch-ua", "sec-ch-ua-mobile", "sec-ch-ua-platform", "user-agent"}
    }


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


def _detect_platform_from_ua(user_agent: str) -> str:
    """Infer a short platform tag from a user-agent string."""
    ua = user_agent.lower()
    if "windows nt" in ua:
        return "_win"
    if "macintosh" in ua or "mac os x" in ua:
        return "_mac"
    if "android" in ua:
        return "_android"
    if "linux" in ua or "x11" in ua:
        return "_linux"
    return _platform_suffix()


def _detect_browser_from_ua(user_agent: str) -> str:
    """Map a user-agent string to a profile browser name."""
    ua = user_agent.lower()
    if "edg/" in ua or "edge/" in ua:
        return "msedge"
    if "opr/" in ua or "opera/" in ua:
        return "opera"
    if "firefox/" in ua:
        return "firefox"
    # Chrome, Chromium and Brave all report Chrome/ in the UA.
    if "chrome/" in ua or "chromium/" in ua or "headlesschrome/" in ua:
        # Brave adds a brand token, but for profiling we use the generic Chrome path.
        return "chrome"
    if "version/" in ua and "safari/" in ua:
        return "safari"
    return "chromium"


def _profile_name(browser_name: str, version: str, platform: str | None = None) -> str:
    safe_version = re.sub(r"[^0-9A-Za-z]+", "_", version).strip("_") or "unknown"
    if platform is None:
        platform = _platform_suffix()
    return f"{browser_name}_{safe_version}{platform}".lower()


def _apply_profile_overrides(fp: dict, browser_override: str, version_override: str) -> dict:
    if not browser_override and not version_override:
        return fp
    fp["browser"] = browser_override or fp["browser"]
    fp["version"] = version_override or fp["version"]
    ua_platform = _detect_platform_from_ua(fp.get("ua", ""))
    fp["name"] = _profile_name(fp["browser"], fp["version"], ua_platform)
    return fp


def _candidate_targets(headless_chrome: bool) -> list[dict]:
    """Potential launch targets; availability is detected at runtime."""
    targets = [
        {"type": "chromium", "channel": None, "profile_browser": "chromium", "label": "chromium"},
        {
            "type": "chromium",
            "channel": "chrome",
            "profile_browser": "chrome",
            "label": "chromium:chrome",
        },
        {
            "type": "chromium",
            "channel": "chrome-beta",
            "profile_browser": "chrome-beta",
            "label": "chromium:chrome-beta",
        },
        {
            "type": "chromium",
            "channel": "msedge",
            "profile_browser": "msedge",
            "label": "chromium:msedge",
        },
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

    # In headed Linux CI, the bundled Playwright Chromium target has shown
    # sporadic launch hangs. Use the stable Chrome channel instead.
    if sys.platform.startswith("linux") and not headless_chrome:
        targets = [t for t in targets if t["label"] != "chromium"]

    return targets


def _is_headless_target(target: dict, headless_chrome: bool) -> bool:
    """Chromium-family targets can run in headed mode; others remain headless."""
    if target["type"] == "chromium":
        return headless_chrome
    return True


def _discover_available_targets(
    playwright_instance, headless_chrome: bool
) -> tuple[list[dict], dict[str, str]]:
    available: list[dict] = []
    unavailable: dict[str, str] = {}

    for target in _candidate_targets(headless_chrome):
        browser_type = getattr(playwright_instance, target["type"], None)
        if browser_type is None:
            unavailable[target["label"]] = "browser type not available"
            continue

        launch_kwargs = {"headless": _is_headless_target(target, headless_chrome)}
        if target["channel"]:
            launch_kwargs["channel"] = target["channel"]
        if target.get("executable_path"):
            launch_kwargs["executable_path"] = target["executable_path"]

        try:
            browser = browser_type.launch(**launch_kwargs, timeout=_BROWSER_LAUNCH_TIMEOUT_MS)
            browser.close()
            available.append(target)
            print(f"[discover] available: {target['label']}", flush=True)
        except Exception as exc:  # noqa: BLE001
            unavailable[target["label"]] = str(exc)
            print(f"[discover] unavailable: {target['label']} ({exc})", flush=True)

    return available, unavailable


def _capture_over_cdp(
    playwright_instance,
    cdp_url: str,
    url: str,
    ignore_https_errors: bool,
) -> dict:
    """Capture a fingerprint from a Chromium instance exposed via Chrome DevTools Protocol."""
    label = f"cdp:{cdp_url}"
    browser = playwright_instance.chromium.connect_over_cdp(cdp_url)

    # Create a fresh context so we can honour the certificate-error policy.
    # Force en-US locale so Accept-Language is deterministic for the registry.
    context = browser.new_context(ignore_https_errors=ignore_https_errors, locale="en-US")
    page = context.new_page()

    api_url = f"{url}/api/all"
    print(f"[{label}] Fetching {api_url} ...", flush=True)

    last_exc: Exception | None = None
    for attempt in range(1, 4):
        try:
            response = page.goto(api_url, wait_until="domcontentloaded", timeout=60_000)
            if response is not None and response.status == 200:
                break
            status = response.status if response else "no response"
            raise RuntimeError(f"[{label}] GET {api_url} returned status {status}")
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            print(f"[{label}] Attempt {attempt}/3 failed: {exc}", flush=True)
            if attempt < 3:
                time.sleep(2**attempt)
    else:
        raise last_exc  # type: ignore[misc]

    body = page.inner_text("body")
    data = json.loads(body)

    browser.close()

    tls = data.get("tls", {})
    http2 = data.get("http2", {})
    user_agent = data.get("user_agent") or ""

    profile_browser = _detect_browser_from_ua(user_agent)
    version = _extract_browser_version(profile_browser, user_agent)
    platform = _detect_platform_from_ua(user_agent)

    ordered, headers = _parse_sent_headers(data)
    result = {
        "name": _profile_name(profile_browser, version, platform),
        "browser": profile_browser,
        "version": version,
        "ja3": tls.get("ja3"),
        "ja4_r": tls.get("ja4_r"),
        "http2": http2.get("akamai_fingerprint"),
        "ua": user_agent,
        "header_order": ordered,
        "headers": _sanitize_header_values(headers),
    }

    print(
        f"[{label}] name={result['name']} ja3={bool(result['ja3'])} "
        f"http2={bool(result['http2'])} headers={len(result['header_order'])}",
        flush=True,
    )
    return result


def capture_fingerprint(
    playwright_instance,
    target: dict,
    url: str,
    ignore_https_errors: bool,
    headless_chrome: bool,
) -> dict:
    browser_type = getattr(playwright_instance, target["type"])
    launch_kwargs = {"headless": _is_headless_target(target, headless_chrome)}
    if target["channel"]:
        launch_kwargs["channel"] = target["channel"]
    if target.get("executable_path"):
        launch_kwargs["executable_path"] = target["executable_path"]

    browser = browser_type.launch(**launch_kwargs, timeout=_BROWSER_LAUNCH_TIMEOUT_MS)
    context = browser.new_context(ignore_https_errors=ignore_https_errors)
    page = context.new_page()

    api_url = f"{url}/api/all"
    print(f"[{target['label']}] Fetching {api_url} ...", flush=True)

    last_exc: Exception | None = None
    for attempt in range(1, 4):
        try:
            response = page.goto(api_url, wait_until="domcontentloaded", timeout=30_000)
            if response is not None and response.status == 200:
                break
            status = response.status if response else "no response"
            raise RuntimeError(f"[{target['label']}] GET {api_url} returned status {status}")
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            print(
                f"[{target['label']}] Attempt {attempt}/3 failed: {exc}",
                flush=True,
            )
            if attempt < 3:
                time.sleep(2**attempt)
    else:
        raise last_exc  # type: ignore[misc]

    body = page.inner_text("body")
    data = json.loads(body)

    browser.close()

    tls = data.get("tls", {})
    http2 = data.get("http2", {})
    user_agent = data.get("user_agent") or ""

    profile_browser = target["profile_browser"]
    version = _extract_browser_version(profile_browser, user_agent)

    ordered, headers = _parse_sent_headers(data)
    result = {
        "name": _profile_name(profile_browser, version),
        "browser": profile_browser,
        "version": version,
        "ja3": tls.get("ja3"),
        "ja4_r": tls.get("ja4_r"),
        "http2": http2.get("akamai_fingerprint"),
        "ua": user_agent,
        "header_order": ordered,
        "headers": _sanitize_header_values(headers),
    }

    print(
        f"[{target['label']}] name={result['name']} ja3={bool(result['ja3'])} "
        f"http2={bool(result['http2'])} headers={len(result['header_order'])}",
        flush=True,
    )
    return result


def _wait_for_cdp(port: int, timeout: float = 45.0) -> None:
    """Block until Chrome's CDP HTTP endpoint at /json responds or timeout expires."""
    deadline = time.monotonic() + timeout
    url = f"http://localhost:{port}/json"
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            return
        except Exception:  # noqa: BLE001
            time.sleep(1)
    raise RuntimeError(f"Chrome CDP endpoint {url} did not respond within {timeout:.0f}s")


def _wait_for_cdp_with_fre_handling(
    serial: str,
    label: str,
    local_port: int,
    timeout: float = 90.0,
) -> None:
    """Wait for CDP while continuing to dismiss Chrome first-run dialogs."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            _wait_for_cdp(local_port, timeout=min(5.0, max(1.0, deadline - time.monotonic())))
            return
        except RuntimeError:
            _dismiss_chrome_fre_ui(serial, label)
            _log_chrome_sockets(serial, label)
            time.sleep(2)
    raise RuntimeError(
        f"Chrome CDP endpoint http://localhost:{local_port}/json did not respond within {timeout:.0f}s"
    )


def _adb_devices() -> list[str]:
    """Return serials of connected ADB devices (state == 'device')."""
    serial_override = os.environ.get("ADB_SERIAL")
    if serial_override:
        return [serial_override]
    result = subprocess.run(_adb_command("devices"), capture_output=True, text=True, timeout=15)
    serials: list[str] = []
    for line in result.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            serials.append(parts[0])
    return serials


def _write_chrome_cmdline_flags(serial: str, label: str) -> None:
    """Write Chrome command-line flags to the well-known location.

    Chrome on Android reads /data/local/tmp/chrome-command-line when the build
    has ro.debuggable=1 (google_apis emulators) or the CHROME_COMMAND_LINE
    feature is enabled.  On google_apis_playstore (user build) this has no
    effect but it is harmless.
    """
    flags = "chrome --disable-fre --no-first-run --no-default-browser-check"
    result = subprocess.run(
        _adb_command(
            "-s",
            serial,
            "shell",
            f"echo '{flags}' > /data/local/tmp/chrome-command-line"
            " && chmod 664 /data/local/tmp/chrome-command-line",
        ),
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode == 0:
        print(f"[{label}] Wrote Chrome command-line flags file", flush=True)
    else:
        print(
            f"[{label}] Could not write Chrome flags file (non-fatal): {result.stderr.strip()}",
            flush=True,
        )


def _dismiss_chrome_fre_ui(serial: str, label: str) -> bool:
    """Tap the first 'Accept'/'Continue'/'Agree' button found in the UI hierarchy.

    Uses uiautomator dump so it works regardless of screen resolution or exact
    button placement.  Returns True if a button was found and tapped.
    """
    _UI_DUMP = "/data/local/tmp/ui_dump.xml"
    # Dump the live UI hierarchy to a file on device.
    dump = subprocess.run(
        _adb_command("-s", serial, "shell", "uiautomator", "dump", _UI_DUMP),
        capture_output=True,
        text=True,
        timeout=20,
    )
    if dump.returncode != 0:
        print(f"[{label}] uiautomator dump failed: {dump.stderr.strip()!r}", flush=True)
        return False

    xml_result = subprocess.run(
        _adb_command("-s", serial, "shell", "cat", _UI_DUMP),
        capture_output=True,
        text=True,
        timeout=15,
    )
    xml_text = xml_result.stdout.strip()
    if not xml_text:
        print(f"[{label}] UI dump empty", flush=True)
        return False

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        print(f"[{label}] UI dump XML parse error: {exc}", flush=True)
        return False

    exact_targets = (
        "use without an account",
        "continue without an account",
        "no thanks",
        "accept & continue",
        "accept and continue",
        "accept",
        "continue",
        "next",
        "yes, i'm in",
        "got it",
    )
    keyword_targets = ("without an account", "no thanks", "accept", "continue", "next", "got it")
    candidates: list[tuple[int, str, int, int]] = []

    for node in root.iter("node"):
        text = (node.get("text") or "").strip().lower()
        desc = (node.get("content-desc") or "").strip().lower()
        label_text = text or desc
        if not label_text:
            continue

        # Ignore large explanatory paragraphs; FRE actions are short controls.
        if len(label_text) > 40:
            continue

        clickable = node.get("clickable") == "true"
        enabled = node.get("enabled") == "true"
        if not clickable or not enabled:
            continue

        score = -1
        if label_text in exact_targets:
            score = 100
        elif any(target in label_text for target in keyword_targets):
            score = 50
        if score < 0:
            continue

        bounds = node.get("bounds", "")
        m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
        if not m:
            continue
        x = (int(m.group(1)) + int(m.group(3))) // 2
        y = (int(m.group(2)) + int(m.group(4))) // 2
        candidates.append((score, label_text, x, y))

    if candidates:
        candidates.sort(key=lambda item: (-item[0], item[3], item[2]))
        score, button_text, x, y = candidates[0]
        print(f"[{label}] Tapping FRE button '{button_text}' at ({x}, {y})", flush=True)
        subprocess.run(
            _adb_command("-s", serial, "shell", "input", "tap", str(x), str(y)),
            capture_output=True,
            timeout=5,
        )
        return True

    page_text = xml_text.lower()
    if "https://policies.google.com/" in page_text or "google terms of service" in page_text:
        print(f"[{label}] Chrome opened the Terms page; sending Back to return to FRE", flush=True)
        subprocess.run(
            _adb_command("-s", serial, "shell", "input", "keyevent", "4"),
            capture_output=True,
            timeout=5,
        )
        return True

    print(f"[{label}] No actionable FRE button found in UI dump", flush=True)
    return False


def _log_chrome_sockets(serial: str, label: str) -> None:
    """Print Chrome-related abstract Unix sockets for diagnostics."""
    # Read /proc/net/unix directly (no pipe to avoid shell timeout issues).
    result = subprocess.run(
        _adb_command("-s", serial, "shell", "cat", "/proc/net/unix"),
        capture_output=True,
        text=True,
        timeout=20,
    )
    chrome_lines = [ln for ln in result.stdout.splitlines() if "chrome" in ln.lower()]
    if chrome_lines:
        print(f"[{label}] Chrome abstract sockets:\n" + "\n".join(chrome_lines), flush=True)
    else:
        print(f"[{label}] No Chrome abstract sockets found yet", flush=True)


def _capture_android_cdp(
    serial: str, url: str, ignore_https_errors: bool, local_port: int = 9222
) -> dict:
    """Capture TLS fingerprint from an Android device via ADB port-forward + Playwright CDP."""
    label = f"android:{serial}"

    # Verify Chrome is installed before attempting to start it.
    pkg_check = subprocess.run(
        _adb_command("-s", serial, "shell", "pm", "list", "packages", _CHROME_PACKAGE),
        capture_output=True,
        text=True,
        timeout=15,
    )
    if _CHROME_PACKAGE not in pkg_check.stdout:
        raise RuntimeError(
            f"Chrome ({_CHROME_PACKAGE}) not installed on {serial}. "
            f"pm output: {pkg_check.stdout.strip()!r}"
        )

    # Try writing Chrome command-line flags (works on ro.debuggable=1 builds).
    _write_chrome_cmdline_flags(serial, label)
    _configure_adb_reverse(serial)

    # Force-stop any previous Chrome session so we start fresh.
    subprocess.run(
        _adb_command("-s", serial, "shell", "am", "force-stop", _CHROME_PACKAGE),
        capture_output=True,
        timeout=10,
    )
    time.sleep(1)

    print(f"[{label}] Starting Chrome (about:blank) ...", flush=True)
    start_result = subprocess.run(
        _adb_command(
            "-s",
            serial,
            "shell",
            "am",
            "start",
            "-n",
            f"{_CHROME_PACKAGE}/{_CHROME_ACTIVITY}",
            "-a",
            "android.intent.action.VIEW",
            "-d",
            "about:blank",
            "--activity-clear-task",
        ),
        capture_output=True,
        text=True,
        timeout=20,
    )
    if start_result.stdout.strip():
        print(f"[{label}] am start: {start_result.stdout.strip()}", flush=True)
    if "Error" in start_result.stdout or start_result.returncode != 0:
        raise RuntimeError(f"am start failed: {start_result.stdout.strip()}")

    # Allow Chrome time to reach the FRE dialog before we try to dismiss it.
    print(f"[{label}] Waiting for Chrome to initialize (10 s) ...", flush=True)
    time.sleep(10)

    # Try the testing broadcast first (works on Chromium test builds).
    fre_bcast = subprocess.run(
        _adb_command(
            "-s",
            serial,
            "shell",
            "am",
            "broadcast",
            "-a",
            "com.google.chrome.testing.ACCEPT_TERMS_OF_SERVICE",
        ),
        capture_output=True,
        text=True,
        timeout=10,
    )
    print(f"[{label}] FRE broadcast: {fre_bcast.stdout.strip()}", flush=True)
    time.sleep(1)

    # Use uiautomator to find and tap the actual FRE accept button (up to 3 attempts).
    for attempt in range(1, 4):
        tapped = _dismiss_chrome_fre_ui(serial, label)
        if tapped:
            time.sleep(2)
            break
        if attempt < 3:
            time.sleep(3)

    forwarded_port = local_port
    if os.environ.get("ANDROID_CDP_EXPOSE_CMD"):
        # When adb runs inside the emulator container, keep the adb forward on a
        # separate loopback port and expose the public host port via socat.
        forwarded_port = int(os.environ.get("ANDROID_CDP_FORWARD_PORT", str(local_port + 1)))

    print(f"[{label}] Forwarding CDP port {forwarded_port} ...", flush=True)
    subprocess.run(
        _adb_command(
            "-s", serial, "forward", f"tcp:{forwarded_port}", "localabstract:chrome_devtools_remote"
        ),
        check=True,
        timeout=10,
        capture_output=True,
    )
    _maybe_expose_cdp_port(forwarded_port)

    _log_chrome_sockets(serial, label)

    print(f"[{label}] Waiting for Chrome DevTools to be ready ...", flush=True)
    _wait_for_cdp_with_fre_handling(serial, label, local_port, timeout=90.0)

    data: dict = {}
    try:
        with sync_playwright() as pw:
            print(f"[{label}] Connecting via CDP ...", flush=True)
            browser = pw.chromium.connect_over_cdp(f"http://localhost:{local_port}")
            if not browser.contexts:
                raise RuntimeError("Chrome CDP session exposed no browser contexts")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            if ignore_https_errors:
                browser_cdp = browser.new_browser_cdp_session()
                browser_cdp.send("Security.enable")
                browser_cdp.send("Security.setIgnoreCertificateErrors", {"ignore": True})
                cdp = context.new_cdp_session(page)
                cdp.send("Security.enable")
                cdp.send("Security.setIgnoreCertificateErrors", {"ignore": True})

            api_url = f"{url}/api/all"
            print(f"[{label}] Fetching {api_url} ...", flush=True)
            last_exc: Exception | None = None
            for attempt in range(1, 4):
                try:
                    response = page.goto(api_url, wait_until="domcontentloaded", timeout=60_000)
                    if response is not None and response.status == 200:
                        break
                    status = response.status if response else "no response"
                    raise RuntimeError(f"GET {api_url} returned status {status}")
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    print(
                        f"[{label}] Attempt {attempt}/3 failed: {exc}",
                        flush=True,
                    )
                    if attempt < 3:
                        time.sleep(2**attempt)
            else:
                raise last_exc  # type: ignore[misc]

            body = page.inner_text("body")
            data = json.loads(body)
            browser.close()
    finally:
        subprocess.run(
            _adb_command("-s", serial, "forward", "--remove", f"tcp:{forwarded_port}"),
            capture_output=True,
            timeout=10,
        )

    tls = data.get("tls", {})
    http2 = data.get("http2", {})
    user_agent = data.get("user_agent") or ""

    version = _extract_browser_version("chrome", user_agent)
    safe_version = re.sub(r"[^0-9A-Za-z]+", "_", version).strip("_") or "unknown"

    ordered, headers = _parse_sent_headers(data)
    result = {
        "name": f"chrome_android_{safe_version}_android",
        "browser": "chrome_android",
        "version": version,
        "ja3": tls.get("ja3"),
        "ja4_r": tls.get("ja4_r"),
        "http2": http2.get("akamai_fingerprint"),
        "ua": user_agent,
        "header_order": ordered,
        "headers": _sanitize_header_values(headers),
    }
    print(
        f"[{label}] name={result['name']} ja3={bool(result['ja3'])} "
        f"http2={bool(result['http2'])} headers={len(result['header_order'])}",
        flush=True,
    )
    return result


def _main_android(args, output_path: Path) -> int:
    """Capture fingerprints from connected Android devices via ADB + CDP."""
    fingerprints: list[dict] = []
    errors: dict[str, str] = {}

    try:
        serials = _adb_devices()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: ADB device discovery failed: {exc}", file=sys.stderr, flush=True)
        serials = []
        errors["adb_discovery"] = str(exc)

    if not serials:
        if "adb_discovery" not in errors:
            errors["adb_discovery"] = "No Android devices found via ADB"
            print("ERROR: no Android devices found via ADB", file=sys.stderr, flush=True)
    else:
        for serial in serials:
            label = f"android:{serial}"
            try:
                fp = _capture_android_cdp(serial, args.url, args.ignore_https_errors)
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


def _capture_selenium(selenium_url: str, browser_name: str, url: str) -> dict:
    """Capture a fingerprint from a Selenium WebDriver server."""
    try:
        from selenium import webdriver  # type: ignore[import]
        from selenium.webdriver.common.by import By  # type: ignore[import]
        from selenium.webdriver.support import expected_conditions as EC  # type: ignore[import]
        from selenium.webdriver.support.ui import WebDriverWait  # type: ignore[import]
    except ImportError as exc:
        raise RuntimeError("selenium package is required for --selenium-url") from exc

    label = f"selenium:{browser_name}:{selenium_url}"
    browser_name_lower = browser_name.lower()

    if browser_name_lower in ("chrome", "chromium", "googlechrome"):
        from selenium.webdriver.chrome.options import Options as ChromeOptions

        options = ChromeOptions()
        options.add_argument("--disable-blink-features=PrettyPrintJSONDocument")
    elif browser_name_lower in ("edge", "microsoftedge"):
        from selenium.webdriver.edge.options import Options as EdgeOptions

        options = EdgeOptions()
        options.add_argument("--disable-blink-features=PrettyPrintJSONDocument")
    elif browser_name_lower in ("firefox", "ff"):
        from selenium.webdriver.firefox.options import Options as FirefoxOptions

        options = FirefoxOptions()
        options.set_preference("devtools.jsonview.enabled", False)
    elif browser_name_lower in ("safari", "webkit"):
        from selenium.webdriver.safari.options import Options as SafariOptions

        options = SafariOptions()
    else:
        raise RuntimeError(f"Unsupported --selenium-browser: {browser_name}")

    driver = webdriver.Remote(command_executor=selenium_url, options=options)
    try:
        api_url = f"{url}/api/all"
        print(f"[{label}] Fetching {api_url} ...", flush=True)
        driver.get(api_url)
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        body = driver.execute_script("return document.body.innerText")
        data = json.loads(body)
    finally:
        driver.quit()

    tls = data.get("tls", {})
    http2 = data.get("http2", {})
    user_agent = data.get("user_agent") or ""

    profile_browser = _detect_browser_from_ua(user_agent)
    version = _extract_browser_version(profile_browser, user_agent)
    platform = _detect_platform_from_ua(user_agent)

    ordered, headers = _parse_sent_headers(data)
    result = {
        "name": _profile_name(profile_browser, version, platform),
        "browser": profile_browser,
        "version": version,
        "ja3": tls.get("ja3"),
        "ja4_r": tls.get("ja4_r"),
        "http2": http2.get("akamai_fingerprint"),
        "ua": user_agent,
        "header_order": ordered,
        "headers": _sanitize_header_values(headers),
    }

    print(
        f"[{label}] name={result['name']} ja3={bool(result['ja3'])} "
        f"http2={bool(result['http2'])} headers={len(result['header_order'])}",
        flush=True,
    )
    return result


def _main_selenium(args, output_path: Path) -> int:
    """Capture fingerprints from a Selenium WebDriver server."""
    fingerprints: list[dict] = []
    errors: dict[str, str] = {}

    if not args.selenium_browser:
        print(
            "ERROR: --selenium-browser is required when using --selenium-url",
            file=sys.stderr,
            flush=True,
        )
        return 1

    try:
        fp = _capture_selenium(args.selenium_url, args.selenium_browser, args.url)
        _apply_profile_overrides(fp, args.browser_override, args.version_override)
        fingerprints.append(fp)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR capturing {args.selenium_url}: {exc}", file=sys.stderr, flush=True)
        errors[args.selenium_url] = str(exc)

    payload = {
        "schema": "trackme_browser_fingerprints/v1",
        "captured_at": datetime.now(UTC).isoformat(),
        "source": {
            "type": "trackme",
            "url": args.url,
            "discovery": {
                "type": "selenium",
                "selenium_url": args.selenium_url,
                "selenium_browser": args.selenium_browser,
            },
        },
        "fingerprints": fingerprints,
    }
    if errors:
        payload["errors"] = errors

    output_path.write_text(json.dumps(payload, indent=2))
    print(f"\nWrote Selenium fingerprints to {output_path}", flush=True)

    if errors:
        print(f"Failed captures: {sorted(errors)}", file=sys.stderr)
        return 1
    return 0


def _main_cdp(args, output_path: Path) -> int:
    """Capture a single fingerprint from a remote Chromium browser over CDP."""
    fingerprints: list[dict] = []
    errors: dict[str, str] = {}

    with sync_playwright() as pw:
        try:
            fp = _capture_over_cdp(pw, args.cdp_url, args.url, args.ignore_https_errors)
            _apply_profile_overrides(fp, args.browser_override, args.version_override)
            fingerprints.append(fp)
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR capturing {args.cdp_url}: {exc}", file=sys.stderr, flush=True)
            errors[args.cdp_url] = str(exc)

    payload = {
        "schema": "trackme_browser_fingerprints/v1",
        "captured_at": datetime.now(UTC).isoformat(),
        "source": {
            "type": "trackme",
            "url": args.url,
            "discovery": {"type": "cdp", "cdp_url": args.cdp_url},
        },
        "fingerprints": fingerprints,
    }
    if errors:
        payload["errors"] = errors

    output_path.write_text(json.dumps(payload, indent=2))
    print(f"\nWrote CDP fingerprints to {output_path}", flush=True)

    if errors:
        print(f"Failed captures: {sorted(errors)}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture browser fingerprints via Playwright")
    parser.add_argument("--url", default="https://localhost", help="tlsfingerprint.com base URL")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument(
        "--android-only",
        action="store_true",
        help="Capture from connected Android devices via ADB only (skips desktop browsers). "
        "Use --url https://10.0.2.2 when targeting an Android emulator.",
    )
    parser.add_argument(
        "--discover-only",
        action="store_true",
        help="Only detect available browser targets; do not call tlsfingerprint.com",
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
    parser.add_argument(
        "--headless-chrome",
        action="store_true",
        help="Run Chromium-family targets in headless mode. "
        "By default, Chrome/Edge/Chromium are launched headed.",
    )
    parser.add_argument(
        "--adb-serial",
        default="",
        help="Optional Android device serial to use instead of adb discovery.",
    )
    parser.add_argument(
        "--cdp-url",
        default="",
        help="Connect to an already-running Chromium browser over the Chrome DevTools Protocol "
        "(e.g. http://localhost:9222). Useful with Dockerized browser images.",
    )
    parser.add_argument(
        "--selenium-url",
        default="",
        help="Connect to a Selenium WebDriver server (e.g. http://localhost:4444/wd/hub). "
        "Useful with selenium/standalone-firefox, standalone-chrome, etc.",
    )
    parser.add_argument(
        "--selenium-browser",
        default="",
        help="Browser type for Selenium: firefox, chrome, edge, MicrosoftEdge, safari.",
    )
    parser.add_argument(
        "--browser-override",
        default="",
        help="Override the detected browser name (e.g. 'chromium' for a Chrome-derived image).",
    )
    parser.add_argument(
        "--version-override",
        default="",
        help="Override the detected browser version (e.g. '149.0.0.0' for matching registry).",
    )
    args = parser.parse_args()

    if args.adb_serial:
        os.environ["ADB_SERIAL"] = args.adb_serial

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.android_only:
        return _main_android(args, output_path)

    if args.selenium_url:
        return _main_selenium(args, output_path)

    if args.cdp_url:
        return _main_cdp(args, output_path)

    fingerprints: list[dict] = []
    errors: dict[str, str] = {}

    with sync_playwright() as pw:
        available_targets, unavailable_targets = _discover_available_targets(
            pw, args.headless_chrome
        )
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
            item.strip().lower() for item in args.require_browsers.split(",") if item.strip()
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
                fp = capture_fingerprint(
                    pw, target, args.url, args.ignore_https_errors, args.headless_chrome
                )
                _apply_profile_overrides(fp, args.browser_override, args.version_override)
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
