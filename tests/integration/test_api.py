import pytest
from cycletls import CycleTLS, Request

@pytest.fixture
def simple_request():
    """returns a simple request interface"""
    return Request(url="https://ja3er.com/json", method="get")

def test_api_call():
    cycle = CycleTLS()
    result = cycle.get("https://ja3er.com/json")
    
    cycle.close()
    assert result.status_code == 200

