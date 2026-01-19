"""Simple demonstration of the CycleTLS client."""

import cycletls
from pprint import pprint

# Use module-level get function (simplest API)
response = cycletls.get('http://localhost:5001/')
print(f"Status: {response.status_code}")
print(f"Success: {response.ok}")

# Use .text property for response text
try:
    pprint(response.text)
except Exception as e:
    print(f"Error: {e}")

# Or use .json() method for JSON responses
try:
    data = response.json()
    print("JSON response:")
    pprint(data)
except Exception:
    pass
