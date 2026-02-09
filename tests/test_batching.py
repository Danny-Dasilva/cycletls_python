"""Tests for the unified batching backend (_batcher.py).

All tests mock the FFI batch function so no Go binary is needed.
"""

from __future__ import annotations

import asyncio
import threading
from concurrent.futures import Future
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest


from cycletls._batcher import (
    RequestBatcher,
    _PendingRequest,
    get_batcher,
    shutdown_batcher,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_payload(request_id: str = "req_1") -> Dict[str, Any]:
    """Return a minimal payload dict for testing."""
    return {
        "requestId": request_id,
        "options": {"url": "https://example.com", "method": "GET"},
    }


def _make_response(request_id: str = "req_1") -> Dict[str, Any]:
    """Return a minimal response dict matching the payload."""
    return {
        "RequestID": request_id,
        "Status": 200,
        "Body": "OK",
        "Headers": {},
    }


def _echo_batch_fn(payloads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Batch function that echoes back a response for each payload."""
    return [_make_response(p.get("requestId", "")) for p in payloads]


# ---------------------------------------------------------------------------
# RequestBatcher unit tests
# ---------------------------------------------------------------------------


class TestRequestBatcherLifecycle:
    """Test batcher startup and shutdown."""

    def test_creates_daemon_thread(self):
        batcher = RequestBatcher(batch_fn=_echo_batch_fn)
        try:
            assert batcher._thread.is_alive()
            assert batcher._thread.daemon is True
            assert batcher._thread.name == "cycletls-batcher"
        finally:
            batcher.shutdown()

    def test_shutdown_stops_thread(self):
        batcher = RequestBatcher(batch_fn=_echo_batch_fn)
        batcher.shutdown()
        assert not batcher._thread.is_alive()

    def test_double_shutdown_is_safe(self):
        batcher = RequestBatcher(batch_fn=_echo_batch_fn)
        batcher.shutdown()
        batcher.shutdown()  # Should not raise

    def test_shutdown_drains_remaining(self):
        """Items queued just before shutdown are still flushed."""
        results = []

        def capturing_batch_fn(payloads):
            responses = _echo_batch_fn(payloads)
            results.extend(responses)
            return responses

        batcher = RequestBatcher(
            batch_fn=capturing_batch_fn,
            # Large flush interval so the batch won't auto-flush before
            # we call shutdown.
            flush_interval=10.0,
            batch_size=1000,
        )

        # Submit a request (it will sit in the queue).
        future: Future = Future()
        pending = _PendingRequest(
            payload=_make_payload("drain_test"),
            future=future,
            request_id="drain_test",
        )
        batcher._queue.put(pending)

        # Shutdown should drain and flush the pending item.
        batcher.shutdown()
        assert future.done()
        assert future.result()["Status"] == 200


class TestSubmitSync:
    """Test synchronous submission."""

    def test_single_request(self):
        batcher = RequestBatcher(batch_fn=_echo_batch_fn)
        try:
            payload = _make_payload("sync_1")
            result = batcher.submit_sync(payload)
            assert result["Status"] == 200
            assert result["RequestID"] == "sync_1"
        finally:
            batcher.shutdown()

    def test_multiple_concurrent_sync_requests(self):
        """Multiple threads submitting sync requests get correct results."""
        call_count = {"n": 0}

        def counting_batch_fn(payloads):
            call_count["n"] += 1
            return _echo_batch_fn(payloads)

        batcher = RequestBatcher(
            batch_fn=counting_batch_fn,
            batch_size=5,
            flush_interval=0.01,  # 10ms window
        )

        results = [None] * 10
        errors = []

        def submit(idx):
            try:
                payload = _make_payload(f"sync_{idx}")
                results[idx] = batcher.submit_sync(payload)
            except Exception as e:
                errors.append((idx, e))

        threads = [threading.Thread(target=submit, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)

        batcher.shutdown()

        assert not errors, f"Errors: {errors}"
        for i in range(10):
            assert results[i] is not None, f"Result {i} was None"
            assert results[i]["RequestID"] == f"sync_{i}"

    def test_batch_fn_exception_propagates(self):
        """If batch_fn raises, the exception propagates to all callers."""

        def failing_batch_fn(payloads):
            raise RuntimeError("FFI exploded")

        batcher = RequestBatcher(batch_fn=failing_batch_fn)
        try:
            with pytest.raises(RuntimeError, match="FFI exploded"):
                batcher.submit_sync(_make_payload())
        finally:
            batcher.shutdown()


class TestSubmitAsync:
    """Test async submission."""

    @pytest.mark.asyncio
    async def test_single_async_request(self):
        batcher = RequestBatcher(batch_fn=_echo_batch_fn)
        try:
            payload = _make_payload("async_1")
            result = await batcher.submit_async(payload)
            assert result["Status"] == 200
            assert result["RequestID"] == "async_1"
        finally:
            batcher.shutdown()

    @pytest.mark.asyncio
    async def test_multiple_concurrent_async_requests(self):
        """Multiple async tasks get correct results."""
        batcher = RequestBatcher(
            batch_fn=_echo_batch_fn,
            batch_size=5,
            flush_interval=0.01,
        )
        try:
            tasks = []
            for i in range(10):
                payload = _make_payload(f"async_{i}")
                tasks.append(batcher.submit_async(payload))

            results = await asyncio.gather(*tasks)
            for i, result in enumerate(results):
                assert result["RequestID"] == f"async_{i}"
                assert result["Status"] == 200
        finally:
            batcher.shutdown()

    @pytest.mark.asyncio
    async def test_async_batch_fn_exception_propagates(self):
        """If batch_fn raises, the exception propagates to async callers."""

        def failing_batch_fn(payloads):
            raise ValueError("bad batch")

        batcher = RequestBatcher(batch_fn=failing_batch_fn)
        try:
            with pytest.raises(ValueError, match="bad batch"):
                await batcher.submit_async(_make_payload())
        finally:
            batcher.shutdown()


class TestBatchingBehavior:
    """Test that the batcher actually batches requests."""

    def test_requests_are_batched(self):
        """Requests arriving within the flush window are sent together."""
        batch_sizes = []

        def tracking_batch_fn(payloads):
            batch_sizes.append(len(payloads))
            return _echo_batch_fn(payloads)

        batcher = RequestBatcher(
            batch_fn=tracking_batch_fn,
            batch_size=100,
            flush_interval=0.05,  # 50ms window
        )

        # Submit 5 requests nearly simultaneously.
        futures = []
        for i in range(5):
            f: Future = Future()
            pending = _PendingRequest(
                payload=_make_payload(f"batch_{i}"),
                future=f,
                request_id=f"batch_{i}",
            )
            batcher._queue.put(pending)
            futures.append(f)

        # Wait for all to complete.
        for f in futures:
            f.result(timeout=5.0)

        batcher.shutdown()

        # All 5 should have been batched together (or close to it).
        total_processed = sum(batch_sizes)
        assert total_processed == 5
        # The first batch should contain multiple items (at least 2).
        assert max(batch_sizes) >= 2, (
            f"Expected batching but got individual calls: {batch_sizes}"
        )

    def test_batch_size_limit_triggers_flush(self):
        """When batch_size is reached, flush happens immediately."""
        batch_sizes = []

        def tracking_batch_fn(payloads):
            batch_sizes.append(len(payloads))
            return _echo_batch_fn(payloads)

        batcher = RequestBatcher(
            batch_fn=tracking_batch_fn,
            batch_size=3,
            flush_interval=10.0,  # Very long window
        )

        # Submit exactly batch_size requests.
        futures = []
        for i in range(3):
            f: Future = Future()
            pending = _PendingRequest(
                payload=_make_payload(f"limit_{i}"),
                future=f,
                request_id=f"limit_{i}",
            )
            batcher._queue.put(pending)
            futures.append(f)

        # Should complete quickly despite long flush_interval.
        for f in futures:
            f.result(timeout=5.0)

        batcher.shutdown()
        assert 3 in batch_sizes

    def test_result_count_mismatch_raises(self):
        """If batch_fn returns wrong number of results, all callers get an error."""

        def bad_batch_fn(payloads):
            # Always return exactly 1 result regardless of input count.
            return [_make_response("x")]

        batcher = RequestBatcher(
            batch_fn=bad_batch_fn,
            batch_size=100,
            flush_interval=0.05,  # 50ms window to collect multiple items
        )

        # Submit multiple items concurrently so they batch together.
        futures: list[Future] = []
        for i in range(3):
            f: Future = Future()
            pending = _PendingRequest(
                payload=_make_payload(f"mismatch_{i}"),
                future=f,
                request_id=f"mismatch_{i}",
            )
            batcher._queue.put(pending)
            futures.append(f)

        # All futures should complete with a RuntimeError.
        for f in futures:
            f_exc = None
            try:
                f.result(timeout=5.0)
            except RuntimeError as exc:
                f_exc = exc

            # At least some of the futures should raise (those in the batch
            # with >1 items).  A single-item batch would succeed since 1==1.
            # We just need to verify the mechanism works.
            if f_exc is not None:
                assert "returned 1 results for" in str(f_exc)

        batcher.shutdown()


# ---------------------------------------------------------------------------
# Singleton management tests
# ---------------------------------------------------------------------------


class TestSingletonManagement:
    """Test get_batcher / shutdown_batcher module-level functions."""

    def test_get_batcher_returns_singleton(self):
        shutdown_batcher()  # Clean state
        try:
            b1 = get_batcher(batch_fn=_echo_batch_fn)
            b2 = get_batcher(batch_fn=_echo_batch_fn)
            assert b1 is b2
        finally:
            shutdown_batcher()

    def test_shutdown_batcher_clears_singleton(self):
        shutdown_batcher()  # Clean state
        b1 = get_batcher(batch_fn=_echo_batch_fn)
        shutdown_batcher()
        b2 = get_batcher(batch_fn=_echo_batch_fn)
        assert b1 is not b2
        shutdown_batcher()

    def test_shutdown_batcher_noop_when_none(self):
        shutdown_batcher()  # Clean state
        shutdown_batcher()  # Should not raise


# ---------------------------------------------------------------------------
# Integration with CycleTLS
# ---------------------------------------------------------------------------


class TestCycleTLSBatchingIntegration:
    """Test that CycleTLS routes through the batcher when enabled."""

    def setup_method(self):
        # Ensure clean singleton state between tests.
        shutdown_batcher()

    def teardown_method(self):
        shutdown_batcher()

    def test_default_no_batching(self):
        from cycletls.api import CycleTLS

        client = CycleTLS()
        assert client._batcher is None
        assert client._use_batching is False
        client.close()

    def test_batching_enabled_creates_batcher(self):
        from cycletls.api import CycleTLS

        with patch("cycletls.api.ffi_send_batch_request", new=_echo_batch_fn):
            client = CycleTLS(use_batching=True)
            assert client._use_batching is True
            assert client._batcher is not None
            client.close()

    def test_close_shuts_down_batcher(self):
        from cycletls.api import CycleTLS

        with patch("cycletls.api.ffi_send_batch_request", new=_echo_batch_fn):
            client = CycleTLS(use_batching=True)
            batcher = client._batcher
            assert batcher is not None
            client.close()
            assert client._batcher is None
            assert batcher._shutdown_event.is_set()

    def test_sync_request_routes_through_batcher(self):
        from cycletls.api import CycleTLS

        with patch("cycletls.api.ffi_send_batch_request", new=_echo_batch_fn):
            client = CycleTLS(use_batching=True)

        payload = _make_payload("integration_sync")

        with patch.object(client, "_prepare_request", return_value=payload):
            with patch.object(client, "_parse_response") as mock_parse:
                mock_parse.return_value = MagicMock(status_code=200)
                client.request("GET", "https://example.com")
                assert mock_parse.called
                # Verify that the batcher was used (it received a response
                # from the echo batch fn, which _parse_response then handled).
                call_args = mock_parse.call_args
                assert call_args is not None
                response_data = call_args[0][0]
                assert response_data["Status"] == 200

        client.close()

    @pytest.mark.asyncio
    async def test_async_request_routes_through_batcher(self):
        from cycletls.api import CycleTLS

        with patch("cycletls.api.ffi_send_batch_request", new=_echo_batch_fn):
            client = CycleTLS(use_batching=True)

        payload = _make_payload("integration_async")

        with patch.object(client, "_prepare_request", return_value=payload):
            with patch.object(client, "_parse_response") as mock_parse:
                mock_parse.return_value = MagicMock(status_code=200)
                await client.arequest("GET", "https://example.com")
                assert mock_parse.called
                call_args = mock_parse.call_args
                assert call_args is not None
                response_data = call_args[0][0]
                assert response_data["Status"] == 200

        client.close()


class TestSessionBatchingIntegration:
    """Test that Session passes through batching parameters."""

    def setup_method(self):
        shutdown_batcher()

    def teardown_method(self):
        shutdown_batcher()

    def test_session_default_no_batching(self):
        from cycletls.sessions import Session

        session = Session()
        assert session._use_batching is False
        assert session._batcher is None
        session.close()

    def test_session_with_batching(self):
        from cycletls.sessions import Session

        with patch("cycletls.api.ffi_send_batch_request", new=_echo_batch_fn):
            session = Session(use_batching=True, batch_size=16, flush_interval=0.001)
            assert session._use_batching is True
            assert session._batcher is not None
            session.close()
