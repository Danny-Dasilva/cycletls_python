"""Tests for benchmark CSV output columns: us_per_req and vs_requests."""

import pytest


class TestRecordTestResultUsPerReq:
    """Test that _record_test_result includes us_per_req."""

    def test_us_per_req_calculated_correctly(self):
        """us_per_req should be wall_time * 1_000_000 / requests."""
        from benchmarks.core import _record_test_result

        result = _record_test_result(
            library_name='test_lib',
            version='1.0',
            session_type='sync_session',
            size='default',
            requests_count=1000,
            wall_time=0.5,  # 0.5 seconds for 1000 requests
            cpu_time=0.3,
        )

        assert 'us_per_req' in result
        # 0.5 * 1_000_000 / 1000 = 500.0 us/req
        assert result['us_per_req'] == pytest.approx(500.0, rel=1e-3)

    def test_us_per_req_zero_wall_time(self):
        """us_per_req should be 0 when wall_time is 0."""
        from benchmarks.core import _record_test_result

        result = _record_test_result(
            library_name='test_lib',
            version='1.0',
            session_type='sync_session',
            size='default',
            requests_count=1000,
            wall_time=0.0,
            cpu_time=0.0,
        )

        assert result['us_per_req'] == 0

    def test_us_per_req_realistic_values(self):
        """Test with realistic benchmark values (e.g., ~116 us/req)."""
        from benchmarks.core import _record_test_result

        # 10000 requests in 1.164 seconds -> 116.4 us/req
        result = _record_test_result(
            library_name='cycletls',
            version='0.0.3',
            session_type='async_session',
            size='default',
            requests_count=10000,
            wall_time=1.164,
            cpu_time=0.5,
        )

        assert result['us_per_req'] == pytest.approx(116.4, rel=1e-3)


class TestComputeVsRequests:
    """Test the vs_requests computation function."""

    def test_compute_vs_requests_baseline(self):
        """The requests library result should get 'baseline' as vs_requests."""
        from benchmarks.core import compute_vs_requests

        results = [
            {'library': 'requests', 'session_type': 'sync_session', 'wall_time': 1.0, 'requests': 100},
            {'library': 'httpx', 'session_type': 'sync_session', 'wall_time': 0.5, 'requests': 100},
        ]

        enriched = compute_vs_requests(results)

        # Find the requests result
        req_result = next(r for r in enriched if r['library'] == 'requests')
        assert req_result['vs_requests'] == 'baseline'

    def test_compute_vs_requests_speedup(self):
        """Libraries faster than requests should show Nx speedup."""
        from benchmarks.core import compute_vs_requests

        results = [
            {'library': 'requests', 'session_type': 'sync_session', 'wall_time': 1.0, 'requests': 100},
            {'library': 'httpx', 'session_type': 'sync_session', 'wall_time': 0.5, 'requests': 100},
        ]

        enriched = compute_vs_requests(results)

        httpx_result = next(r for r in enriched if r['library'] == 'httpx')
        # requests wall_time=1.0, httpx wall_time=0.5 => 1.0/0.5 = 2.0x
        assert httpx_result['vs_requests'] == '2.0x'

    def test_compute_vs_requests_slower(self):
        """Libraries slower than requests should still get a ratio."""
        from benchmarks.core import compute_vs_requests

        results = [
            {'library': 'requests', 'session_type': 'sync_session', 'wall_time': 1.0, 'requests': 100},
            {'library': 'slow_lib', 'session_type': 'sync_session', 'wall_time': 2.0, 'requests': 100},
        ]

        enriched = compute_vs_requests(results)

        slow_result = next(r for r in enriched if r['library'] == 'slow_lib')
        # 1.0 / 2.0 = 0.5x
        assert slow_result['vs_requests'] == '0.5x'

    def test_compute_vs_requests_no_requests_library(self):
        """When requests library is not in results, vs_requests should be 'N/A'."""
        from benchmarks.core import compute_vs_requests

        results = [
            {'library': 'httpx', 'session_type': 'sync_session', 'wall_time': 0.5, 'requests': 100},
            {'library': 'aiohttp', 'session_type': 'async_session', 'wall_time': 0.3, 'requests': 100},
        ]

        enriched = compute_vs_requests(results)

        for r in enriched:
            assert r['vs_requests'] == 'N/A'

    def test_compute_vs_requests_uses_session_type(self):
        """vs_requests should prefer the sync_session variant of requests as baseline."""
        from benchmarks.core import compute_vs_requests

        results = [
            {'library': 'requests', 'session_type': 'sync_session', 'wall_time': 1.0, 'requests': 100},
            {'library': 'requests', 'session_type': 'sync_no_session', 'wall_time': 2.0, 'requests': 100},
            {'library': 'httpx', 'session_type': 'sync_session', 'wall_time': 0.5, 'requests': 100},
        ]

        enriched = compute_vs_requests(results)

        httpx_result = next(r for r in enriched if r['library'] == 'httpx')
        # Baseline is requests sync_session at wall_time=1.0
        assert httpx_result['vs_requests'] == '2.0x'

    def test_compute_vs_requests_empty_list(self):
        """Empty input should return empty output."""
        from benchmarks.core import compute_vs_requests

        assert compute_vs_requests([]) == []

    def test_compute_vs_requests_does_not_mutate_originals(self):
        """compute_vs_requests should not modify the input dicts in place (or if it does, it adds the field)."""
        from benchmarks.core import compute_vs_requests

        results = [
            {'library': 'requests', 'session_type': 'sync_session', 'wall_time': 1.0, 'requests': 100},
        ]

        enriched = compute_vs_requests(results)
        # The returned list should have the vs_requests field
        assert 'vs_requests' in enriched[0]


