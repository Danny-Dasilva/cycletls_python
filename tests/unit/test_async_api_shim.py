"""Tests for the async_api.py backward-compatibility shim (Phase 3).

Validates that AsyncCycleTLS is a subclass of CycleTLS whose async methods
delegate to the a-prefixed parent methods.
"""

import inspect
import pytest

from cycletls.async_api import (
    AsyncCycleTLS,
    async_delete,
    async_get,
    async_post,
    async_put,
)
from cycletls.api import CycleTLS


class TestAsyncCycleTLSIsSubclass:
    """AsyncCycleTLS should be a subclass of CycleTLS, not a standalone class."""

    def test_is_subclass(self):
        assert issubclass(AsyncCycleTLS, CycleTLS)

    def test_instance_is_cycleTLS(self):
        client = AsyncCycleTLS()
        assert isinstance(client, CycleTLS)


class TestAsyncMethodSignatures:
    """Verify that the shim overrides are async and have correct signatures."""

    def test_request_is_async(self):
        assert inspect.iscoroutinefunction(AsyncCycleTLS.request)

    def test_get_is_async(self):
        assert inspect.iscoroutinefunction(AsyncCycleTLS.get)

    def test_post_is_async(self):
        assert inspect.iscoroutinefunction(AsyncCycleTLS.post)

    def test_put_is_async(self):
        assert inspect.iscoroutinefunction(AsyncCycleTLS.put)

    def test_patch_is_async(self):
        assert inspect.iscoroutinefunction(AsyncCycleTLS.patch)

    def test_delete_is_async(self):
        assert inspect.iscoroutinefunction(AsyncCycleTLS.delete)

    def test_head_is_async(self):
        assert inspect.iscoroutinefunction(AsyncCycleTLS.head)

    def test_options_is_async(self):
        assert inspect.iscoroutinefunction(AsyncCycleTLS.options)

    def test_close_is_async(self):
        assert inspect.iscoroutinefunction(AsyncCycleTLS.close)


class TestConvenienceFunctions:
    """Test that module-level convenience functions exist and are async."""

    def test_async_get_is_coroutine(self):
        assert inspect.iscoroutinefunction(async_get)

    def test_async_post_is_coroutine(self):
        assert inspect.iscoroutinefunction(async_post)

    def test_async_put_is_coroutine(self):
        assert inspect.iscoroutinefunction(async_put)

    def test_async_delete_is_coroutine(self):
        assert inspect.iscoroutinefunction(async_delete)


class TestAllExports:
    """Test __all__ exports are correct."""

    def test_all_exports(self):
        from cycletls import async_api
        assert "AsyncCycleTLS" in async_api.__all__
        assert "async_get" in async_api.__all__
        assert "async_post" in async_api.__all__
        assert "async_put" in async_api.__all__
        assert "async_delete" in async_api.__all__


class TestNoLegacyImports:
    """Verify the shim does not import legacy heavy dependencies."""

    def test_no_ffi_import(self):
        """The shim should not import _ffi directly -- it delegates to parent."""
        import cycletls.async_api as mod
        source = inspect.getsource(mod)
        assert "from . import _ffi" not in source
        assert "from ._ffi" not in source

    def test_no_json_import(self):
        """The shim should not import json directly."""
        import cycletls.async_api as mod
        source = inspect.getsource(mod)
        assert "import json" not in source

    def test_no_urllib_import(self):
        """The shim should not import urllib directly."""
        import cycletls.async_api as mod
        source = inspect.getsource(mod)
        assert "import urllib" not in source
