"""
Concurrent execution tests for async CycleTLS.

Tests concurrent operations including:
- Multiple concurrent requests with asyncio.gather()
- Batch request handling
- Performance verification for parallel execution
"""

import pytest
import asyncio
import time
import cycletls
from cycletls import AsyncCycleTLS


class TestAsyncConcurrent:
    """Test concurrent async request execution."""

    @pytest.mark.asyncio
    async def test_concurrent_get_requests(self, httpbin_url):
        """Test multiple concurrent GET requests."""
        urls = [f"{httpbin_url}/get?id={i}" for i in range(10)]

        responses = await asyncio.gather(*[
            cycletls.aget(url) for url in urls
        ])

        assert len(responses) == 10
        assert all(r.status_code == 200 for r in responses)

        # Verify each response has correct ID
        for i, response in enumerate(responses):
            data = response.json()
            assert data["args"]["id"] == str(i)

    @pytest.mark.asyncio
    async def test_concurrent_post_requests(self, httpbin_url):
        """Test multiple concurrent POST requests."""
        payloads = [{"id": i, "data": f"test_{i}"} for i in range(5)]

        responses = await asyncio.gather(*[
            cycletls.apost(f"{httpbin_url}/post", json_data=payload)
            for payload in payloads
        ])

        assert len(responses) == 5
        assert all(r.status_code == 200 for r in responses)

        # Verify each response has correct payload
        for i, response in enumerate(responses):
            data = response.json()
            assert data["json"]["id"] == i
            assert data["json"]["data"] == f"test_{i}"

    @pytest.mark.asyncio
    async def test_concurrent_mixed_methods(self, httpbin_url):
        """Test concurrent requests with different HTTP methods."""
        tasks = [
            cycletls.aget(f"{httpbin_url}/get"),
            cycletls.apost(f"{httpbin_url}/post", json_data={"test": "post"}),
            cycletls.aput(f"{httpbin_url}/put", json_data={"test": "put"}),
            cycletls.apatch(f"{httpbin_url}/patch", json_data={"test": "patch"}),
            cycletls.adelete(f"{httpbin_url}/delete"),
        ]

        responses = await asyncio.gather(*tasks)

        assert len(responses) == 5
        assert all(r.status_code == 200 for r in responses)

    @pytest.mark.asyncio
    async def test_concurrent_with_client_reuse(self, httpbin_url):
        """Test concurrent requests using same client instance."""
        async with AsyncCycleTLS() as client:
            tasks = [
                client.get(f"{httpbin_url}/get?id={i}")
                for i in range(10)
            ]

            responses = await asyncio.gather(*tasks)

            assert len(responses) == 10
            assert all(r.status_code == 200 for r in responses)

    @pytest.mark.asyncio
    async def test_large_concurrent_batch(self, httpbin_url):
        """Test large batch of concurrent requests."""
        # Test with 50 concurrent requests
        num_requests = 50
        urls = [f"{httpbin_url}/get?batch_id={i}" for i in range(num_requests)]

        responses = await asyncio.gather(*[
            cycletls.aget(url) for url in urls
        ])

        assert len(responses) == num_requests
        assert all(r.status_code == 200 for r in responses)

    @pytest.mark.asyncio
    async def test_concurrent_with_different_params(self, httpbin_url):
        """Test concurrent requests with different parameters."""
        tasks = [
            cycletls.aget(f"{httpbin_url}/get", params={"type": "json"}),
            cycletls.aget(f"{httpbin_url}/get", params={"type": "html"}),
            cycletls.aget(f"{httpbin_url}/get", headers={"X-Test": "header"}),
            cycletls.aget(f"{httpbin_url}/get", user_agent="Custom-Agent"),
        ]

        responses = await asyncio.gather(*tasks)

        assert len(responses) == 4
        assert all(r.status_code == 200 for r in responses)

        # Verify parameters were applied
        assert responses[0].json()["args"]["type"] == "json"
        assert responses[1].json()["args"]["type"] == "html"
        assert responses[2].json()["headers"]["X-Test"] == "header"
        assert responses[3].json()["headers"]["User-Agent"] == "Custom-Agent"


