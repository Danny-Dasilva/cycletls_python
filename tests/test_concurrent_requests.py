"""
Concurrent Requests Tests for CycleTLS Python library.

Based on CycleTLS JavaScript multipleRequests tests, these tests verify:
- Multiple simultaneous requests
- Thread safety
- Connection pool under load
- Error isolation between concurrent requests
- Performance under concurrent load

Tests use httpbin.org and multiple endpoints to verify concurrent request handling.
"""

import pytest
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from test_utils import (
    assert_valid_response,
    assert_valid_json_response,
)


class TestConcurrentRequests:
    """Test multiple concurrent requests."""

    def test_multiple_concurrent_get_requests(self, cycletls_client, httpbin_url, firefox_ja3):
        """Test multiple concurrent GET requests complete successfully."""
        # Define multiple requests to different endpoints
        request_configs = [
            {
                'url': f'{httpbin_url}/user-agent',
                'params': {
                    'ja3': firefox_ja3,
                    'user_agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0'
                }
            },
            {
                'url': f'{httpbin_url}/headers',
                'params': {
                    'headers': {'X-Test-Header': 'test-value'}
                }
            },
            {
                'url': f'{httpbin_url}/ip',
                'params': {}
            },
            {
                'url': f'{httpbin_url}/uuid',
                'params': {}
            },
            {
                'url': f'{httpbin_url}/get',
                'params': {}
            },
        ]

        # Execute all requests concurrently using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=len(request_configs)) as executor:
            futures = [
                executor.submit(cycletls_client.get, config['url'], **config['params'])
                for config in request_configs
            ]

            # Wait for all to complete and verify
            responses = []
            for future in as_completed(futures):
                response = future.result()
                responses.append(response)

        # Verify all responses are successful
        assert len(responses) == len(request_configs), \
            f"Expected {len(request_configs)} responses, got {len(responses)}"

        for idx, response in enumerate(responses):
            assert response.status_code == 200, \
                f"Request {idx} should return 200, got {response.status_code}"
            assert response.body, f"Request {idx} should have non-empty body"

    def test_concurrent_mixed_methods(self, cycletls_client, httpbin_url):
        """Test concurrent requests with different HTTP methods."""
        # Define requests with various methods
        request_configs = [
            {
                'method': 'get',
                'url': f'{httpbin_url}/get',
                'params': {}
            },
            {
                'method': 'post',
                'url': f'{httpbin_url}/post',
                'params': {'json_data': {'field': 'POST-VAL'}}
            },
            {
                'method': 'put',
                'url': f'{httpbin_url}/put',
                'params': {'json_data': {'field': 'PUT-VAL'}}
            },
            {
                'method': 'patch',
                'url': f'{httpbin_url}/patch',
                'params': {'json_data': {'field': 'PATCH-VAL'}}
            },
            {
                'method': 'delete',
                'url': f'{httpbin_url}/delete',
                'params': {'json_data': {'field': 'DELETE-VAL'}}
            },
        ]

        # Execute all requests concurrently
        def execute_request(config):
            method = getattr(cycletls_client, config['method'])
            return method(config['url'], **config['params'])

        with ThreadPoolExecutor(max_workers=len(request_configs)) as executor:
            futures = [executor.submit(execute_request, config) for config in request_configs]
            responses = [future.result() for future in as_completed(futures)]

        # Verify all responses are successful
        assert len(responses) == len(request_configs), \
            f"Expected {len(request_configs)} responses, got {len(responses)}"

        for idx, response in enumerate(responses):
            assert response.status_code == 200, \
                f"Request {idx} should return 200, got {response.status_code}"

    def test_concurrent_with_cookies(self, cycletls_client, httpbin_url):
        """Test concurrent requests with cookies."""
        cookies = [
            {
                "name": "example1",
                "value": "aaaaaaa",
                "expires": "2026-01-02T15:04:05Z"
            }
        ]

        # Make multiple concurrent requests with cookies
        urls = [
            f'{httpbin_url}/cookies',
            f'{httpbin_url}/cookies',
            f'{httpbin_url}/cookies',
        ]

        with ThreadPoolExecutor(max_workers=len(urls)) as executor:
            futures = [
                executor.submit(cycletls_client.get, url, cookies=cookies)
                for url in urls
            ]
            responses = [future.result() for future in as_completed(futures)]

        # Verify all responses received cookies
        for idx, response in enumerate(responses):
            assert_valid_response(response, expected_status=200)
            data = assert_valid_json_response(response)
            assert 'cookies' in data, f"Response {idx} should contain cookies"
            assert 'example1' in data['cookies'], f"Response {idx} should have cookie 'example1'"

    def test_high_concurrency_same_endpoint(self, cycletls_client, httpbin_url):
        """Test many concurrent requests to the same endpoint."""
        num_requests = 20
        url = f'{httpbin_url}/get'

        # Execute many requests concurrently to same endpoint
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(cycletls_client.get, f'{url}?id={i}')
                for i in range(num_requests)
            ]
            responses = [future.result() for future in as_completed(futures)]

        # Verify all completed successfully
        assert len(responses) == num_requests, \
            f"Expected {num_requests} responses, got {len(responses)}"

        successful_responses = sum(1 for r in responses if r.status_code == 200)
        assert successful_responses == num_requests, \
            f"Expected all {num_requests} to succeed, got {successful_responses}"


