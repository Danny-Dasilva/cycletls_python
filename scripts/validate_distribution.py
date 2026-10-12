"""Reject incomplete release archives before any files reach PyPI."""

import platform
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path


def validate(directory: Path) -> None:
    wheels = list(directory.glob("*.whl"))
    if not wheels:
        raise ValueError("No wheel was built")
    extension = {"Darwin": ".dylib", "Linux": ".so", "Windows": ".dll"}[platform.system()]
    for wheel in wheels:
        with zipfile.ZipFile(wheel) as archive:
            native = [
                name
                for name in archive.namelist()
                if name.startswith("cycletls/dist/") and name.endswith(extension)
            ]
            if not native:
                raise ValueError(f"{wheel.name} has no {extension} runtime library")
            with tempfile.TemporaryDirectory() as temporary:
                for name in native:
                    path = archive.extract(name, temporary)
                    subprocess.run(
                        [
                            sys.executable,
                            "-c",
                            "import ctypes, sys; lib = ctypes.CDLL(sys.argv[1]); "
                            "assert lib.getRequestZeroCopy; assert lib.freeString; "
                            "lib.cancelAsyncRequest(0)",
                            path,
                        ],
                        check=True,
                        timeout=30,
                    )
        print(f"Validated {wheel.name}: native library loads and exposes the FFI API")
    for source in directory.glob("*.tar.gz"):
        if source.stat().st_size >= 100_000_000:
            raise ValueError(f"{source.name} exceeds PyPI's 100 MB file limit")
        with tarfile.open(source) as archive:
            names = archive.getnames()
        for required in ("golang/ffi.go", "cycletls/_ffi.py", "hatch_build.py"):
            if not any(name.endswith("/" + required) for name in names):
                raise ValueError(f"{source.name} is missing {required}")
        if any("/zig-linux-" in name or "/continuum/" in name for name in names):
            raise ValueError(f"{source.name} includes build scratch or local state")
        print(f"Validated {source.name}: {source.stat().st_size:,} bytes")


if __name__ == "__main__":
    validate(Path(sys.argv[1]))
