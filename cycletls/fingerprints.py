"""TLS fingerprint profiles and registry for CycleTLS.

This module provides a registry architecture for reusable TLS fingerprint
configurations backed by JSON files.
"""

from __future__ import annotations

import json
import os
import random as _random
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, Optional


class BrowserFamily(str, Enum):
    """Browser family for fingerprint lookup."""

    BRAVE = "brave"
    CHROME = "chrome"
    CHROMIUM = "chromium"
    EDGE = "edge"
    FIREFOX = "firefox"
    OPERA = "opera"
    SAFARI = "safari"
    SAMSUNG = "samsung"


class Platform(str, Enum):
    """Platform / operating system for fingerprint lookup."""

    ANDROID = "android"
    IOS = "ios"
    LINUX = "linux"
    MACOS = "mac"
    WINDOWS = "win"


_FAMILY_PREFIXES: dict[BrowserFamily, tuple[str, ...]] = {
    BrowserFamily.BRAVE: ("brave",),
    BrowserFamily.CHROME: ("chrome",),
    BrowserFamily.CHROMIUM: ("chromium",),
    BrowserFamily.EDGE: ("edge", "msedge"),
    BrowserFamily.FIREFOX: ("firefox",),
    BrowserFamily.OPERA: ("opera",),
    BrowserFamily.SAFARI: ("safari",),
    BrowserFamily.SAMSUNG: ("samsung",),
}


def _version_tuple(name: str) -> tuple[int, ...]:
    """Extract numeric version components from a profile name for sorting."""
    parts = re.findall(r"\d+", name)
    return tuple(int(p) for p in parts) if parts else (0,)


@dataclass
class TLSFingerprint:
    """A reusable TLS fingerprint configuration."""

    name: str
    ja3: str
    ja4r: Optional[str] = None
    http2_fingerprint: Optional[str] = None
    quic_fingerprint: Optional[str] = None
    user_agent: Optional[str] = None
    header_order: Optional[list[str]] = None
    disable_grease: bool = False
    force_http1: bool = False
    force_http3: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TLSFingerprint:
        return cls(
            name=data["name"],
            ja3=data["ja3"],
            ja4r=data.get("ja4r"),
            http2_fingerprint=data.get("http2_fingerprint"),
            quic_fingerprint=data.get("quic_fingerprint"),
            user_agent=data.get("user_agent"),
            header_order=data.get("header_order"),
            disable_grease=data.get("disable_grease", False),
            force_http1=data.get("force_http1", False),
            force_http3=data.get("force_http3", False),
        )

    @classmethod
    def from_json(cls, path: str | Path) -> TLSFingerprint:
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "ja3": self.ja3,
        }
        if self.ja4r is not None:
            result["ja4r"] = self.ja4r
        if self.http2_fingerprint is not None:
            result["http2_fingerprint"] = self.http2_fingerprint
        if self.quic_fingerprint is not None:
            result["quic_fingerprint"] = self.quic_fingerprint
        if self.user_agent is not None:
            result["user_agent"] = self.user_agent
        if self.header_order is not None:
            result["header_order"] = self.header_order
        if self.disable_grease:
            result["disable_grease"] = True
        if self.force_http1:
            result["force_http1"] = True
        if self.force_http3:
            result["force_http3"] = True
        return result

    def to_json(self, path: str | Path) -> None:
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def apply_to_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        if "ja3" not in kwargs:
            kwargs["ja3"] = self.ja3
        if self.ja4r is not None and "ja4r" not in kwargs:
            kwargs["ja4r"] = self.ja4r
        if self.http2_fingerprint is not None and "http2_fingerprint" not in kwargs:
            kwargs["http2_fingerprint"] = self.http2_fingerprint
        if self.quic_fingerprint is not None and "quic_fingerprint" not in kwargs:
            kwargs["quic_fingerprint"] = self.quic_fingerprint
        if self.user_agent is not None and "user_agent" not in kwargs:
            kwargs["user_agent"] = self.user_agent
        if self.header_order is not None and "header_order" not in kwargs:
            kwargs["header_order"] = self.header_order
        if self.disable_grease and "disable_grease" not in kwargs:
            kwargs["disable_grease"] = True
        if self.force_http1 and "force_http1" not in kwargs:
            kwargs["force_http1"] = True
        if self.force_http3 and "force_http3" not in kwargs:
            kwargs["force_http3"] = True
        return kwargs