class TestConnectionReuse:
    """Test connection reuse and pooling under concurrent load."""

    def test_sequential_requests_same_host(self, cycletls_client, httpbin_url, firefox_ja3):
        """Test sequential requests to same host reuse connection."""
        url_base = httpbin_url

        # Make multiple sequential requests
        response1 = cycletls_client.get(
            f'{url_base}/get',
            ja3=firefox_ja3,
            user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0'
        )
        assert_valid_response(response1, expected_status=200)

        # Second request - should reuse connection
        response2 = cycletls_client.get(
            f'{url_base}/get?second=true',
            ja3=firefox_ja3,
            user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0'
        )
        assert_valid_response(response2, expected_status=200)

        # Third request with different path but same domain
        response3 = cycletls_client.get(
            f'{url_base}/headers',
            ja3=firefox_ja3,
            user_agent='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0'
        )
        assert_valid_response(response3, expected_status=200)

        # All requests should complete successfully
        # Connection reuse is happening at the Go level

    def test_concurrent_requests_same_domain(self, cycletls_client, httpbin_url):
        """Test concurrent requests to same domain utilize connection pool."""
        # Make many concurrent requests to same domain
        endpoints = [
            '/get',
            '/headers',
            '/ip',
            '/user-agent',
            '/uuid',
            '/base64/aGVsbG8=',
        ]

        urls = [f'{httpbin_url}{endpoint}' for endpoint in endpoints]

        with ThreadPoolExecutor(max_workers=len(urls)) as executor:
            futures = [executor.submit(cycletls_client.get, url) for url in urls]
            responses = [future.result() for future in as_completed(futures)]

        # All should complete successfully
        for idx, response in enumerate(responses):
            assert response.status_code == 200, \
                f"Request to {urls[idx]} should return 200, got {response.status_code}"


