"""Unified batching backend for CycleTLS.

Collects individual requests from sync and async callers into micro-batches
and sends them through the batch FFI path for optimal throughput. A background
daemon thread drains the queue either when ``batch_size`` items have
accumulated or after a short ``flush_interval`` timeout -- whichever comes
first.

Sync callers block on a :class:`concurrent.futures.Future`; async callers
``await`` it via :func:`asyncio.wrap_future`.

The batcher is opt-in (``use_batching=True`` on CycleTLS/Session) and
completely transparent -- callers get back the same ``Dict[str, Any]``
response payload they would from the direct FFI path.
"""

from __future__ import annotations

import asyncio
import atexit
import logging
import queue
import threading
from concurrent.futures import Future
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal data structures
# ---------------------------------------------------------------------------


@dataclass
class _PendingRequest:
    """A single queued request waiting to be batched."""

    payload: Dict[str, Any]
    future: Future  # type: ignore[type-arg]
    request_id: str = ""


# ---------------------------------------------------------------------------
# RequestBatcher
# ---------------------------------------------------------------------------

# Default tuning knobs
_DEFAULT_BATCH_SIZE = 32
_DEFAULT_FLUSH_INTERVAL = 0.0001  # 100 microseconds


class RequestBatcher:
    """Collects requests and dispatches them as FFI batches.

    Parameters
    ----------
    batch_fn:
        The FFI batch function to call.  Signature must be
        ``(list[dict]) -> list[dict]``.  Typically
        :func:`cycletls._ffi.send_batch_request`.
    batch_size:
        Maximum number of requests to accumulate before flushing.
    flush_interval:
        Maximum time (seconds) to wait for more requests before
        flushing a partial batch.  Defaults to 100 us.
    """

    def __init__(
        self,
        batch_fn: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]],
        batch_size: int = _DEFAULT_BATCH_SIZE,
        flush_interval: float = _DEFAULT_FLUSH_INTERVAL,
    ) -> None:
        self._batch_fn = batch_fn
        self._batch_size = batch_size
        self._flush_interval = flush_interval

        # Unbounded queue -- producers never block.
        self._queue: queue.Queue[Optional[_PendingRequest]] = queue.Queue()

        self._shutdown_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name="cycletls-batcher",
            daemon=True,
        )
        self._thread.start()

        # Best-effort cleanup when the interpreter exits.
        atexit.register(self.shutdown)
        logger.debug(
            "RequestBatcher started (batch_size=%d, flush_interval=%.6fs)",
            batch_size,
            flush_interval,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def submit_sync(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a request and block until the result is ready.

        Parameters
        ----------
        payload:
            The prepared FFI payload (as returned by
            ``CycleTLS._prepare_request``).

        Returns
        -------
        Dict[str, Any]
            Raw response dictionary from the FFI layer.
        """
        future: Future[Dict[str, Any]] = Future()
        pending = _PendingRequest(
            payload=payload,
            future=future,
            request_id=payload.get("requestId", ""),
        )
        self._queue.put(pending)
        return future.result()  # blocks

    async def submit_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a request and await the result.

        Uses :func:`asyncio.wrap_future` to bridge the
        :class:`concurrent.futures.Future` into the running event loop.
        """
        future: Future[Dict[str, Any]] = Future()
        pending = _PendingRequest(
            payload=payload,
            future=future,
            request_id=payload.get("requestId", ""),
        )
        self._queue.put(pending)
        loop = asyncio.get_running_loop()
        return await asyncio.wrap_future(future, loop=loop)

    def shutdown(self) -> None:
        """Signal the background thread to stop and wait for it."""
        if self._shutdown_event.is_set():
            return
        logger.debug("RequestBatcher shutting down")
        self._shutdown_event.set()
        # Send a sentinel so the thread wakes up if it's blocking on get().
        self._queue.put(None)
        self._thread.join(timeout=2.0)

    # ------------------------------------------------------------------
    # Background thread
    # ------------------------------------------------------------------

    def _run(self) -> None:
        """Drain the queue in batches until shutdown."""
        while not self._shutdown_event.is_set():
            batch = self._collect_batch()
            if batch:
                self._flush(batch)

        # Drain any remaining items after shutdown signal.
        remaining = self._drain_remaining()
        if remaining:
            self._flush(remaining)

    def _collect_batch(self) -> List[_PendingRequest]:
        """Block until at least one request arrives, then greedily collect
        up to ``batch_size`` items within ``flush_interval``."""
        batch: List[_PendingRequest] = []

        # Block indefinitely for the first item.
        try:
            first = self._queue.get(timeout=1.0)
        except queue.Empty:
            return batch
        if first is None:
            # Sentinel -- shutdown requested.
            return batch
        batch.append(first)

        # Greedily drain more items up to batch_size, within flush_interval.
        import time

        deadline = time.monotonic() + self._flush_interval
        while len(batch) < self._batch_size:
            remaining_time = deadline - time.monotonic()
            if remaining_time <= 0:
                break
            try:
                item = self._queue.get(timeout=remaining_time)
            except queue.Empty:
                break
            if item is None:
                # Sentinel -- stop collecting but still flush what we have.
                break
            batch.append(item)

        return batch

    def _drain_remaining(self) -> List[_PendingRequest]:
        """Non-blocking drain of anything left in the queue."""
        items: List[_PendingRequest] = []
        while True:
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                break
            if item is not None:
                items.append(item)
        return items

    def _flush(self, batch: List[_PendingRequest]) -> None:
        """Send a batch through the FFI and distribute results."""
        payloads = [p.payload for p in batch]
        logger.debug("Flushing batch of %d requests", len(payloads))

        try:
            results = self._batch_fn(payloads)
        except Exception as exc:
            # Propagate the error to every waiting caller.
            for pending in batch:
                if not pending.future.done():
                    pending.future.set_exception(exc)
            return

        # Distribute results back to callers.
        if len(results) != len(batch):
            exc = RuntimeError(
                f"Batch FFI returned {len(results)} results for "
                f"{len(batch)} requests"
            )
            for pending in batch:
                if not pending.future.done():
                    pending.future.set_exception(exc)
            return

        for pending, result in zip(batch, results):
            if not pending.future.done():
                pending.future.set_result(result)


# ---------------------------------------------------------------------------
# Module-level singleton management
# ---------------------------------------------------------------------------

_global_batcher: Optional[RequestBatcher] = None
_global_lock = threading.Lock()


def get_batcher(
    batch_fn: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]],
    batch_size: int = _DEFAULT_BATCH_SIZE,
    flush_interval: float = _DEFAULT_FLUSH_INTERVAL,
) -> RequestBatcher:
    """Return (or create) the module-level singleton batcher.

    The first call creates the batcher; subsequent calls return the same
    instance (the parameters are only used on first creation).
    """
    global _global_batcher
    if _global_batcher is not None:
        return _global_batcher
    with _global_lock:
        # Double-checked locking.
        if _global_batcher is not None:
            return _global_batcher
        _global_batcher = RequestBatcher(
            batch_fn=batch_fn,
            batch_size=batch_size,
            flush_interval=flush_interval,
        )
        return _global_batcher


def shutdown_batcher() -> None:
    """Shut down the global batcher if one exists."""
    global _global_batcher
    with _global_lock:
        if _global_batcher is not None:
            _global_batcher.shutdown()
            _global_batcher = None
