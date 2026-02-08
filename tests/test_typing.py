"""Tests for PEP 561 py.typed marker and type annotation correctness."""

import os
import subprocess
import sys

import pytest


class TestPyTypedMarker:
    """Verify py.typed marker exists for PEP 561 compliance."""

    def test_py_typed_file_exists(self):
        """py.typed marker must exist in the cycletls package directory."""
        package_dir = os.path.dirname(os.path.dirname(__file__))
        py_typed_path = os.path.join(package_dir, "cycletls", "py.typed")
        assert os.path.exists(py_typed_path), f"py.typed not found at {py_typed_path}"

    def test_py_typed_file_is_empty(self):
        """py.typed should be an empty file (PEP 561 convention)."""
        package_dir = os.path.dirname(os.path.dirname(__file__))
        py_typed_path = os.path.join(package_dir, "cycletls", "py.typed")
        assert os.path.getsize(py_typed_path) == 0


class TestTypeAnnotations:
    """Verify type annotations are present and correct at runtime."""

    def test_cycleTLS_request_has_annotations(self):
        from cycletls.api import CycleTLS
        annotations = CycleTLS.request.__annotations__
        assert "method" in annotations
        assert "url" in annotations
        assert "return" in annotations

    def test_cycleTLS_get_has_annotations(self):
        from cycletls.api import CycleTLS
        annotations = CycleTLS.get.__annotations__
        assert "url" in annotations
        assert "return" in annotations

    def test_cycleTLS_post_has_annotations(self):
        from cycletls.api import CycleTLS
        annotations = CycleTLS.post.__annotations__
        assert "url" in annotations
        assert "data" in annotations
        assert "json_data" in annotations
        assert "json" in annotations
        assert "auth" in annotations
        assert "return" in annotations

    def test_cycleTLS_arequest_has_annotations(self):
        from cycletls.api import CycleTLS
        annotations = CycleTLS.arequest.__annotations__
        assert "method" in annotations
        assert "url" in annotations
        assert "json" in annotations
        assert "auth" in annotations
        assert "return" in annotations

    def test_cycleTLS_apost_has_annotations(self):
        from cycletls.api import CycleTLS
        annotations = CycleTLS.apost.__annotations__
        assert "url" in annotations
        assert "json" in annotations
        assert "auth" in annotations
        assert "return" in annotations

    def test_session_init_has_annotations(self):
        from cycletls.sessions import Session
        annotations = Session.__init__.__annotations__
        assert "base_url" in annotations
        assert "auth" in annotations

    def test_session_arequest_has_annotations(self):
        from cycletls.sessions import Session
        annotations = Session.arequest.__annotations__
        assert "method" in annotations
        assert "url" in annotations
        assert "json" in annotations
        assert "auth" in annotations
        assert "return" in annotations


class TestPyrightCheck:
    """Run pyright to validate type correctness (if available)."""

    @pytest.mark.skipif(
        subprocess.run(
            [sys.executable, "-m", "pyright", "--version"],
            capture_output=True,
        ).returncode != 0,
        reason="pyright not installed",
    )
    def test_pyright_passes_on_stub_file(self, tmp_path):
        """Create a small stub that uses the typed API and verify pyright accepts it."""
        stub = tmp_path / "check_types.py"
        stub.write_text(
            """\
from cycletls.api import CycleTLS
from cycletls.sessions import Session
from cycletls.schema import Response

def check_sync(client: CycleTLS) -> Response:
    return client.get("https://example.com", auth=("u", "p"))

def check_json(client: CycleTLS) -> Response:
    return client.post("https://example.com", json={"key": "val"})

def check_session() -> Session:
    return Session(base_url="https://api.example.com", auth=("u", "p"))

async def check_async(client: CycleTLS) -> Response:
    return await client.arequest("get", "https://example.com", auth=("u", "p"))
"""
        )
        result = subprocess.run(
            [sys.executable, "-m", "pyright", str(stub)],
            capture_output=True,
            text=True,
        )
        # Allow warnings but no errors
        assert "error" not in result.stdout.lower() or result.returncode == 0, (
            f"pyright found type errors:\n{result.stdout}\n{result.stderr}"
        )
