"""Regression coverage for native-library selection during wheel builds."""

from pathlib import Path

import pytest

import hatch_build

PLATFORMS = [
    ("Linux", "x86_64", "libcycletls-linux-x64.so", "libcycletls.so", "manylinux2014_x86_64"),
    ("Linux", "aarch64", "libcycletls-linux-arm64.so", "libcycletls.so", "manylinux2014_aarch64"),
    (
        "Darwin",
        "x86_64",
        "libcycletls-darwin-x64.dylib",
        "libcycletls.dylib",
        "macosx_10_15_x86_64",
    ),
    ("Darwin", "arm64", "libcycletls-darwin-arm64.dylib", "libcycletls.dylib", "macosx_11_0_arm64"),
    ("Windows", "AMD64", "cycletls-win-x64.dll", "cycletls.dll", "win_amd64"),
    ("Windows", "ARM64", "cycletls-win-arm64.dll", "cycletls.dll", "win_arm64"),
]


def make_hook(tmp_path, monkeypatch, system, machine):
    monkeypatch.setattr(hatch_build.platform, "system", lambda: system)
    monkeypatch.setattr(hatch_build.platform, "machine", lambda: machine)
    return hatch_build.CycleTLSBuildHook(
        root=str(tmp_path),
        config={},
        build_config=None,
        metadata=None,
        directory=str(tmp_path / "wheel-output"),
        target_name="wheel",
    )


def add_artifact(tmp_path, name):
    artifact = tmp_path / "cycletls" / "dist" / name
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(b"native artifact")
    return artifact


@pytest.mark.parametrize("system,machine,qualified,generic,tag", PLATFORMS)
def test_generic_only_release_library_is_included(
    tmp_path, monkeypatch, system, machine, qualified, generic, tag
):
    hook = make_hook(tmp_path, monkeypatch, system, machine)
    binary = add_artifact(tmp_path, generic)
    header = add_artifact(tmp_path, Path(generic).with_suffix(".h").name)
    build_data = {}

    hook.initialize("standard", build_data)

    assert build_data["tag"] == f"py3-none-{tag}"
    assert build_data["force_include"] == {
        str(binary): f"cycletls/dist/{binary.name}",
        str(header): f"cycletls/dist/{header.name}",
    }


@pytest.mark.parametrize("system,machine,qualified,generic,tag", PLATFORMS)
def test_qualified_library_has_priority_and_only_its_header_is_included(
    tmp_path, monkeypatch, system, machine, qualified, generic, tag
):
    hook = make_hook(tmp_path, monkeypatch, system, machine)
    binary = add_artifact(tmp_path, qualified)
    header = add_artifact(tmp_path, Path(qualified).with_suffix(".h").name)
    add_artifact(tmp_path, generic)
    add_artifact(tmp_path, Path(generic).with_suffix(".h").name)
    for _, _, foreign_qualified, foreign_generic, _ in PLATFORMS:
        add_artifact(tmp_path, foreign_qualified)
        add_artifact(tmp_path, foreign_generic)
    build_data = {}

    hook.initialize("standard", build_data)

    assert build_data["force_include"] == {
        str(binary): f"cycletls/dist/{binary.name}",
        str(header): f"cycletls/dist/{header.name}",
    }


@pytest.mark.parametrize("system,machine,qualified,generic,tag", PLATFORMS)
def test_missing_native_library_fails_wheel_build(
    tmp_path, monkeypatch, system, machine, qualified, generic, tag
):
    hook = make_hook(tmp_path, monkeypatch, system, machine)

    with pytest.raises(RuntimeError, match="native library") as error:
        hook.initialize("standard", {})

    assert qualified in str(error.value)
    assert generic in str(error.value)


def test_foreign_platform_library_cannot_satisfy_wheel_build(tmp_path, monkeypatch):
    hook = make_hook(tmp_path, monkeypatch, "Linux", "x86_64")
    add_artifact(tmp_path, "libcycletls-darwin-arm64.dylib")
    add_artifact(tmp_path, "cycletls.dll")

    with pytest.raises(RuntimeError, match="native library"):
        hook.initialize("standard", {})


def test_matching_header_is_optional(tmp_path, monkeypatch):
    hook = make_hook(tmp_path, monkeypatch, "Linux", "x86_64")
    binary = add_artifact(tmp_path, "libcycletls.so")
    add_artifact(tmp_path, "cycletls.h")
    build_data = {}

    hook.initialize("standard", build_data)

    assert build_data["force_include"] == {str(binary): "cycletls/dist/libcycletls.so"}


def test_unsupported_platform_fails_wheel_build(tmp_path, monkeypatch):
    hook = make_hook(tmp_path, monkeypatch, "FreeBSD", "x86_64")

    with pytest.raises(RuntimeError, match="Unsupported platform"):
        hook.initialize("standard", {})


def test_directory_named_like_library_cannot_satisfy_wheel_build(tmp_path, monkeypatch):
    hook = make_hook(tmp_path, monkeypatch, "Linux", "x86_64")
    (tmp_path / "cycletls" / "dist" / "libcycletls.so").mkdir(parents=True)

    with pytest.raises(RuntimeError, match="native library"):
        hook.initialize("standard", {})
