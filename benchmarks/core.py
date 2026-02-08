"""Core benchmarking functions and utilities."""

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from io import BytesIO

try:
    import pycurl
except ImportError:
    pycurl = None

try:
    import urllib3 as _urllib3
except ImportError:
    _urllib3 = None


class CycleTLSSession:
    """Wrapper for CycleTLS to provide a requests-like Session interface."""

    def __init__(self):
        from cycletls import CycleTLS
        self.client = CycleTLS()

    def get(self, url: str):
        return self.client.get(url)

    def close(self):
        self.client.close()


class CycleTLSAsyncSession:
    """Wrapper for CycleTLS async to provide an async Session interface."""

    def __init__(self):
        from cycletls import CycleTLS
        self.client = CycleTLS()

    async def get(self, url: str):
        return await self.client.aget(url)

    async def aclose(self):
        self.client.close()

    def close(self):
        self.client.close()


class Urllib3Session:
    """Wrapper for urllib3 to provide a Session-like interface."""

    def __init__(self):
        if _urllib3 is None:
            raise ImportError("urllib3 is not installed")
        self.pool = _urllib3.PoolManager()

    def get(self, url: str):
        return self.pool.request("GET", url)

    def close(self):
        self.pool.clear()


class PycurlSession:
    """Wrapper for pycurl to provide a Session-like interface."""

    def __init__(self):
        self.curl = pycurl.Curl() if pycurl else None
        self._response = BytesIO()

    def get(self, url: str) -> "PycurlSession":
        """Execute a GET request."""
        if not self.curl:
            raise ImportError("pycurl is not installed")

        self._response = BytesIO()
        self.curl.setopt(pycurl.URL, url)
        self.curl.setopt(pycurl.WRITEDATA, self._response)
        self.curl.perform()
        return self

    @property
    def text(self) -> str:
        """Get response text."""
        return self._response.getvalue().decode('utf-8', errors='ignore')

    def close(self):
        """Close the session."""
        if self.curl:
            self.curl.close()


def add_package_version(packages: List[Tuple[str, Any]]) -> List[Tuple[str, Any, str]]:
    """Add version information to package list."""
    result = []
    for name, pkg_class in packages:
        try:
            # Try to get version from the module
            module = pkg_class.__module__.split('.')[0]
            pkg = __import__(module)
            version = getattr(pkg, '__version__', 'unknown')
        except Exception:
            version = 'unknown'
        result.append((name, pkg_class, version))
    return result


def _execute_request(session: Any, url: str, library_name: str) -> Optional[str]:
    """Execute a single synchronous HTTP request."""
    try:
        if library_name == 'pycurl':
            return session.get(url).text
        else:
            response = session.get(url)
            return response.text if hasattr(response, 'text') else response.body.decode()
    except Exception as e:
        print(f"Error in {library_name}: {e}")
        return None


async def _async_execute_request(session: Any, url: str, library_name: str) -> Optional[str]:
    """Execute a single asynchronous HTTP request."""
    try:
        if library_name == 'aiohttp':
            async with session.get(url) as response:
                return await response.text()
        elif library_name == 'ry':
            response = await session.get(url)
            return response.text()
        else:
            response = await session.get(url)
            return response.text if hasattr(response, 'text') else response.body.decode()
    except Exception as e:
        print(f"Error in {library_name}: {e}")
        return None


def _safe_close_session(session: Any, library_name: str) -> None:
    """Safely close a synchronous session."""
    try:
        if hasattr(session, 'close'):
            session.close()
    except Exception:
        pass


async def _safe_close_async_session(session: Any, library_name: str) -> None:
    """Safely close an asynchronous session."""
    try:
        if hasattr(session, 'close'):
            if asyncio.iscoroutinefunction(session.close):
                await session.close()
            else:
                session.close()
        elif hasattr(session, 'aclose'):
            await session.aclose()
    except Exception:
        pass


def _execute_timed_test(func: Callable, *args, **kwargs) -> Tuple[float, float]:
    """Execute a function and measure both wall time and CPU time."""
    cpu_start = time.process_time()
    wall_start = time.perf_counter()

    func(*args, **kwargs)

    wall_time = time.perf_counter() - wall_start
    cpu_time = time.process_time() - cpu_start

    return wall_time, cpu_time


async def _execute_timed_async_test(func: Callable, *args, **kwargs) -> Tuple[float, float]:
    """Execute an async function and measure both wall time and CPU time."""
    cpu_start = time.process_time()
    wall_start = time.perf_counter()

    await func(*args, **kwargs)

    wall_time = time.perf_counter() - wall_start
    cpu_time = time.process_time() - cpu_start

    return wall_time, cpu_time


def _record_test_result(
    library_name: str,
    version: str,
    session_type: str,
    size: str,
    requests_count: int,
    wall_time: float,
    cpu_time: float,
) -> Dict[str, Any]:
    """Create a result dictionary."""
    return {
        'library': library_name,
        'version': version,
        'session_type': session_type,
        'payload_size': size,
        'requests': requests_count,
        'wall_time': wall_time,
        'cpu_time': cpu_time,
        'req_per_sec': requests_count / wall_time if wall_time > 0 else 0,
        'us_per_req': wall_time * 1_000_000 / requests_count if wall_time > 0 else 0,
    }