DEFAULT_FINGERPRINTS_FILE = Path(__file__).resolve().parent / "data" / "fingerprints.json"


class FingerprintRegistry:
    """Registry for managing fingerprint profiles."""

    _profiles: ClassVar[dict[str, TLSFingerprint]] = {}

    @classmethod
    def register(cls, profile: TLSFingerprint) -> None:
        cls._profiles[profile.name] = profile

    @classmethod
    def register_many(cls, profiles: list[TLSFingerprint]) -> None:
        for profile in profiles:
            cls.register(profile)

    @classmethod
    def unregister(cls, name: str) -> bool:
        if name in cls._profiles:
            del cls._profiles[name]
            return True
        return False

    @classmethod
    def get(cls, name: str) -> TLSFingerprint:
        if name not in cls._profiles:
            raise KeyError(f"Fingerprint profile '{name}' not found. Available: {cls.list()}")
        return cls._profiles[name]

    @classmethod
    def get_or_none(cls, name: str) -> Optional[TLSFingerprint]:
        return cls._profiles.get(name)

    @classmethod
    def list(cls) -> list[str]:
        return list(cls._profiles.keys())

    @classmethod
    def all(cls) -> dict[str, TLSFingerprint]:
        return dict(cls._profiles)

    @classmethod
    def clear(cls) -> None:
        cls._profiles.clear()

    @classmethod
    def _candidates(
        cls,
        family: Optional[BrowserFamily] = None,
        platform: Optional[Platform] = None,
    ) -> list[TLSFingerprint]:
        if family is not None:
            return cls.by_family(family, platform=platform)
        if platform is not None:
            suffix = f"_{platform.value}"
            return [fp for fp in cls._profiles.values() if fp.name.endswith(suffix)]
        return list(cls._profiles.values())

    @classmethod
    def by_family(
        cls, family: BrowserFamily, platform: Optional[Platform] = None
    ) -> list[TLSFingerprint]:
        """Return all profiles whose name starts with any prefix for *family*.

        If *platform* is given, only profiles whose name ends with
        ``_<platform.value>`` are returned.  Profiles without a platform suffix
        are excluded when *platform* is specified.
        """
        prefixes = _FAMILY_PREFIXES.get(family, ())
        candidates = [
            fp for fp in cls._profiles.values() if any(fp.name.startswith(p) for p in prefixes)
        ]
        if platform is not None:
            suffix = f"_{platform.value}"
            candidates = [fp for fp in candidates if fp.name.endswith(suffix)]
        return candidates

    @classmethod
    def latest(
        cls,
        family: Optional[BrowserFamily] = None,
        platform: Optional[Platform] = None,
    ) -> TLSFingerprint:
        """Return the profile with the highest version number.

        *family* and *platform* are optional filters; omit both to search the
        entire registry.
        """
        candidates = cls._candidates(family, platform)
        if not candidates:
            raise KeyError(
                f"No profiles found"
                f"{f' for family {family!r}' if family else ''}"
                f"{f' on platform {platform!r}' if platform else ''}. "
                f"Available: {cls.list()}"
            )
        return max(candidates, key=lambda fp: _version_tuple(fp.name))

    @classmethod
    def random(
        cls,
        family: Optional[BrowserFamily] = None,
        platform: Optional[Platform] = None,
    ) -> TLSFingerprint:
        """Return a random profile.

        *family* and *platform* are optional filters; omit both to pick from
        the entire registry.
        """
        candidates = cls._candidates(family, platform)
        if not candidates:
            raise KeyError(
                f"No profiles found"
                f"{f' for family {family!r}' if family else ''}"
                f"{f' on platform {platform!r}' if platform else ''}. "
                f"Available: {cls.list()}"
            )
        return _random.choice(candidates)

    @classmethod
    def load_from_file(cls, path: str | Path, clear: bool = False) -> list[TLSFingerprint]:
        payload = json.loads(Path(path).read_text())

        raw_items: list[dict[str, Any]]
        if isinstance(payload, dict) and isinstance(payload.get("fingerprints"), list):
            raw_items = [v for v in payload["fingerprints"] if isinstance(v, dict)]
        elif isinstance(payload, list):
            raw_items = [v for v in payload if isinstance(v, dict)]
        else:
            raise ValueError(f"Unsupported fingerprint registry format in {path}")

        loaded = [
            TLSFingerprint.from_dict(item) for item in raw_items if "name" in item and "ja3" in item
        ]
        if clear:
            cls.clear()
        cls.register_many(loaded)
        return loaded

    @classmethod
    def save_to_file(cls, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": "cycletls_fingerprint_registry/v1",
            "fingerprints": [fp.to_dict() for _, fp in sorted(cls._profiles.items())],
        }
        target.write_text(json.dumps(payload, indent=2) + "\n")


