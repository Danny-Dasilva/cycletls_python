#!/usr/bin/env python3
"""Test if _merge_defaults caching is working."""

import os
import sys
import time

os.environ["CYCLETLS_LIB_PATH"] = (
    "/Users/dannydasilva/Documents/personal/cycletls_python/dist/libcycletls.dylib"
)
sys.path.insert(0, "/Users/dannydasilva/Documents/personal/cycletls_python")

from cycletls._config import _merge_defaults, _merged_cache

print("Testing _merge_defaults caching...")
print()

# Test 1: Empty kwargs (should use cache after first call)
print("Test 1: Empty kwargs (should use cache)")
start = time.time()
for i in range(10000):
    result = _merge_defaults({})
elapsed = time.time() - start
print(f"  Time for 10k calls with empty kwargs: {elapsed:.4f}s")
print(f"  Avg time per call: {elapsed / 10000 * 1000000:.2f}μs")
print(f"  Cache value: {_merged_cache}")
print()

# Test 2: Non-empty kwargs (should not use cache)
print("Test 2: Non-empty kwargs (should not use cache)")
start = time.time()
for i in range(10000):
    result = _merge_defaults({"timeout": 10})
elapsed = time.time() - start
print(f"  Time for 10k calls with kwargs: {elapsed:.4f}s")
print(f"  Avg time per call: {elapsed / 10000 * 1000000:.2f}μs")
print()

# Test 3: Verify cache is used
print("Test 3: Verify cache is being used")
result1 = _merge_defaults({})
result2 = _merge_defaults({})
print(f"  Same object? {result1 is result2}")
print(f"  Should be True if cache is working")
print()

print("Done!")
