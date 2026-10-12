"""Regressions for notification cleanup and isolated backend routing."""

import asyncio
import os
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import ormsgpack
import pytest

import cycletls
from cycletls import _ffi
from cycletls.exceptions import CycleTLSError, CycleTLSWorkerDied


class NotifyLibrary:
    def __init__(self):
        self.cancelled = []
        self.write_fd = None

    def submitRequestAsyncWithNotify(self, buf, size, fd):
        self.write_fd = fd
        return 17

    def cancelAsyncRequest(self, handle):
        self.cancelled.append(handle)


@pytest.fixture
def notify_lib(monkeypatch):
    monkeypatch.setenv("CYCLETLS_BACKEND", "inprocess")
    lib = NotifyLibrary()
    monkeypatch.setattr(_ffi, "_load_library", lambda: lib)
    return lib


@pytest.mark.asyncio
async def test_notification_timeout_does_not_start_executor_reader(notify_lib, monkeypatch):
    loop = asyncio.get_running_loop()
    executor = Mock(side_effect=AssertionError("notification must not use a pool thread"))
    monkeypatch.setattr(loop, "run_in_executor", executor)
    with pytest.raises(asyncio.TimeoutError):
        await _ffi.send_request_async_callback({"requestId": "slow", "options": {}}, 0.01)
    assert notify_lib.cancelled == [17]
    with pytest.raises(OSError):
        os.fstat(notify_lib.write_fd)


@pytest.mark.asyncio
async def test_notification_cancellation_releases_handle(notify_lib):
    task = asyncio.create_task(_ffi.send_request_async_callback({"options": {}}, 10))
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert notify_lib.cancelled == [17]


@pytest.mark.asyncio
async def test_polling_timeout_releases_handle(monkeypatch, notify_lib):
    monkeypatch.setattr(_ffi, "_has_async_zerocopy_support", lambda: True)
    monkeypatch.setattr(_ffi, "submit_request_async_zerocopy", lambda payload: 17)
    monkeypatch.setattr(_ffi, "check_request_async_zerocopy", lambda handle: None)
    with pytest.raises(asyncio.TimeoutError):
        await _ffi.send_request_async({"options": {}}, timeout=0.001)
    assert notify_lib.cancelled == [17]


@pytest.fixture
def subprocess_backend(monkeypatch):
    monkeypatch.setenv("CYCLETLS_BACKEND", "subprocess")
    backend = SimpleNamespace(
        send_request=Mock(return_value={"Status": 200}),
        send_batch_request=Mock(return_value=[{"Status": 200}]),
        send_request_async=AsyncMock(return_value={"Status": 200}),
    )
    monkeypatch.setitem(sys.modules, "cycletls._subprocess", backend)
    monkeypatch.setattr(cycletls, "_subprocess", backend, raising=False)
    monkeypatch.setattr(_ffi, "_load_library", Mock(side_effect=AssertionError("host loaded Go")))
    return backend


def test_isolated_sync_route_does_not_load_go(subprocess_backend):
    assert _ffi.send_request({"options": {}}) == {"Status": 200}
    subprocess_backend.send_request.assert_called_once()


def test_isolated_batch_route_does_not_load_go(subprocess_backend):
    assert _ffi.send_batch_request([{"options": {}}]) == [{"Status": 200}]
    subprocess_backend.send_batch_request.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("callback", [False, True])
async def test_isolated_async_route_does_not_load_go(subprocess_backend, callback):
    if callback:
        assert _ffi._has_callback_support()
        result = await _ffi.send_request_async_callback({"options": {}}, 1)
    else:
        result = await _ffi.send_request_async({"options": {}}, timeout=1)
    assert result == {"Status": 200}
    subprocess_backend.send_request_async.assert_awaited_once()


def test_invalid_backend_fails_before_loading_go(monkeypatch):
    monkeypatch.setenv("CYCLETLS_BACKEND", "typo")
    monkeypatch.setattr(_ffi, "_load_library", Mock(side_effect=AssertionError("host loaded Go")))
    with pytest.raises(ValueError, match="CYCLETLS_BACKEND"):
        _ffi.send_request({})


@pytest.mark.asyncio
async def test_notification_success_preserves_binary_response(notify_lib):
    payload = {"Status": 200, "Body": b"\x00\xff"}
    packed = ormsgpack.packb(payload)
    buffer = _ffi._ffi.new("char[]", packed)
    notify_lib.freeString = Mock()

    def submit(buf, size, fd):
        notify_lib.write_fd = fd
        os.write(fd, b"\x01")
        return 17

    def result(handle, out_len):
        out_len[0] = len(packed)
        return buffer

    notify_lib.submitRequestAsyncWithNotify = submit
    notify_lib.getAsyncResult = result
    assert await _ffi.send_request_async_callback({"options": {}}) == payload
    notify_lib.freeString.assert_called_once_with(buffer)


@pytest.mark.asyncio
async def test_event_loop_without_readers_uses_polling(notify_lib, monkeypatch):
    loop = asyncio.get_running_loop()
    monkeypatch.setattr(loop, "add_reader", Mock(side_effect=NotImplementedError))
    poll = AsyncMock(return_value={"Status": 200})
    monkeypatch.setattr(_ffi, "send_request_async", poll)
    assert await _ffi.send_request_async_callback({"options": {}}, 1) == {"Status": 200}
    assert notify_lib.write_fd is None
    poll.assert_awaited_once()


def test_subprocess_mode_prevents_direct_host_library_load(monkeypatch):
    monkeypatch.setenv("CYCLETLS_BACKEND", "subprocess")
    with pytest.raises(CycleTLSError, match="inprocess"):
        _ffi._load_library()


@pytest.mark.parametrize("method", ["get", "batch"])
def test_public_sync_api_preserves_worker_death(monkeypatch, method):
    from cycletls import api

    failure = CycleTLSWorkerDied("worker exited")
    monkeypatch.setattr(api, "ffi_send_request", Mock(side_effect=failure))
    monkeypatch.setattr(api, "ffi_send_batch_request", Mock(side_effect=failure))
    with cycletls.CycleTLS() as client, pytest.raises(CycleTLSWorkerDied):
        if method == "get":
            client.get("https://example.com")
        else:
            client.batch([{"url": "https://example.com", "method": "GET"}])


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["aget", "abatch"])
async def test_public_async_api_preserves_worker_death(monkeypatch, method):
    from cycletls import api

    failure = CycleTLSWorkerDied("worker exited")
    monkeypatch.setattr(api, "_has_callback_support", lambda: False)
    monkeypatch.setattr(api, "ffi_send_request_async", AsyncMock(side_effect=failure))
    monkeypatch.setattr(api, "ffi_send_requests_batch", AsyncMock(side_effect=failure))
    async with cycletls.CycleTLS() as client:
        with pytest.raises(CycleTLSWorkerDied):
            if method == "aget":
                await client.aget("https://example.com")
            else:
                await client.abatch([{"url": "https://example.com", "method": "GET"}])
