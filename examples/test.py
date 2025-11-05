"""Simple demonstration of the CycleTLS client."""

import json
import cycletls
from pprint import pprint
response = cycletls.get('http://localhost:5001/',)
print(response.status_code)

try:
    pprint(response.text)
except Exception:
    try:
        print(json.loads(response.body))
    except Exception:
        print(response.body)
