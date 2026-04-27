import os

import pytest

from cycletls import CycleTLS, Request

_TLSFP_URL = os.environ.get("TLSFP_URL", "https://tls.peet.ws")

@pytest.fixture
def simple_request():
    """returns a simple request interface"""
    return Request(url=f"{_TLSFP_URL}/api/clean", method="get")

def test_api_call():
    cycle = CycleTLS()
    result = cycle.get(f"{_TLSFP_URL}/api/clean")

    cycle.close()
    assert result.status_code == 200