def _extract_header_order_from_trackme_raw(raw: dict[str, Any]) -> list[str]:
    http2 = raw.get("http2", {})
    sent_frames = http2.get("sent_frames", [])
    if not isinstance(sent_frames, list):
        return []

    for frame in sent_frames:
        if not isinstance(frame, dict) or frame.get("frame_type") != "HEADERS":
            continue
        headers = frame.get("headers")
        if not isinstance(headers, list):
            continue

        ordered: list[str] = []
        for header in headers:
            if not isinstance(header, str) or header.startswith(":") or ":" not in header:
                continue
            name = header.split(":", 1)[0].strip().lower()
            if name:
                ordered.append(name)
        if ordered:
            return ordered
    return []


def _extract_trackme_version(browser: str, user_agent: str) -> str:
    token_map = {
        "firefox": r"Firefox/([0-9.]+)",
        "chromium": r"(?:HeadlessChrome|Chrome)/([0-9.]+)",
        "chrome": r"(?:HeadlessChrome|Chrome)/([0-9.]+)",
    }
    pattern = token_map.get(browser.lower())
    if not pattern:
        return "unknown"
    match = re.search(pattern, user_agent)
    return match.group(1) if match else "unknown"


def _build_trackme_name(browser: str, version: str) -> str:
    safe_version = re.sub(r"[^0-9A-Za-z]+", "_", version).strip("_") or "unknown"
    return f"{browser}_{safe_version}".lower()


def _normalize_trackme_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    fingerprints = payload.get("fingerprints")
    if isinstance(fingerprints, list):
        normalized: list[dict[str, Any]] = []
        for entry in fingerprints:
            if not isinstance(entry, dict):
                continue
            normalized.append(
                {
                    "name": entry.get("name"),
                    "ja3": entry.get("ja3"),
                    "ja4r": entry.get("ja4_r") or entry.get("ja4r"),
                    "http2_fingerprint": entry.get("http2") or entry.get("http2_fingerprint"),
                    "user_agent": entry.get("ua") or entry.get("user_agent"),
                    "header_order": entry.get("header_order"),
                }
            )
        return normalized

    normalized_old: list[dict[str, Any]] = []
    for browser, entry in payload.items():
        if not isinstance(entry, dict) or "error" in entry:
            continue

        raw_candidate = entry.get("raw")
        raw: dict[str, Any] = (
            {str(k): v for k, v in raw_candidate.items()} if isinstance(raw_candidate, dict) else {}
        )
        user_agent = entry.get("ua") or raw.get("user_agent") or ""
        version = _extract_trackme_version(str(browser), str(user_agent))

        normalized_old.append(
            {
                "name": _build_trackme_name(str(browser), version),
                "ja3": entry.get("ja3"),
                "ja4r": entry.get("ja4_r") or entry.get("ja4r"),
                "http2_fingerprint": entry.get("http2") or entry.get("http2_akamai"),
                "user_agent": user_agent,
                "header_order": _extract_header_order_from_trackme_raw(raw),
            }
        )
    return normalized_old


