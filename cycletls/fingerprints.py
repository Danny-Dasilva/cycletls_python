"""TLS fingerprint profiles and registry for CycleTLS.

This module provides a plugin architecture for managing reusable TLS fingerprint
configurations. Users can define custom browser profiles and load them from JSON files.

Example:
    >>> from cycletls.fingerprints import TLSFingerprint, FingerprintRegistry
    >>>
    >>> # Use a built-in profile
    >>> profile = FingerprintRegistry.get("chrome_120")
    >>>
    >>> # Or create a custom profile
    >>> custom = TLSFingerprint(
    ...     name="my_browser",
    ...     ja3="771,4865-4867-4866-...",
    ...     user_agent="Custom/1.0"
    ... )
    >>> FingerprintRegistry.register(custom)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Optional


@dataclass
class TLSFingerprint:
    """A reusable TLS fingerprint configuration.

    Attributes:
        name: Unique identifier for this profile
        ja3: JA3 fingerprint string
        ja4r: Optional JA4R fingerprint string
        http2_fingerprint: Optional HTTP/2 fingerprint (SETTINGS, WINDOW_UPDATE, etc.)
        quic_fingerprint: Optional QUIC/HTTP3 fingerprint
        user_agent: User-Agent header value
        header_order: Ordered list of header names to maintain
        disable_grease: Whether to disable GREASE extensions
        force_http1: Force HTTP/1.1 protocol
        force_http3: Force HTTP/3 protocol
    """

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
        """Create a TLSFingerprint from a dictionary.

        Args:
            data: Dictionary with fingerprint configuration

        Returns:
            TLSFingerprint instance
        """
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
        """Load a TLSFingerprint from a JSON file.

        Args:
            path: Path to JSON file

        Returns:
            TLSFingerprint instance
        """
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
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
        """Save fingerprint to a JSON file.

        Args:
            path: Path to save JSON file
        """
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def apply_to_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Apply this fingerprint's settings to request kwargs.

        Only sets values that aren't already specified in kwargs.

        Args:
            kwargs: Request keyword arguments

        Returns:
            Updated kwargs dictionary
        """
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


class FingerprintRegistry:
    """Registry for managing fingerprint profiles.

    This is a singleton class that stores all registered fingerprint profiles.
    Profiles can be registered programmatically or loaded from JSON files.

    Example:
        >>> FingerprintRegistry.register(my_profile)
        >>> profile = FingerprintRegistry.get("chrome_120")
        >>> all_names = FingerprintRegistry.list()
    """

    _profiles: ClassVar[dict[str, TLSFingerprint]] = {}

    @classmethod
    def register(cls, profile: TLSFingerprint) -> None:
        """Register a fingerprint profile.

        Args:
            profile: TLSFingerprint to register
        """
        cls._profiles[profile.name] = profile

    @classmethod
    def unregister(cls, name: str) -> bool:
        """Unregister a fingerprint profile.

        Args:
            name: Name of profile to remove

        Returns:
            True if profile was removed, False if not found
        """
        if name in cls._profiles:
            del cls._profiles[name]
            return True
        return False

    @classmethod
    def get(cls, name: str) -> TLSFingerprint:
        """Get a fingerprint profile by name.

        Args:
            name: Profile name

        Returns:
            TLSFingerprint instance

        Raises:
            KeyError: If profile not found
        """
        if name not in cls._profiles:
            raise KeyError(f"Fingerprint profile '{name}' not found. Available: {cls.list()}")
        return cls._profiles[name]

    @classmethod
    def get_or_none(cls, name: str) -> Optional[TLSFingerprint]:
        """Get a fingerprint profile by name, or None if not found.

        Args:
            name: Profile name

        Returns:
            TLSFingerprint instance or None
        """
        return cls._profiles.get(name)

    @classmethod
    def list(cls) -> list[str]:
        """List all registered profile names.

        Returns:
            List of profile names
        """
        return list(cls._profiles.keys())

    @classmethod
    def all(cls) -> dict[str, TLSFingerprint]:
        """Get all registered profiles.

        Returns:
            Dictionary of name -> TLSFingerprint
        """
        return dict(cls._profiles)

    @classmethod
    def clear(cls) -> None:
        """Remove all registered profiles."""
        cls._profiles.clear()


# ============================================================================
# Built-in Browser Fingerprint Profiles
# ============================================================================

# Chrome 120 on Windows 10
CHROME_120 = TLSFingerprint(
    name="chrome_120",
    ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",
    http2_fingerprint="1:65536,2:0,3:1000,4:6291456,6:262144|15663105|0|m,a,s,p",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    header_order=[
        "host",
        "connection",
        "content-length",
        "sec-ch-ua",
        "sec-ch-ua-mobile",
        "sec-ch-ua-platform",
        "upgrade-insecure-requests",
        "user-agent",
        "accept",
        "sec-fetch-site",
        "sec-fetch-mode",
        "sec-fetch-user",
        "sec-fetch-dest",
        "accept-encoding",
        "accept-language",
        "cookie",
    ],
)

