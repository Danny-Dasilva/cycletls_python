"""HTTP transport that keeps the Go runtime in a fresh Python interpreter.

Requests are never replayed after worker death. A subsequent call starts a new
worker; request IDs let concurrent callers receive responses out of order.
"""

import asyncio
import atexit
import concurrent.futures
import os
import struct
import subprocess
import sys
import threading
from typing import IO, Any, Optional

import ormsgpack

from .exceptions import CycleTLSError, CycleTLSWorkerDied, Timeout

_MAX_FRAME = 256 * 1024 * 1024


def _read_exact(stream: IO[bytes], size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        chunk = stream.read(size - len(chunks))
        if not chunk:
            raise EOFError("Worker pipe closed during a message")
        chunks.extend(chunk)
    return bytes(chunks)


def _read_frame(stream: IO[bytes]) -> Optional[dict]:
    header = stream.read(4)
    if not header:
        return None
    if len(header) < 4:
        header += _read_exact(stream, 4 - len(header))
    size = struct.unpack("!I", header)[0]
    if size > _MAX_FRAME:
        raise ValueError("Worker message exceeds maximum frame size")
    return ormsgpack.unpackb(_read_exact(stream, size))


def _write_frame(stream: IO[bytes], message: dict) -> None:
    data = ormsgpack.packb(message)
    if len(data) > _MAX_FRAME:
        raise ValueError("Worker message exceeds maximum frame size")
    frame = memoryview(struct.pack("!I", len(data)) + data)
    while frame:
        written = stream.write(frame)
        if not written:
            raise BrokenPipeError("Worker pipe closed while writing a message")
        frame = frame[written:]
    stream.flush()


def _timeout(payload: Any) -> float:
    options = payload.get("options", {}) if isinstance(payload, dict) else {}
    value = options.get("timeout", 30)
    return float(value) if value and float(value) > 0 else 30.0


def _remote_error(error: dict) -> Exception:
    from . import exceptions

    error_name = str(error.get("type", ""))
    error_type = getattr(exceptions, error_name, None)
    if not isinstance(error_type, type) or not issubclass(error_type, Exception):
        error_type = {
            "ValueError": ValueError,
            "TypeError": TypeError,
            "RuntimeError": RuntimeError,
        }.get(error_name, CycleTLSError)
    return error_type(error.get("message", "Worker request failed"))


class SubprocessBackend:
    """One lazy worker shared by synchronous and asynchronous callers."""

    def __init__(self, command: Optional[list[str]] = None):
        self._command = command or [sys.executable, "-m", "cycletls._subprocess", "worker"]
        self._lock = threading.RLock()
        self._process = None
        self._reader = None
        self._pending = {}
        self._next_id = 0
        self._pid = os.getpid()

    def _ensure_owner(self):
        if self._pid == os.getpid():
            return
        # After a host fork, inherited locks may be held by vanished threads.
        # Drop only this child's pipe copies; the original worker belongs to
        # the parent and must never be terminated or read from here.
        process = self._process
        self._lock = threading.RLock()
        self._process = None
        self._reader = None
        self._pending = {}
        self._pid = os.getpid()
        if process is not None:
            if process.stdin is not None:
                process.stdin.close()
            if process.stdout is not None:
                process.stdout.close()

    def _start(self):
        if self._process is not None and self._process.poll() is None:
            return self._process
        env = os.environ.copy()
        env["CYCLETLS_BACKEND"] = "inprocess"
        process = subprocess.Popen(
            self._command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=env, bufsize=0
        )
        self._process = process
        self._reader = threading.Thread(
            target=self._read, args=(process,), daemon=True, name="cycletls-worker-reader"
        )
        self._reader.start()
        return process

    def _fail(self, process, reason):
        with self._lock:
            if self._process is process:
                self._process = None
            affected = [
                (key, future) for key, (owner, future) in self._pending.items() if owner is process
            ]
            for key, future in affected:
                self._pending.pop(key, None)
                if not future.done():
                    try:
                        future.set_exception(CycleTLSWorkerDied(reason))
                    except concurrent.futures.InvalidStateError:
                        pass

    def _read(self, process):
        try:
            while True:
                message = _read_frame(process.stdout)
                if message is None:
                    break
                with self._lock:
                    item = self._pending.pop(message["id"], None)
                    if item is None:
                        continue
                    _, future = item
                    if not future.done():
                        try:
                            if "error" in message:
                                future.set_exception(_remote_error(message["error"]))
                            else:
                                future.set_result(message["result"])
                        except concurrent.futures.InvalidStateError:
                            # asyncio can cancel its future between the check and delivery.
                            pass
        except (OSError, EOFError, ValueError, KeyError) as error:
            self._fail(process, f"CycleTLS worker communication failed: {error}")
        finally:
            try:
                status = process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                process.kill()
                status = process.wait()
            self._fail(process, f"CycleTLS worker exited with status {status}")
            process.stdout.close()
            process.stdin.close()

    def _submit(self, operation, payload):
        self._ensure_owner()
        future = concurrent.futures.Future()
        with self._lock:
            process = self._start()
            assert process.stdin is not None
            self._next_id += 1
            request_id = self._next_id
            self._pending[request_id] = (process, future)
            try:
                _write_frame(
                    process.stdin, {"id": request_id, "operation": operation, "payload": payload}
                )
            except (BrokenPipeError, OSError) as error:
                self._fail(process, f"CycleTLS worker pipe closed: {error}")
            except Exception:
                self._pending.pop(request_id, None)
                raise
        return request_id, future

    def _discard(self, request_id):
        with self._lock:
            item = self._pending.pop(request_id, None)
            if item:
                item[1].cancel()

    def _request(self, operation, payload, timeout):
        request_id, future = self._submit(operation, payload)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError as error:
            raise Timeout(f"Request timed out after {timeout} seconds") from error
        finally:
            self._discard(request_id)

    def send_request(self, payload):
        return self._request("request", payload, _timeout(payload))

    def send_batch_request(self, payloads):
        if not payloads:
            return []
        return self._request("batch", payloads, max(_timeout(p) for p in payloads))

    async def send_request_async(self, payload, timeout=None):
        # Process creation and pipe writes may block; keep them off the event loop.
        submission = asyncio.create_task(asyncio.to_thread(self._submit, "request", payload))
        try:
            request_id, future = await asyncio.shield(submission)
        except asyncio.CancelledError:

            def discard_when_submitted(task):
                if not task.cancelled() and task.exception() is None:
                    self._discard(task.result()[0])

            submission.add_done_callback(discard_when_submitted)
            raise
        try:
            return await asyncio.wait_for(
                asyncio.wrap_future(future),
                timeout=_timeout(payload) if timeout is None else timeout,
            )
        finally:
            self._discard(request_id)

    def close(self):
        self._ensure_owner()
        with self._lock:
            process = self._process
            self._process = None
            reader = self._reader
            self._reader = None
            if process is None:
                return
            self._fail(process, "CycleTLS worker closed")
            process.terminate()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        if reader is not None and reader is not threading.current_thread():
            reader.join(timeout=1)


_backend = SubprocessBackend()
send_request = _backend.send_request
send_batch_request = _backend.send_batch_request
send_request_async = _backend.send_request_async
close = _backend.close
atexit.register(close)


def _worker():
    # Reserve stdout for frames; native Go/C writes to fd 1 must not corrupt IPC.
    output = os.fdopen(os.dup(sys.stdout.fileno()), "wb", buffering=0)
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
    os.environ["CYCLETLS_BACKEND"] = "inprocess"
    from . import _ffi

    write_lock = threading.Lock()

    def execute(message):
        try:
            fn = _ffi.send_batch_request if message["operation"] == "batch" else _ffi.send_request
            response = {"id": message["id"], "result": fn(message["payload"])}
        except Exception as error:
            response = {
                "id": message["id"],
                "error": {"type": type(error).__name__, "message": str(error)},
            }
        with write_lock:
            _write_frame(output, response)

    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
        while True:
            message = _read_frame(sys.stdin.buffer)
            if message is None:
                break
            executor.submit(execute, message)


if __name__ == "__main__":
    _worker()