def load_trackme_fingerprints(
    path: str | Path,
    persist_path: str | Path | None = None,
) -> list[TLSFingerprint]:
    payload = json.loads(Path(path).read_text())
    entries = _normalize_trackme_payload(payload)

    loaded: list[TLSFingerprint] = []
    for entry in entries:
        if not entry.get("name") or not entry.get("ja3"):
            continue
        profile = TLSFingerprint.from_dict(entry)
        FingerprintRegistry.register(profile)
        loaded.append(profile)

    if persist_path is not None:
        FingerprintRegistry.save_to_file(persist_path)

    return loaded


_PROFILE_EXPORTS: dict[str, str] = {
    "CHROME_120": "chrome_120_win",
    "CHROME_121": "chrome_121_win",
    "CHROME_122": "chrome_122_win",
    "CHROME_123": "chrome_123_win",
    "CHROME_124": "chrome_124_win",
    "CHROME_125": "chrome_125_win",
    "FIREFOX_121": "firefox_121_win",
    "FIREFOX_122": "firefox_122_win",
    "FIREFOX_123": "firefox_123_win",
    "FIREFOX_124": "firefox_124_win",
    "SAFARI_17": "safari_17_mac",
    "SAFARI_26": "safari_26_0_mac",
    "EDGE_120": "edge_120_win",
    "EDGE_121": "edge_121_win",
    "EDGE_122": "edge_122_win",
    "OPERA_106": "opera_106_win",
    "BRAVE_1_63": "brave_1_63_win",
    "CHROME_ANDROID": "chrome_android",
    "SAFARI_IOS": "safari_ios",
    "CHROME_LINUX": "chrome_linux",
    "FIREFOX_LINUX": "firefox_linux",
    "SAMSUNG_BROWSER_23": "samsung_browser_23_android",
}


# Initialize registry from the default JSON-backed profile list.
if DEFAULT_FINGERPRINTS_FILE.exists():
    FingerprintRegistry.load_from_file(DEFAULT_FINGERPRINTS_FILE, clear=True)
else:
    print(
        f"cycletls: warning: default fingerprints file not found: {DEFAULT_FINGERPRINTS_FILE}. "
        "Built-in profiles will not be available.",
        file=sys.stderr,
    )

# Optional extra runtime file(s)
_extra_file = os.environ.get("CYCLETLS_FINGERPRINTS_FILE")
if _extra_file:
    try:
        FingerprintRegistry.load_from_file(_extra_file, clear=False)
    except Exception as _exc:
        print(
            f"cycletls: warning: failed to load CYCLETLS_FINGERPRINTS_FILE={_extra_file!r}: {_exc}",
            file=sys.stderr,
        )

_trackme_capture_path = os.environ.get("CYCLETLS_TRACKME_FINGERPRINT_FILE")
if _trackme_capture_path:
    try:
        load_trackme_fingerprints(_trackme_capture_path, persist_path=DEFAULT_FINGERPRINTS_FILE)
    except Exception as _exc:
        print(
            f"cycletls: warning: failed to load CYCLETLS_TRACKME_FINGERPRINT_FILE={_trackme_capture_path!r}: {_exc}",
            file=sys.stderr,
        )

for export_name, profile_name in _PROFILE_EXPORTS.items():
    profile = FingerprintRegistry.get_or_none(profile_name)
    if profile is not None:
        globals()[export_name] = profile
    else:
        print(
            f"cycletls: warning: built-in profile '{profile_name}' not found in registry.",
            file=sys.stderr,
        )


_PROFILE_EXPORT_NAMES = list(_PROFILE_EXPORTS.keys())


__all__ = [
    "BrowserFamily",
    "Platform",
    "TLSFingerprint",
    "FingerprintRegistry",
    "DEFAULT_FINGERPRINTS_FILE",
    "load_trackme_fingerprints",
] + _PROFILE_EXPORT_NAMES