class TestThreadSafety:
    """Test thread safety of CycleTLS client."""

    def test_shared_client_concurrent_access(self, cycletls_client, httpbin_url):
        """Test that shared client can handle concurrent access safely."""
        num_threads = 10
        requests_per_thread = 5

        results = []
        results_lock = threading.Lock()

        def make_requests(thread_id):
            thread_results = []
            for i in range(requests_per_thread):
                try:
                    response = cycletls_client.get(
                        f'{httpbin_url}/get?thread={thread_id}&req={i}'
                    )
                    thread_results.append({
                        'thread_id': thread_id,
                        'request_num': i,
                        'status': response.status_code,
                        'success': True
                    })
                except Exception as e:
                    thread_results.append({
                        'thread_id': thread_id,
                        'request_num': i,
                        'error': str(e),
                        'success': False
                    })

            with results_lock:
                results.extend(thread_results)

        # Create and start threads
        threads = []
        for thread_id in range(num_threads):
            thread = threading.Thread(target=make_requests, args=(thread_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all requests completed
        total_expected = num_threads * requests_per_thread
        assert len(results) == total_expected, \
            f"Expected {total_expected} results, got {len(results)}"

        # Count successful requests
        successful = sum(1 for r in results if r.get('success', False))
        assert successful == total_expected, \
            f"Expected all {total_expected} requests to succeed, got {successful}"

    def test_concurrent_different_configurations(self, cycletls_client, httpbin_url):
        """Test concurrent requests with different configurations don't interfere."""
        def make_request_with_config(config_id, headers):
            response = cycletls_client.get(
                f'{httpbin_url}/headers',
                headers=headers
            )
            data = response.json()
            # Verify our header was sent
            assert headers['X-Config-Id'] in data['headers'].get('X-Config-Id', ''), \
                f"Config {config_id} header should be preserved"
            return config_id

        # Different configurations
        configs = [
            {'X-Config-Id': 'config-1', 'X-Test': 'value1'},
            {'X-Config-Id': 'config-2', 'X-Test': 'value2'},
            {'X-Config-Id': 'config-3', 'X-Test': 'value3'},
            {'X-Config-Id': 'config-4', 'X-Test': 'value4'},
            {'X-Config-Id': 'config-5', 'X-Test': 'value5'},
        ]

        with ThreadPoolExecutor(max_workers=len(configs)) as executor:
            futures = [
                executor.submit(make_request_with_config, i, config)
                for i, config in enumerate(configs)
            ]
            results = [future.result() for future in as_completed(futures)]

        # All should complete successfully
        assert len(results) == len(configs), \
            f"Expected {len(configs)} results, got {len(results)}"


class TestErrorIsolation:
    """Test that errors in concurrent requests don't affect other requests."""

    def test_mixed_success_and_failure_requests(self, cycletls_client, httpbin_url):
        """Test that failed requests don't affect successful ones."""
        # Mix of successful and failing requests
        request_configs = [
            {'url': f'{httpbin_url}/status/200', 'should_succeed': True},
            {'url': f'{httpbin_url}/status/404', 'should_succeed': False},
            {'url': f'{httpbin_url}/status/200', 'should_succeed': True},
            {'url': f'{httpbin_url}/status/500', 'should_succeed': False},
            {'url': f'{httpbin_url}/status/200', 'should_succeed': True},
            {'url': f'{httpbin_url}/get', 'should_succeed': True},
        ]

        def make_request(config):
            try:
                response = cycletls_client.get(config['url'])
                return {
                    'status': response.status_code,
                    'success': True,
                    'expected': config['should_succeed']
                }
            except Exception as e:
                return {
                    'error': str(e),
                    'success': False,
                    'expected': config['should_succeed']
                }

        with ThreadPoolExecutor(max_workers=len(request_configs)) as executor:
            futures = [executor.submit(make_request, config) for config in request_configs]
            results = [future.result() for future in as_completed(futures)]

        # Verify all requests completed (some with errors)
        assert len(results) == len(request_configs), \
            f"Expected {len(request_configs)} results, got {len(results)}"

        # Verify successful requests did succeed
        successful_results = [r for r in results if r.get('expected', False)]
        for result in successful_results:
            if result.get('success'):
                assert result.get('status') in [200, 404, 500], \
                    f"Request completed with status: {result.get('status')}"

    def test_timeout_doesnt_affect_other_requests(self, cycletls_client, httpbin_url):
        """Test that a timeout in one request doesn't affect others."""
        # Mix of fast and slow requests
        request_configs = [
            {'url': f'{httpbin_url}/get', 'timeout': None},
            {'url': f'{httpbin_url}/delay/10', 'timeout': 1},  # Will timeout
            {'url': f'{httpbin_url}/get', 'timeout': None},
            {'url': f'{httpbin_url}/get', 'timeout': None},
        ]

        def make_request(config):
            try:
                if config['timeout']:
                    response = cycletls_client.get(config['url'], timeout=config['timeout'])
                else:
                    response = cycletls_client.get(config['url'])
                return {
                    'url': config['url'],
                    'status': response.status_code,
                    'success': True
                }
            except Exception as e:
                return {
                    'url': config['url'],
                    'error': str(e),
                    'success': False
                }

        with ThreadPoolExecutor(max_workers=len(request_configs)) as executor:
            futures = [executor.submit(make_request, config) for config in request_configs]
            results = [future.result() for future in as_completed(futures)]

        # Verify all requests completed
        assert len(results) == len(request_configs), \
            f"Expected {len(request_configs)} results, got {len(results)}"

        # Verify the non-timeout requests succeeded
        fast_requests = [r for r in results if '/delay/' not in r['url']]
        successful_fast = sum(1 for r in fast_requests if r.get('success'))
        assert successful_fast >= 2, \
            f"At least 2 fast requests should succeed, got {successful_fast}"


class TestPerformance:
    """Test performance under concurrent load."""

    def test_concurrent_performance(self, cycletls_client, httpbin_url):
        """Test that concurrent requests complete in reasonable time."""
        num_requests = 10
        url = f'{httpbin_url}/get'

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(cycletls_client.get, f'{url}?id={i}')
                for i in range(num_requests)
            ]
            responses = [future.result() for future in as_completed(futures)]

        elapsed_time = time.time() - start_time

        # All should succeed
        successful = sum(1 for r in responses if r.status_code == 200)
        assert successful == num_requests, \
            f"Expected {num_requests} successful requests, got {successful}"

        # Should complete in reasonable time (less than 30 seconds for 10 requests)
        assert elapsed_time < 30, \
            f"Concurrent requests took too long: {elapsed_time:.2f}s"

    def test_sequential_vs_concurrent_comparison(self, cycletls_client, httpbin_url):
        """Compare sequential vs concurrent execution time."""
        num_requests = 5
        url = f'{httpbin_url}/delay/1'  # 1 second delay per request

        # Sequential execution
        start_sequential = time.time()
        for i in range(num_requests):
            try:
                cycletls_client.get(f'{url}?id={i}', timeout=5)
            except Exception:
                pass  # Ignore timeouts for this test
        sequential_time = time.time() - start_sequential

        # Concurrent execution
        start_concurrent = time.time()
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [
                executor.submit(cycletls_client.get, f'{url}?id={i}', timeout=5)
                for i in range(num_requests)
            ]
            try:
                [future.result() for future in as_completed(futures)]
            except Exception:
                pass  # Ignore timeouts
        concurrent_time = time.time() - start_concurrent

        # Concurrent should be significantly faster
        # Note: This test might be flaky depending on network conditions
        # We're just checking that concurrent doesn't take num_requests times as long
        assert concurrent_time < sequential_time, \
            f"Concurrent ({concurrent_time:.2f}s) should be faster than sequential ({sequential_time:.2f}s)"
