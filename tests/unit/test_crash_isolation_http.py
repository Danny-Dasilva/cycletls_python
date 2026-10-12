"""Verify both backends against a local server and a rebuilt Go library."""

import asyncio
import os
import signal
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from cycletls import CycleTLS, CycleTLSWorkerDied, _ffi, _subprocess


@pytest.fixture
def slow_started():
    return threading.Event()


@pytest.fixture
def local_url(slow_started):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/slow":
                slow_started.set()
                time.sleep(0.3)
            body = b"isolated\x00\xff"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}/"
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.fixture
def isolated(monkeypatch):
    _subprocess.close()
    monkeypatch.setenv("CYCLETLS_BACKEND", "subprocess")
    monkeypatch.setattr(_ffi, "_lib", None)
    yield
    assert _ffi._lib is None, "Go must stay outside the Python application"
    _subprocess.close()


def test_isolated_sync_and_batch_use_real_go(local_url, isolated):
    with CycleTLS() as client:
        assert client.get(local_url).content == b"isolated\x00\xff"
        responses = client.batch([{"url": local_url}, {"url": local_url}])
        assert [r.content for r in responses] == [b"isolated\x00\xff"] * 2


@pytest.mark.asyncio
async def test_isolated_async_and_batch_use_real_go(local_url, isolated):
    async with CycleTLS() as client:
        responses = await asyncio.gather(*(client.aget(local_url) for _ in range(4)))
        assert [r.content for r in responses] == [b"isolated\x00\xff"] * 4
        responses = await client.abatch([{"url": local_url}, {"url": local_url}])
        assert [r.content for r in responses] == [b"isolated\x00\xff"] * 2


@pytest.mark.asyncio
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX fatal signal")
async def test_real_go_worker_abort_preserves_host_and_restarts(local_url, slow_started, isolated):
    async with CycleTLS() as client:
        task = asyncio.create_task(client.aget(local_url + "slow"))
        assert await asyncio.to_thread(slow_started.wait, 5), "Worker did not reach the server"
        os.kill(_subprocess._backend._process.pid, signal.SIGABRT)
        with pytest.raises(CycleTLSWorkerDied):
            await task
        assert (await client.aget(local_url)).content == b"isolated\x00\xff"


@pytest.mark.asyncio
async def test_inprocess_notification_uses_real_go(local_url, monkeypatch):
    monkeypatch.setenv("CYCLETLS_BACKEND", "inprocess")
    if _ffi.os.name == "nt":
        pytest.skip("Windows uses the polling async API")
    assert _ffi._has_callback_support(), "Build the updated Go shared library"
    with CycleTLS() as client:
        response = await client.aget(local_url)
        assert response.content == b"isolated\x00\xff"


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX notification descriptors")
def test_c_shared_notification_after_cancellation_survives_sigpipe(local_url):
    script = """
import os, signal, sys, time
import ormsgpack
from cycletls import _ffi
signal.signal(signal.SIGPIPE, signal.SIG_DFL)
lib = _ffi._load_library()
read_fd, write_fd = os.pipe()
data = ormsgpack.packb({'requestId': 'cancelled', 'options': {
    'url': sys.argv[1] + 'slow', 'method': 'GET', 'timeout': 2}})
handle = lib.submitRequestAsyncWithNotify(_ffi._ffi.from_buffer(data), len(data), write_fd)
assert handle
lib.cancelAsyncRequest(handle)
os.close(read_fd)
os.close(write_fd)
time.sleep(0.7)
assert lib.getAsyncResult(handle, _ffi._ffi.new('int*')) == _ffi._ffi.NULL
"""
    env = dict(os.environ, CYCLETLS_BACKEND="inprocess")
    result = subprocess.run(
        [sys.executable, "-c", script, local_url], env=env, capture_output=True, timeout=10
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")