class TestAsyncPerformance:
    """Test async performance characteristics."""

    @pytest.mark.asyncio
    async def test_concurrent_faster_than_sequential(self, httpbin_url):
        """Verify concurrent requests are faster than sequential."""
        # Use delay endpoint to make the difference clear
        delay_seconds = 1
        num_requests = 3

        # Sequential execution
        start = time.time()
        for _ in range(num_requests):
            await cycletls.aget(f"{httpbin_url}/delay/{delay_seconds}")
        sequential_time = time.time() - start

        # Concurrent execution
        start = time.time()
        await asyncio.gather(*[
            cycletls.aget(f"{httpbin_url}/delay/{delay_seconds}")
            for _ in range(num_requests)
        ])
        concurrent_time = time.time() - start

        # Concurrent should be significantly faster
        # Sequential: ~3 seconds, Concurrent: ~1 second
        assert concurrent_time < sequential_time * 0.6
        print(f"\nSequential: {sequential_time:.2f}s, Concurrent: {concurrent_time:.2f}s")
        print(f"Speedup: {sequential_time / concurrent_time:.2f}x")

    @pytest.mark.asyncio
    async def test_throughput_with_quick_requests(self, httpbin_url):
        """Test throughput with many quick requests."""
        num_requests = 20
        start = time.time()

        responses = await asyncio.gather(*[
            cycletls.aget(f"{httpbin_url}/get?id={i}")
            for i in range(num_requests)
        ])

        elapsed = time.time() - start

        assert len(responses) == num_requests
        assert all(r.status_code == 200 for r in responses)

        requests_per_second = num_requests / elapsed
        print(f"\nThroughput: {requests_per_second:.2f} req/s ({elapsed:.2f}s total)")

        # Should handle at least 10 requests per second
        assert requests_per_second > 10


class TestAsyncErrorHandlingConcurrent:
    """Test error handling in concurrent requests."""

    @pytest.mark.asyncio
    async def test_concurrent_with_some_failures(self, httpbin_url):
        """Test concurrent requests where some fail."""
        tasks = [
            cycletls.aget(f"{httpbin_url}/status/200"),  # Success
            cycletls.aget(f"{httpbin_url}/status/404"),  # Not Found
            cycletls.aget(f"{httpbin_url}/status/200"),  # Success
            cycletls.aget(f"{httpbin_url}/status/500"),  # Server Error
            cycletls.aget(f"{httpbin_url}/status/200"),  # Success
        ]

        responses = await asyncio.gather(*tasks)

        assert len(responses) == 5
        assert responses[0].status_code == 200
        assert responses[1].status_code == 404
        assert responses[2].status_code == 200
        assert responses[3].status_code == 500
        assert responses[4].status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_all_success(self, httpbin_url):
        """Test that all concurrent requests succeed."""
        num_requests = 15
        responses = await asyncio.gather(*[
            cycletls.aget(f"{httpbin_url}/status/200")
            for _ in range(num_requests)
        ])

        assert len(responses) == num_requests
        assert all(r.status_code == 200 for r in responses)
        assert all(r.ok for r in responses)


class TestAsyncTaskCancellation:
    """Test async task cancellation behavior."""

    @pytest.mark.asyncio
    async def test_cancel_pending_requests(self, httpbin_url):
        """Test cancelling pending async requests."""
        # Start multiple long-running requests
        tasks = [
            asyncio.create_task(cycletls.aget(f"{httpbin_url}/delay/5"))
            for _ in range(3)
        ]

        # Wait a bit
        await asyncio.sleep(0.1)

        # Cancel all tasks
        for task in tasks:
            task.cancel()

        # Verify cancellation
        results = await asyncio.gather(*tasks, return_exceptions=True)
        assert all(isinstance(r, asyncio.CancelledError) for r in results)

    @pytest.mark.asyncio
    async def test_timeout_group_of_requests(self, httpbin_url):
        """Test timeout for a group of requests."""
        # This should timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                asyncio.gather(*[
                    cycletls.aget(f"{httpbin_url}/delay/10")
                    for _ in range(3)
                ]),
                timeout=1.0  # 1 second timeout
            )


class TestAsyncBatchPatterns:
    """Test common async batch patterns."""

    @pytest.mark.asyncio
    async def test_process_results_as_completed(self, httpbin_url):
        """Test processing results as they complete."""
        tasks = [
            asyncio.create_task(cycletls.aget(f"{httpbin_url}/delay/{i}"))
            for i in [1, 0, 2]  # Different delays
        ]

        results = []
        for coro in asyncio.as_completed(tasks):
            response = await coro
            results.append(response.status_code)

        assert len(results) == 3
        assert all(code == 200 for code in results)

    @pytest.mark.asyncio
    async def test_gather_with_return_exceptions(self, httpbin_url):
        """Test gather with return_exceptions=True."""
        tasks = [
            cycletls.aget(f"{httpbin_url}/status/200"),
            cycletls.aget("https://invalid-domain-that-does-not-exist-12345.com"),
            cycletls.aget(f"{httpbin_url}/status/200"),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        assert len(results) == 3
        assert results[0].status_code == 200
        assert isinstance(results[1], Exception)  # Failed request
        assert results[2].status_code == 200

    @pytest.mark.asyncio
    async def test_semaphore_rate_limiting(self, httpbin_url):
        """Test rate limiting with semaphore."""
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent

        async def limited_request(url):
            async with semaphore:
                return await cycletls.aget(url)

        # Launch 20 requests, but only 5 at a time
        responses = await asyncio.gather(*[
            limited_request(f"{httpbin_url}/get?id={i}")
            for i in range(20)
        ])

        assert len(responses) == 20
        assert all(r.status_code == 200 for r in responses)
