import pytest
from cycletls import CycleTLS, Request

@pytest.fixture
def simple_request():
    """returns a simple request interface"""
    return Request(url="https://tls.peet.ws/api/clean", method="get")

def test_api_call():
    cycle = CycleTLS()
    result = cycle.get("https://tls.peet.ws/api/clean")
    
    cycle.close()
    assert result.status_code == 200

