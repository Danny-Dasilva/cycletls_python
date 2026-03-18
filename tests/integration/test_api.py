import os
import pytest
from cycletls import CycleTLS, Request

_TRACKME_URL = os.environ.get("TRACKME_URL", "https://tls.peet.ws")

@pytest.fixture
def simple_request():
    """returns a simple request interface"""
    return Request(url=f"{_TRACKME_URL}/api/clean", method="get")

def test_api_call():
    cycle = CycleTLS()
    result = cycle.get(f"{_TRACKME_URL}/api/clean")
    
    cycle.close()
    assert result.status_code == 200

