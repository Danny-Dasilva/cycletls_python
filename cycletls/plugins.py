"""Plugin loading utilities for CycleTLS fingerprints.

This module provides utilities for loading fingerprint profiles from external
sources like JSON files and directories.

Example:
    >>> from cycletls.plugins import load_fingerprints_from_dir, load_fingerprints_from_env
    >>>
    >>> # Load from a specific directory
    >>> load_fingerprints_from_dir("/path/to/fingerprints")
    >>>
    >>> # Or automatically load from CYCLETLS_FINGERPRINTS_DIR env var
    >>> load_fingerprints_from_env()
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from .fingerprints import TLSFingerprint, FingerprintRegistry

logger = logging.getLogger(__name__)


def load_fingerprints_from_dir(directory: str | Path) -> int:
    """Load all JSON fingerprint files from a directory.

    Scans the given directory for .json files and attempts to load each
    as a TLSFingerprint. Invalid files are logged and skipped.

    Args:
        directory: Path to directory containing fingerprint JSON files

    Returns:
        Number of fingerprints successfully loaded

    Example:
        >>> count = load_fingerprints_from_dir("/path/to/fingerprints")
        >>> print(f"Loaded {count} fingerprint profiles")
    """
    path = Path(directory)
    if not path.exists():
        logger.warning(f"Fingerprint directory does not exist: {directory}")
        return 0

    if not path.is_dir():
        logger.warning(f"Path is not a directory: {directory}")
        return 0

    loaded = 0
    for json_file in path.glob("*.json"):
        try:
            profile = TLSFingerprint.from_json(json_file)
            FingerprintRegistry.register(profile)
            logger.debug(f"Loaded fingerprint profile '{profile.name}' from {json_file}")
            loaded += 1
        except Exception as e:
            logger.warning(f"Failed to load fingerprint from {json_file}: {e}")

    logger.info(f"Loaded {loaded} fingerprint profiles from {directory}")
    return loaded


def load_fingerprints_from_env() -> int:
    """Load fingerprints from directory specified in CYCLETLS_FINGERPRINTS_DIR.

    If the environment variable is set, loads all .json files from that directory.
    If the variable is not set, does nothing.

    Returns:
        Number of fingerprints loaded, or 0 if env var not set

    Example:
        >>> import os
        >>> os.environ["CYCLETLS_FINGERPRINTS_DIR"] = "/my/fingerprints"
        >>> count = load_fingerprints_from_env()
    """
    dir_path = os.environ.get("CYCLETLS_FINGERPRINTS_DIR")
    if dir_path:
        return load_fingerprints_from_dir(dir_path)
    return 0


def load_fingerprint_from_file(path: str | Path) -> TLSFingerprint:
    """Load a single fingerprint from a JSON file and register it.

    Args:
        path: Path to the JSON fingerprint file

    Returns:
        The loaded TLSFingerprint

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
        KeyError: If required fields are missing
    """
    profile = TLSFingerprint.from_json(path)
    FingerprintRegistry.register(profile)
    logger.debug(f"Loaded and registered fingerprint profile '{profile.name}'")
    return profile


def create_fingerprint_template(path: str | Path, name: str = "custom_browser") -> None:
    """Create a template fingerprint JSON file for users to customize.

    Args:
        path: Path to save the template file
        name: Name for the fingerprint profile
    """
    template = TLSFingerprint(
        name=name,
        ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",
        http2_fingerprint="1:65536,2:0,3:1000,4:6291456,6:262144|15663105|0|m,a,s,p",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        header_order=[
            "host",
            "connection",
            "user-agent",
            "accept",
            "accept-encoding",
            "accept-language",
            "cookie",
        ],
    )
    template.to_json(path)
    logger.info(f"Created fingerprint template at {path}")


__all__ = [
    "load_fingerprints_from_dir",
    "load_fingerprints_from_env",
    "load_fingerprint_from_file",
    "create_fingerprint_template",
]
