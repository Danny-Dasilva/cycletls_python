#!/usr/bin/env python3
"""
Concurrent Async Requests Example for CycleTLS

This example demonstrates concurrent request handling with async/await,
including:
- Making multiple requests in parallel with asyncio.gather()
- Performance comparison: sequential vs concurrent
- Batch processing patterns
- Rate limiting with semaphores
- Error handling in concurrent requests
"""

import asyncio
import time
from typing import List
import cycletls
from cycletls import AsyncCycleTLS


async def example_basic_concurrent():
    """Basic concurrent requests using asyncio.gather()."""
    print("=== Basic Concurrent Requests ===\n")

    urls = [
        "https://httpbin.org/get?id=1",
        "https://httpbin.org/get?id=2",
        "https://httpbin.org/get?id=3",
        "https://httpbin.org/get?id=4",
        "https://httpbin.org/get?id=5",
    ]

    print(f"Making {len(urls)} concurrent requests...")
    start_time = time.time()

    # All requests execute in parallel
    responses = await asyncio.gather(*[
        cycletls.aget(url) for url in urls
    ])

    elapsed = time.time() - start_time

    print(f"Completed {len(responses)} requests in {elapsed:.2f} seconds")
    print(f"All successful: {all(r.status_code == 200 for r in responses)}")

    # Display results
    for i, response in enumerate(responses, 1):
        data = response.json()
        print(f"  Request {i}: {data['args']['id']}")

    print()


async def example_performance_comparison():
    """Compare sequential vs concurrent performance."""
    print("=== Performance Comparison ===\n")

    # URLs with artificial delay
    num_requests = 5
    delay = 1  # 1 second delay per request
    urls = [f"https://httpbin.org/delay/{delay}?id={i}" for i in range(num_requests)]

    # Sequential execution
    print(f"Sequential: Making {num_requests} requests with {delay}s delay each...")
    start_time = time.time()

    for url in urls:
        await cycletls.aget(url)

    sequential_time = time.time() - start_time
    print(f"Sequential time: {sequential_time:.2f}s\n")

    # Concurrent execution
    print(f"Concurrent: Making {num_requests} requests with {delay}s delay each...")
    start_time = time.time()

    await asyncio.gather(*[cycletls.aget(url) for url in urls])

    concurrent_time = time.time() - start_time
    print(f"Concurrent time: {concurrent_time:.2f}s\n")

    # Calculate speedup
    speedup = sequential_time / concurrent_time
    print(f"Speedup: {speedup:.2f}x faster")
    print(f"Time saved: {sequential_time - concurrent_time:.2f}s\n")


async def example_mixed_methods():
    """Concurrent requests with different HTTP methods."""
    print("=== Mixed HTTP Methods ===\n")

    print("Making concurrent GET, POST, PUT, PATCH, DELETE requests...")

    tasks = [
        cycletls.aget("https://httpbin.org/get"),
        cycletls.apost("https://httpbin.org/post", json_data={"type": "async"}),
        cycletls.aput("https://httpbin.org/put", json_data={"action": "update"}),
        cycletls.apatch("https://httpbin.org/patch", json_data={"field": "value"}),
        cycletls.adelete("https://httpbin.org/delete"),
    ]

    responses = await asyncio.gather(*tasks)

    for i, response in enumerate(responses, 1):
        method = ["GET", "POST", "PUT", "PATCH", "DELETE"][i-1]
        print(f"  {method}: Status {response.status_code}")

    print()


async def example_batch_processing():
    """Process large batches of requests."""
    print("=== Batch Processing ===\n")

    # Simulate fetching data for many IDs
    num_items = 20
    print(f"Fetching data for {num_items} items in parallel...")

    start_time = time.time()

    urls = [f"https://httpbin.org/get?item_id={i}" for i in range(num_items)]
    responses = await asyncio.gather(*[cycletls.aget(url) for url in urls])

    elapsed = time.time() - start_time

    successful = sum(1 for r in responses if r.status_code == 200)
    print(f"Completed {successful}/{num_items} requests in {elapsed:.2f}s")
    print(f"Throughput: {num_items / elapsed:.2f} requests/second\n")


async def example_rate_limiting():
    """Rate limiting with semaphore."""
    print("=== Rate Limiting with Semaphore ===\n")

    # Limit to 3 concurrent requests at a time
    max_concurrent = 3
    semaphore = asyncio.Semaphore(max_concurrent)

    async def limited_request(url: str, request_id: int):
        """Make request with rate limiting."""
        async with semaphore:
            print(f"  Starting request {request_id}")
            response = await cycletls.aget(url)
            print(f"  Completed request {request_id}")
            return response

    # Launch 10 requests, but only 3 will run at a time
    num_requests = 10
    print(f"Making {num_requests} requests (max {max_concurrent} concurrent)...\n")

    tasks = [
        limited_request(f"https://httpbin.org/get?id={i}", i)
        for i in range(num_requests)
    ]

    responses = await asyncio.gather(*tasks)
    print(f"\nAll {len(responses)} requests completed\n")


