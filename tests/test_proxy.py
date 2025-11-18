import pytest
import socket
import time
from cycletls import CycleTLS


def wait_for_proxy(host, port, timeout=5):
    """
    Wait for proxy to be ready by attempting to connect.

    Args:
        host: Proxy hostname/IP
        port: Proxy port
        timeout: Maximum time to wait in seconds

    Returns:
        bool: True if proxy is ready, False otherwise
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((host, port))
            sock.close()
            return True
        except (socket.error, socket.timeout):
            time.sleep(0.5)
    return False


def is_proxy_available(proxy_url):
    """
    Check if a proxy is available for testing.

    Args:
        proxy_url: Full proxy URL (e.g., "socks5://127.0.0.1:9050")

    Returns:
        bool: True if proxy is available, False otherwise
    """
    try:
        # Parse proxy URL to extract host and port
        parts = proxy_url.split("://")
        if len(parts) < 2:
            return False

        host_port = parts[1].split("@")[-1]  # Handle username:password@host:port
        host, port = host_port.rsplit(":", 1)

        return wait_for_proxy(host, int(port), timeout=2)
    except Exception:
        return False


@pytest.fixture
def client():
    """Create a CycleTLS client instance"""
    cycle = CycleTLS()
    yield cycle
    cycle.close()


@pytest.mark.skipif(
    not is_proxy_available("http://127.0.0.1:8080"),
    reason="HTTP proxy not available at 127.0.0.1:8080"
)
def test_http_proxy(client):
    """Test HTTP proxy connection"""
    proxy_url = "http://127.0.0.1:8080"

    result = client.get(
        "https://httpbin.org/ip",
        proxy=proxy_url,
        ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36"
    )

    assert result.status_code == 200
    # Verify response contains IP information
    assert "origin" in result.body.lower() or "ip" in result.body.lower()


@pytest.mark.skipif(
    not is_proxy_available("https://127.0.0.1:8443"),
    reason="HTTPS proxy not available at 127.0.0.1:8443"
)
def test_https_proxy(client):
    """Test HTTPS proxy connection"""
    proxy_url = "https://127.0.0.1:8443"

    result = client.get(
        "https://httpbin.org/ip",
        proxy=proxy_url,
        ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36"
    )

    assert result.status_code == 200
    assert "origin" in result.body.lower() or "ip" in result.body.lower()


@pytest.mark.skipif(
    not is_proxy_available("socks4://127.0.0.1:9050"),
    reason="SOCKS4 proxy not available at 127.0.0.1:9050"
)
def test_socks4_proxy(client):
    """Test SOCKS4 proxy connection"""
    proxy_url = "socks4://127.0.0.1:9050"

    # Wait for proxy to be ready
    assert wait_for_proxy("127.0.0.1", 9050, timeout=30), "SOCKS4 proxy not ready"

    result = client.get(
        "https://httpbin.org/ip",
        proxy=proxy_url,
        ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36"
    )

    assert result.status_code == 200
    assert "origin" in result.body.lower() or "ip" in result.body.lower()


@pytest.mark.skipif(
    not is_proxy_available("socks5://127.0.0.1:9050"),
    reason="SOCKS5 proxy not available at 127.0.0.1:9050"
)
def test_socks5_proxy(client):
    """Test SOCKS5 proxy connection"""
    proxy_url = "socks5://127.0.0.1:9050"

    # Wait for proxy to be ready
    assert wait_for_proxy("127.0.0.1", 9050, timeout=30), "SOCKS5 proxy not ready"

    result = client.get(
        "https://httpbin.org/ip",
        proxy=proxy_url,
        ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36"
    )

    assert result.status_code == 200
    assert "origin" in result.body.lower() or "ip" in result.body.lower()


@pytest.mark.skipif(
    not is_proxy_available("socks5://127.0.0.1:9050"),
    reason="SOCKS5 proxy not available at 127.0.0.1:9050"
)
def test_socks5h_proxy(client):
    """Test SOCKS5h proxy connection (hostname resolution via proxy)"""
    proxy_url = "socks5h://127.0.0.1:9050"

    # Wait for proxy to be ready
    assert wait_for_proxy("127.0.0.1", 9050, timeout=30), "SOCKS5h proxy not ready"

    result = client.get(
        "https://httpbin.org/ip",
        proxy=proxy_url,
        ja3="771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0",
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36"
    )

    assert result.status_code == 200
    assert "origin" in result.body.lower() or "ip" in result.body.lower()


def test_invalid_proxy_url(client):
    """Test error handling for invalid proxy URL"""
    with pytest.raises(Exception):
        client.get(
            "https://httpbin.org/ip",
            proxy="invalid://malformed:url:here"
        )


def test_unreachable_proxy(client):
    """Test error handling for unreachable proxy"""
    # Use a proxy that should not be reachable
    with pytest.raises(Exception):
        client.get(
            "https://httpbin.org/ip",
            proxy="http://127.0.0.1:1",  # Port 1 should not be open
            timeout=2
        )


def test_proxy_authentication_format(client):
    """Test proxy URL with authentication credentials format"""
    # This test verifies the format is accepted, even if proxy isn't available
    # It will skip if the proxy isn't available
    proxy_url = "http://username:password@127.0.0.1:8080"

    if not is_proxy_available(proxy_url):
        pytest.skip("Authenticated proxy not available")

    result = client.get(
        "https://httpbin.org/ip",
        proxy=proxy_url
    )

    assert result.status_code == 200


def test_no_proxy(client):
    """Test that requests work without proxy (baseline test)"""
    result = client.get("https://httpbin.org/ip")
    assert result.status_code == 200
    assert "origin" in result.body.lower() or "ip" in result.body.lower()


def test_proxy_with_post_request(client):
    """Test proxy functionality with POST request"""
    if not is_proxy_available("socks5://127.0.0.1:9050"):
        pytest.skip("SOCKS5 proxy not available")

    result = client.post(
        "https://httpbin.org/post",
        proxy="socks5://127.0.0.1:9050",
        json_data={"test": "data"}
    )

    assert result.status_code == 200


@pytest.mark.parametrize("proxy_type", [
    "http://127.0.0.1:8080",
    "https://127.0.0.1:8443",
    "socks4://127.0.0.1:9050",
    "socks5://127.0.0.1:9050",
])
def test_proxy_types_parametrized(client, proxy_type):
    """Parametrized test for different proxy types"""
    if not is_proxy_available(proxy_type):
        pytest.skip(f"Proxy {proxy_type} not available")

    result = client.get(
        "https://httpbin.org/ip",
        proxy=proxy_type
    )

    assert result.status_code == 200