# Chrome 121 on Windows 10
CHROME_121 = TLSFingerprint(
    name="chrome_121",
    ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513-21,29-23-24,0",
    http2_fingerprint="1:65536,2:0,3:1000,4:6291456,6:262144|15663105|0|m,a,s,p",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    header_order=[
        "host",
        "connection",
        "content-length",
        "sec-ch-ua",
        "sec-ch-ua-mobile",
        "sec-ch-ua-platform",
        "upgrade-insecure-requests",
        "user-agent",
        "accept",
        "sec-fetch-site",
        "sec-fetch-mode",
        "sec-fetch-user",
        "sec-fetch-dest",
        "accept-encoding",
        "accept-language",
        "cookie",
    ],
)

# Firefox 121 on Windows 10
FIREFOX_121 = TLSFingerprint(
    name="firefox_121",
    ja3="771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-34-51-43-13-45-28-21,29-23-24-25-256-257,0",
    http2_fingerprint="1:65536,4:131072,5:16384|12517377|3:0:0:201,5:0:0:1,7:0:0:1,9:0:7:1,11:0:3:1,13:0:0:241|m,p,a,s",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    header_order=[
        "host",
        "user-agent",
        "accept",
        "accept-language",
        "accept-encoding",
        "connection",
        "cookie",
        "upgrade-insecure-requests",
        "sec-fetch-dest",
        "sec-fetch-mode",
        "sec-fetch-site",
        "sec-fetch-user",
    ],
)

# Safari 17 on macOS
SAFARI_17 = TLSFingerprint(
    name="safari_17",
    ja3="771,4865-4866-4867-49196-49195-52393-49200-49199-52392-49162-49161-49172-49171-157-156-53-47-49160-49170-10,0-23-65281-10-11-16-5-13-18-51-45-43-27,29-23-24-25,0",
    http2_fingerprint="4:4194304,3:100|10485760|0|m,s,p,a",
    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    header_order=[
        "host",
        "accept",
        "sec-fetch-site",
        "cookie",
        "sec-fetch-dest",
        "sec-fetch-mode",
        "user-agent",
        "accept-language",
        "accept-encoding",
        "connection",
    ],
)

# Edge 120 on Windows 10
EDGE_120 = TLSFingerprint(
    name="edge_120",
    ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",
    http2_fingerprint="1:65536,2:0,3:1000,4:6291456,6:262144|15663105|0|m,a,s,p",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    header_order=[
        "host",
        "connection",
        "content-length",
        "sec-ch-ua",
        "sec-ch-ua-mobile",
        "sec-ch-ua-platform",
        "upgrade-insecure-requests",
        "user-agent",
        "accept",
        "sec-fetch-site",
        "sec-fetch-mode",
        "sec-fetch-user",
        "sec-fetch-dest",
        "accept-encoding",
        "accept-language",
        "cookie",
    ],
)

# Mobile Chrome on Android
CHROME_ANDROID = TLSFingerprint(
    name="chrome_android",
    ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",
    http2_fingerprint="1:65536,2:0,3:1000,4:6291456,6:262144|15663105|0|m,a,s,p",
    user_agent="Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.43 Mobile Safari/537.36",
    header_order=[
        "host",
        "connection",
        "sec-ch-ua",
        "sec-ch-ua-mobile",
        "sec-ch-ua-platform",
        "upgrade-insecure-requests",
        "user-agent",
        "accept",
        "sec-fetch-site",
        "sec-fetch-mode",
        "sec-fetch-user",
        "sec-fetch-dest",
        "accept-encoding",
        "accept-language",
        "cookie",
    ],
)

# Mobile Safari on iOS
SAFARI_IOS = TLSFingerprint(
    name="safari_ios",
    ja3="771,4865-4866-4867-49196-49195-52393-49200-49199-52392-49162-49161-49172-49171-157-156-53-47-49160-49170-10,0-23-65281-10-11-16-5-13-18-51-45-43-27,29-23-24-25,0",
    http2_fingerprint="4:4194304,3:100|10485760|0|m,s,p,a",
    user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    header_order=[
        "host",
        "accept",
        "sec-fetch-site",
        "cookie",
        "sec-fetch-dest",
        "sec-fetch-mode",
        "user-agent",
        "accept-language",
        "accept-encoding",
        "connection",
    ],
)


# Register all built-in profiles
def _register_builtin_profiles() -> None:
    """Register all built-in fingerprint profiles."""
    for profile in [
        CHROME_120,
        CHROME_121,
        FIREFOX_121,
        SAFARI_17,
        EDGE_120,
        CHROME_ANDROID,
        SAFARI_IOS,
    ]:
        FingerprintRegistry.register(profile)


_register_builtin_profiles()


__all__ = [
    "TLSFingerprint",
    "FingerprintRegistry",
    "CHROME_120",
    "CHROME_121",
    "FIREFOX_121",
    "SAFARI_17",
    "EDGE_120",
    "CHROME_ANDROID",
    "SAFARI_IOS",
]