def compute_vs_requests(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Add vs_requests comparison field using requests sync_session as baseline."""
    if not results:
        return []

    baseline_time = None
    for r in results:
        if r.get('library') == 'requests' and r.get('session_type') == 'sync_session':
            baseline_time = r['wall_time']
            break

    enriched = []
    for r in results:
        r = dict(r)
        if baseline_time is None:
            r['vs_requests'] = 'N/A'
        elif r.get('library') == 'requests' and r.get('session_type') == 'sync_session':
            r['vs_requests'] = 'baseline'
        else:
            wall = r.get('wall_time', 0)
            if wall > 0 and baseline_time > 0:
                r['vs_requests'] = f'{baseline_time / wall:.1f}x'
            else:
                r['vs_requests'] = 'N/A'
        enriched.append(r)
    return enriched


def session_get_test(
    session_class: Type,
    url: str,
    requests_count: int,
    library_name: str,
) -> None:
    """Test HTTP library with session reuse."""
    session = session_class()
    try:
        for _ in range(requests_count):
            _execute_request(session, url, library_name)
    finally:
        _safe_close_session(session, library_name)


def non_session_get_test(
    session_class: Type,
    url: str,
    requests_count: int,
    library_name: str,
) -> None:
    """Test HTTP library without session reuse (new session per request)."""
    for _ in range(requests_count):
        session = session_class()
        try:
            _execute_request(session, url, library_name)
        finally:
            _safe_close_session(session, library_name)


async def async_session_get_test(
    session_class: Type,
    url: str,
    requests_count: int,
    library_name: str,
) -> None:
    """Test async HTTP library with session reuse."""
    session = session_class()
    try:
        tasks = [
            _async_execute_request(session, url, library_name)
            for _ in range(requests_count)
        ]
        await asyncio.gather(*tasks)
    finally:
        await _safe_close_async_session(session, library_name)


async def async_non_session_get_test(
    session_class: Type,
    url: str,
    requests_count: int,
    library_name: str,
) -> None:
    """Test async HTTP library without session reuse."""
    async def single_request():
        session = session_class()
        try:
            await _async_execute_request(session, url, library_name)
        finally:
            await _safe_close_async_session(session, library_name)

    tasks = [single_request() for _ in range(requests_count)]
    await asyncio.gather(*tasks)


def run_sync_tests(
    packages: List[Tuple[str, Type, str]],
    url: str,
    requests_count: int,
) -> List[Dict[str, Any]]:
    """Run synchronous benchmarks for all packages."""
    results = []

    # Extract size from URL (e.g., "20k" from "/20k" endpoint)
    size = url.split('/')[-1] if '/' in url else 'unknown'

    for library_name, session_class, version in packages:
        print(f"  Testing {library_name} (sync, with session)...")
        try:
            wall_time, cpu_time = _execute_timed_test(
                session_get_test, session_class, url, requests_count, library_name
            )
            results.append(_record_test_result(
                library_name, version, 'sync_session', size,
                requests_count, wall_time, cpu_time
            ))
        except Exception as e:
            print(f"    Failed: {e}")

        print(f"  Testing {library_name} (sync, no session)...")
        try:
            wall_time, cpu_time = _execute_timed_test(
                non_session_get_test, session_class, url, requests_count, library_name
            )
            results.append(_record_test_result(
                library_name, version, 'sync_no_session', size,
                requests_count, wall_time, cpu_time
            ))
        except Exception as e:
            print(f"    Failed: {e}")

    return results


def run_async_tests(
    packages: List[Tuple[str, Type, str]],
    url: str,
    requests_count: int,
) -> List[Dict[str, Any]]:
    """Run asynchronous benchmarks for all packages."""
    results = []

    # Extract size from URL
    size = url.split('/')[-1] if '/' in url else 'unknown'

    for library_name, session_class, version in packages:
        print(f"  Testing {library_name} (async, with session)...")
        try:
            wall_time, cpu_time = asyncio.run(
                _execute_timed_async_test(
                    async_session_get_test, session_class, url, requests_count, library_name
                )
            )
            results.append(_record_test_result(
                library_name, version, 'async_session', size,
                requests_count, wall_time, cpu_time
            ))
        except Exception as e:
            print(f"    Failed: {e}")

        print(f"  Testing {library_name} (async, no session)...")
        try:
            wall_time, cpu_time = asyncio.run(
                _execute_timed_async_test(
                    async_non_session_get_test, session_class, url, requests_count, library_name
                )
            )
            results.append(_record_test_result(
                library_name, version, 'async_no_session', size,
                requests_count, wall_time, cpu_time
            ))
        except Exception as e:
            print(f"    Failed: {e}")

    return results