async def example_error_handling():
    """Handle errors in concurrent requests."""
    print("=== Error Handling ===\n")

    print("Making concurrent requests (some will fail)...")

    tasks = [
        cycletls.aget("https://httpbin.org/status/200"),  # Success
        cycletls.aget("https://httpbin.org/status/404"),  # Not Found
        cycletls.aget("https://httpbin.org/status/200"),  # Success
        cycletls.aget("https://httpbin.org/status/500"),  # Server Error
        cycletls.aget("https://httpbin.org/status/200"),  # Success
    ]

    # gather() by default stops on first exception
    # Use return_exceptions=True to collect all results
    responses = await asyncio.gather(*tasks)

    # Check results
    for i, response in enumerate(responses, 1):
        status = "✓" if response.status_code == 200 else "✗"
        print(f"  Request {i}: {status} Status {response.status_code}")

    print()


async def example_as_completed():
    """Process results as they complete."""
    print("=== Process As Completed ===\n")

    # Create tasks with different delays
    tasks = [
        asyncio.create_task(cycletls.aget(f"https://httpbin.org/delay/{delay}?id={i}"))
        for i, delay in enumerate([2, 0, 1], 1)  # Different delays: 2s, 0s, 1s
    ]

    print("Processing responses as they complete (not in order)...\n")

    # Process results as they become available
    for completed in asyncio.as_completed(tasks):
        response = await completed
        data = response.json()
        request_id = data['args']['id']
        print(f"  Received response for request {request_id}")

    print()


async def example_client_reuse():
    """Reuse client for multiple concurrent requests."""
    print("=== Client Reuse for Concurrent Requests ===\n")

    async with AsyncCycleTLS() as client:
        print("Making 10 concurrent requests with shared client...")

        tasks = [
            client.get(f"https://httpbin.org/get?request={i}")
            for i in range(10)
        ]

        responses = await asyncio.gather(*tasks)

        print(f"Completed {len(responses)} requests")
        print(f"All successful: {all(r.status_code == 200 for r in responses)}\n")


async def example_nested_concurrency():
    """Nested concurrent operations."""
    print("=== Nested Concurrency ===\n")

    async def fetch_user_data(user_id: int):
        """Fetch multiple pieces of data for a user concurrently."""
        print(f"  Fetching data for user {user_id}...")

        # For each user, fetch multiple endpoints concurrently
        profile_task = cycletls.aget(f"https://httpbin.org/get?user={user_id}&type=profile")
        posts_task = cycletls.aget(f"https://httpbin.org/get?user={user_id}&type=posts")
        friends_task = cycletls.aget(f"https://httpbin.org/get?user={user_id}&type=friends")

        responses = await asyncio.gather(profile_task, posts_task, friends_task)

        print(f"  Completed data for user {user_id}")
        return {
            'user_id': user_id,
            'profile': responses[0].status_code,
            'posts': responses[1].status_code,
            'friends': responses[2].status_code,
        }

    # Fetch data for multiple users concurrently
    # Each user's data is also fetched concurrently
    print("Fetching data for 3 users (3 requests each = 9 total)...\n")

    user_data = await asyncio.gather(*[
        fetch_user_data(user_id) for user_id in [1, 2, 3]
    ])

    print(f"\nFetched data for {len(user_data)} users")
    for data in user_data:
        print(f"  User {data['user_id']}: Profile={data['profile']}, "
              f"Posts={data['posts']}, Friends={data['friends']}")

    print()


async def example_timeout_handling():
    """Handle timeouts in concurrent requests."""
    print("=== Timeout Handling ===\n")

    print("Making requests with timeout...\n")

    tasks = [
        cycletls.aget("https://httpbin.org/delay/1", timeout=5),   # Fast, will succeed
        cycletls.aget("https://httpbin.org/delay/10", timeout=2),  # Slow, will timeout
        cycletls.aget("https://httpbin.org/delay/1", timeout=5),   # Fast, will succeed
    ]

    # Use return_exceptions to handle timeouts gracefully
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            print(f"  Request {i}: Timed out")
        else:
            print(f"  Request {i}: Success (status {result.status_code})")

    print()


async def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("CycleTLS Async Concurrent Examples")
    print("="*60 + "\n")

    await example_basic_concurrent()
    await example_performance_comparison()
    await example_mixed_methods()
    await example_batch_processing()
    await example_rate_limiting()
    await example_error_handling()
    await example_as_completed()
    await example_client_reuse()
    await example_nested_concurrency()
    await example_timeout_handling()

    print("="*60)
    print("All examples completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
