"""Release archives must contain runtime libraries and exclude build scratch."""

import platform
import shutil
import tarfile
import zipfile
from pathlib import Path

from hatchling.builders.sdist import SdistBuilder
from hatchling.builders.wheel import WheelBuilder


def test_source_archive_excludes_downloaded_tools_and_local_reports(tmp_path):
    root = Path(__file__).resolve().parents[2]
    shutil.copy(root / "pyproject.toml", tmp_path)
    (tmp_path / "README.md").write_text("Release fixture")
    package = tmp_path / "cycletls"
    package.mkdir()
    (package / "__init__.py").write_text("__version__ = '0.0.4'")
    go = tmp_path / "golang"
    go.mkdir()
    (go / "ffi.go").write_text("package main")
    (go / "go.mod").write_text("module example.com/release")
    (tmp_path / "zig-linux-x86_64-0.13.0").mkdir()
    (tmp_path / "zig-linux-x86_64-0.13.0" / "zig").write_bytes(b"compiler scratch")
    (tmp_path / "cycletls-crash-report.md").write_text("Local incident notes")
    (tmp_path / "continuum").mkdir()
    (tmp_path / "continuum" / "state.json").write_text("{}")
    builder = SdistBuilder(str(tmp_path))
    archive = next(builder.build(directory=str(tmp_path / "output")))
    with tarfile.open(archive) as source:
        names = source.getnames()
    assert any(name.endswith("golang/ffi.go") for name in names)
    assert any(name.endswith("cycletls/__init__.py") for name in names)
    assert not any(
        "zig-linux" in name or "crash-report" in name or "continuum" in name for name in names
    )


def test_wheel_built_without_gitignore_includes_only_selected_native_library(tmp_path):
    root = Path(__file__).resolve().parents[2]
    for name in ("pyproject.toml", "hatch_build.py"):
        shutil.copy(root / name, tmp_path)
    (tmp_path / "README.md").write_text("Release fixture")
    package = tmp_path / "cycletls"
    package.mkdir()
    (package / "__init__.py").write_text("__version__ = '0.0.5'")
    native = package / "dist"
    native.mkdir()
    names = ["libcycletls.so", "libcycletls.dylib", "cycletls.dll"]
    for name in names:
        (native / name).write_bytes(b"fixture native artifact")
    selected = {"Linux": names[0], "Darwin": names[1], "Windows": names[2]}[platform.system()]
    wheel = next(WheelBuilder(str(tmp_path)).build(directory=str(tmp_path / "output")))
    with zipfile.ZipFile(wheel) as archive:
        bundled = [name for name in archive.namelist() if name.startswith("cycletls/dist/")]
    assert bundled == [f"cycletls/dist/{selected}"]
