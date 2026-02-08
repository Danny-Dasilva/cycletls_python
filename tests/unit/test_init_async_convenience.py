"""
Tests for Phase 4: module-level async convenience functions in __init__.py.

Verifies that aget, apost, aput, apatch, adelete, ahead, aoptions, and
async_request use CycleTLS (not AsyncCycleTLS) and call a-prefixed methods.
"""

import ast
import inspect
import textwrap

import pytest

import cycletls


class TestAsyncConvenienceFunctionsUseCorrectClass:
    """Verify module-level async functions use CycleTLS, not AsyncCycleTLS."""

    def _get_source(self, func):
        """Get dedented source of a function."""
        return textwrap.dedent(inspect.getsource(func))

    def test_async_request_uses_cycletls(self):
        """async_request() should use CycleTLS(), not AsyncCycleTLS()."""
        src = self._get_source(cycletls.async_request)
        assert "CycleTLS()" in src, "async_request should instantiate CycleTLS()"
        assert "AsyncCycleTLS()" not in src, "async_request should NOT use AsyncCycleTLS()"

    def test_async_request_calls_arequest(self):
        """async_request() should call client.arequest(), not client.request()."""
        src = self._get_source(cycletls.async_request)
        assert "client.arequest(" in src, "async_request should call client.arequest()"
        # Ensure it does NOT call the sync client.request() (but "arequest" contains "request")
        # Check there's no bare "client.request(" without the "a" prefix
        assert "client.request(" not in src.replace("client.arequest(", ""), (
            "async_request should not call client.request() (sync)"
        )

    def test_aget_uses_cycletls(self):
        """aget() should use CycleTLS(), not AsyncCycleTLS()."""
        src = self._get_source(cycletls.aget)
        assert "CycleTLS()" in src
        assert "AsyncCycleTLS()" not in src

    def test_aget_calls_aget(self):
        """aget() should call client.aget(), not client.get()."""
        src = self._get_source(cycletls.aget)
        assert "client.aget(" in src
        # Ensure no bare client.get( call
        assert "client.get(" not in src.replace("client.aget(", "")

    def test_apost_uses_cycletls(self):
        """apost() should use CycleTLS(), not AsyncCycleTLS()."""
        src = self._get_source(cycletls.apost)
        assert "CycleTLS()" in src
        assert "AsyncCycleTLS()" not in src

    def test_apost_calls_apost(self):
        """apost() should call client.apost(), not client.post()."""
        src = self._get_source(cycletls.apost)
        assert "client.apost(" in src
        assert "client.post(" not in src.replace("client.apost(", "")

    def test_aput_uses_cycletls(self):
        """aput() should use CycleTLS(), not AsyncCycleTLS()."""
        src = self._get_source(cycletls.aput)
        assert "CycleTLS()" in src
        assert "AsyncCycleTLS()" not in src

    def test_aput_calls_aput(self):
        """aput() should call client.aput(), not client.put()."""
        src = self._get_source(cycletls.aput)
        assert "client.aput(" in src
        assert "client.put(" not in src.replace("client.aput(", "")

    def test_apatch_uses_cycletls(self):
        """apatch() should use CycleTLS(), not AsyncCycleTLS()."""
        src = self._get_source(cycletls.apatch)
        assert "CycleTLS()" in src
        assert "AsyncCycleTLS()" not in src

    def test_apatch_calls_apatch(self):
        """apatch() should call client.apatch(), not client.patch()."""
        src = self._get_source(cycletls.apatch)
        assert "client.apatch(" in src
        assert "client.patch(" not in src.replace("client.apatch(", "")

    def test_adelete_uses_cycletls(self):
        """adelete() should use CycleTLS(), not AsyncCycleTLS()."""
        src = self._get_source(cycletls.adelete)
        assert "CycleTLS()" in src
        assert "AsyncCycleTLS()" not in src

    def test_adelete_calls_adelete(self):
        """adelete() should call client.adelete(), not client.delete()."""
        src = self._get_source(cycletls.adelete)
        assert "client.adelete(" in src
        assert "client.delete(" not in src.replace("client.adelete(", "")

    def test_ahead_uses_cycletls(self):
        """ahead() should use CycleTLS(), not AsyncCycleTLS()."""
        src = self._get_source(cycletls.ahead)
        assert "CycleTLS()" in src
        assert "AsyncCycleTLS()" not in src

    def test_ahead_calls_ahead(self):
        """ahead() should call client.ahead(), not client.head()."""
        src = self._get_source(cycletls.ahead)
        assert "client.ahead(" in src
        assert "client.head(" not in src.replace("client.ahead(", "")

    def test_aoptions_uses_cycletls(self):
        """aoptions() should use CycleTLS(), not AsyncCycleTLS()."""
        src = self._get_source(cycletls.aoptions)
        assert "CycleTLS()" in src
        assert "AsyncCycleTLS()" not in src

    def test_aoptions_calls_aoptions(self):
        """aoptions() should call client.aoptions(), not client.options()."""
        src = self._get_source(cycletls.aoptions)
        assert "client.aoptions(" in src
        assert "client.options(" not in src.replace("client.aoptions(", "")


class TestAsyncCycleTLSStillImportable:
    """Verify AsyncCycleTLS is still re-exported for backward compatibility."""

    def test_async_cycletls_in_all(self):
        """AsyncCycleTLS should still be in __all__."""
        assert "AsyncCycleTLS" in cycletls.__all__

    def test_async_cycletls_importable(self):
        """AsyncCycleTLS should be importable from cycletls."""
        from cycletls import AsyncCycleTLS
        assert AsyncCycleTLS is not None

    def test_async_cycletls_importable_from_async_api(self):
        """AsyncCycleTLS should be importable from cycletls.async_api."""
        from cycletls.async_api import AsyncCycleTLS
        assert AsyncCycleTLS is not None


class TestSyncFunctionsUnchanged:
    """Verify sync convenience functions were NOT modified."""

    def _get_source(self, func):
        return textwrap.dedent(inspect.getsource(func))

    def test_get_is_sync(self):
        """cycletls.get should remain a sync function."""
        assert not inspect.iscoroutinefunction(cycletls.get)

    def test_post_is_sync(self):
        """cycletls.post should remain a sync function."""
        assert not inspect.iscoroutinefunction(cycletls.post)

    def test_request_is_sync(self):
        """cycletls.request should remain a sync function."""
        assert not inspect.iscoroutinefunction(cycletls.request)

    def test_sync_get_uses_global_session(self):
        """cycletls.get should still use get_global_session(), not CycleTLS()."""
        src = self._get_source(cycletls.get)
        assert "get_global_session()" in src


class TestAsyncFunctionsAreCoroutines:
    """Verify all async convenience functions are actually coroutine functions."""

    def test_async_request_is_coroutine(self):
        assert inspect.iscoroutinefunction(cycletls.async_request)

    def test_aget_is_coroutine(self):
        assert inspect.iscoroutinefunction(cycletls.aget)

    def test_apost_is_coroutine(self):
        assert inspect.iscoroutinefunction(cycletls.apost)

    def test_aput_is_coroutine(self):
        assert inspect.iscoroutinefunction(cycletls.aput)

    def test_apatch_is_coroutine(self):
        assert inspect.iscoroutinefunction(cycletls.apatch)

    def test_adelete_is_coroutine(self):
        assert inspect.iscoroutinefunction(cycletls.adelete)

    def test_ahead_is_coroutine(self):
        assert inspect.iscoroutinefunction(cycletls.ahead)

    def test_aoptions_is_coroutine(self):
        assert inspect.iscoroutinefunction(cycletls.aoptions)
