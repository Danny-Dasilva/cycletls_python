"""Exercise isolation using fresh interpreters, including fatal worker exits."""

import asyncio
import signal
import subprocess
import sys
import time

import pytest

from cycletls import _subprocess
from cycletls.exceptions import CycleTLSWorkerDied, Timeout

FAKE_WORKER = r"""
import os, signal, sys, threading, time
from cycletls._subprocess import _read_frame, _write_frame
lock = threading.Lock()
def respond(message):
    payload = message['payload']
    if isinstance(payload, dict) and payload.get('error'):
        with lock:
            _write_frame(sys.stdout.buffer, {'id': message['id'], 'error': {
                'type': 'Timeout', 'message': 'native request timeout'}})
        return
    if message['operation'] == 'batch':
        result = payload
    else:
        if payload.get('abort'):
            os.kill(os.getpid(), signal.SIGABRT)
            time.sleep(10)  # Never race signal delivery by sending a success frame.
        if payload.get('exit'):
            os._exit(7)
        time.sleep(payload.get('delay', 0))
        result = payload
    with lock:
        _write_frame(sys.stdout.buffer, {'id': message['id'], 'result': result})
while True:
    message = _read_frame(sys.stdin.buffer)
    if message is None: break
    threading.Thread(target=respond, args=(message,), daemon=True).start()
"""


@pytest.fixture
def backend():
    worker = _subprocess.SubprocessBackend(command=[sys.executable, "-c", FAKE_WORKER])
    yield worker
    worker.close()


def test_bytes_batch_and_restart(backend):
    payload = {"body": b"\x00\xff\x80", "options": {"timeout": 2}}
    assert backend.send_request(payload) == payload
    assert backend.send_batch_request([payload, payload]) == [payload, payload]
    with pytest.raises(CycleTLSWorkerDied, match="7"):
        backend.send_request({"exit": True})
    assert backend.send_request(payload) == payload


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX fatal signal")
def test_abort_is_an_exception_and_next_call_restarts(backend):
    with pytest.raises(CycleTLSWorkerDied, match=str(int(signal.SIGABRT))):
        backend.send_request({"abort": True})
    assert backend.send_request({"after_abort": True}) == {"after_abort": True}


def test_sync_timeout_discards_late_response(backend):
    with pytest.raises(Timeout):
        backend.send_request({"delay": 0.3, "options": {"timeout": 0.02}})
    assert backend.send_request({"next": True}) == {"next": True}


@pytest.mark.asyncio
async def test_concurrent_out_of_order_responses_and_cancellation(backend):
    slow = asyncio.create_task(backend.send_request_async({"delay": 0.4}, timeout=2))
    await asyncio.sleep(0.05)
    start = time.monotonic()
    assert await backend.send_request_async({"fast": b"\xff"}, timeout=2) == {"fast": b"\xff"}
    assert time.monotonic() - start < 0.25
    slow.cancel()
    with pytest.raises(asyncio.CancelledError):
        await slow
    await asyncio.sleep(0.45)
    assert not backend._pending
    assert await backend.send_request_async({"ok": True}) == {"ok": True}


@pytest.mark.asyncio
async def test_async_timeout_leaves_worker_usable(backend):
    with pytest.raises(asyncio.TimeoutError):
        await backend.send_request_async({"delay": 0.3}, timeout=0.02)
    assert await backend.send_request_async({"ok": True}) == {"ok": True}


@pytest.mark.asyncio
async def test_worker_death_fails_every_affected_call(backend):
    slow = asyncio.create_task(backend.send_request_async({"delay": 1}, timeout=2))
    await asyncio.sleep(0.1)
    crash = asyncio.create_task(backend.send_request_async({"exit": True}, timeout=2))
    results = await asyncio.gather(slow, crash, return_exceptions=True)
    assert all(isinstance(result, CycleTLSWorkerDied) for result in results)
    assert not backend._pending


def test_close_reaps_worker_and_can_restart(backend):
    backend.send_request({"ok": True})
    process = backend._process
    backend.close()
    assert process.poll() is not None
    assert not backend._pending
    assert backend.send_request({"restart": True}) == {"restart": True}


def test_remote_exception_type_and_message_survive(backend):
    with pytest.raises(Timeout, match="native request timeout"):
        backend.send_request({"error": True})
    assert backend.send_request({"next": True}) == {"next": True}


def test_frame_supports_partial_reads_and_writes():
    import io

    class PartialBuffer(io.BytesIO):
        def read(self, size=-1):
            return super().read(min(size, 2))

        def write(self, data):
            return super().write(data[:3])

    buffer = PartialBuffer()
    message = {"binary": b"\xff\x00" * 100}
    _subprocess._write_frame(buffer, message)
    buffer.seek(0)
    assert _subprocess._read_frame(buffer) == message


@pytest.mark.skipif(not hasattr(__import__("os"), "fork"), reason="POSIX host fork")
def test_host_fork_starts_separate_worker_without_closing_parent_worker():
    script = """
import os, sys
from cycletls._subprocess import SubprocessBackend
backend = SubprocessBackend(command=[sys.executable, '-c', FAKE_WORKER])
backend.send_request({'parent': True})
parent_worker = backend._process.pid
child = os.fork()
if child == 0:
    try:
        assert backend.send_request({'child': True}) == {'child': True}
        assert backend._process.pid != parent_worker
        backend.close()
        os._exit(0)
    except BaseException:
        os._exit(1)
_, status = os.waitpid(child, 0)
assert status == 0, status
assert backend.send_request({'parent_again': True}) == {'parent_again': True}
assert backend._process.pid == parent_worker
backend.close()
"""
    subprocess.run(
        [sys.executable, "-c", "FAKE_WORKER = " + repr(FAKE_WORKER) + "\n" + script],
        check=True,
        timeout=5,
        capture_output=True,
    )
