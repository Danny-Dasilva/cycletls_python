"""Custom Hatch build hook for platform-specific wheel tags.

CycleTLS ships a Go shared library (.dylib/.so/.dll) via ctypes FFI.
The wheel must be tagged with the correct platform tag so pip installs
the right binary for each OS/arch combination.
"""

from __future__ import annotations

import platform
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


def _get_platform_tag() -> str:
    """Return the PEP 425 platform tag for the current build machine."""
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Darwin":
        if machine in ("arm64", "aarch64"):
            return "macosx_11_0_arm64"
        else:
            return "macosx_10_15_x86_64"
    elif system == "Linux":
        if machine in ("x86_64", "amd64"):
            return "manylinux2014_x86_64"
        elif machine in ("aarch64", "arm64"):
            return "manylinux2014_aarch64"
        else:
            return f"linux_{machine}"
    elif system == "Windows":
        if machine in ("amd64", "x86_64"):
            return "win_amd64"
        elif machine in ("arm64", "aarch64"):
            return "win_arm64"
        else:
            return "win32"
    else:
        return "any"


def _get_platform_binary() -> str | None:
    """Return the filename of the Go shared library for the current platform.

    Returns None if the binary is not found in cycletls/dist/.
    """
    system = platform.system()
    machine = platform.machine().lower()

    if machine in ("x86_64", "amd64"):
        arch = "x64"
    elif machine in ("aarch64", "arm64"):
        arch = "arm64"
    else:
        arch = machine

    if system == "Darwin":
        return f"libcycletls-darwin-{arch}.dylib"
    elif system == "Linux":
        return f"libcycletls-linux-{arch}.so"
    elif system == "Windows":
        return f"cycletls-win-{arch}.dll"
    return None


class CycleTLSBuildHook(BuildHookInterface):
    """Hatch build hook that sets platform-specific wheel tags and includes
    only the relevant Go shared library binary.
    """

    PLUGIN_NAME = "cycletls-platform"

    def initialize(self, version: str, build_data: dict) -> None:
        """Configure the wheel tag and shared artifacts for this platform."""
        # --- Set platform wheel tag ---
        plat_tag = _get_platform_tag()
        if plat_tag != "any":
            build_data["tag"] = f"py3-none-{plat_tag}"

        # --- Include only the platform-specific binary ---
        binary_name = _get_platform_binary()
        if binary_name is None:
            return

        dist_dir = Path(self.root) / "cycletls" / "dist"
        binary_path = dist_dir / binary_name

        if not binary_path.exists():
            return

        # Force-include just this platform binary (and its header, if present)
        build_data["force_include"] = {
            str(binary_path): f"cycletls/dist/{binary_name}",
        }

        # Also include the header file if it exists
        header_name = binary_name.rsplit(".", 1)[0] + ".h"
        header_path = dist_dir / header_name
        if header_path.exists():
            build_data["force_include"][str(header_path)] = f"cycletls/dist/{header_name}"

        # Include generic-named binaries too (backward compat with _ffi.py search order)
        system = platform.system()
        if system == "Darwin":
            generic = dist_dir / "libcycletls.dylib"
        elif system == "Linux":
            generic = dist_dir / "libcycletls.so"
        elif system == "Windows":
            generic = dist_dir / "cycletls.dll"
        else:
            generic = None

        if generic and generic.exists():
            build_data["force_include"][str(generic)] = f"cycletls/dist/{generic.name}"
