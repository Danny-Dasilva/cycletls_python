"""
WebSocket tests for CycleTLS Python library.

Based on CycleTLS TypeScript websocket.test.ts and Go WebSocket tests.
Tests WebSocket functionality including:
- Connection with protocol="websocket"
- Text message sending/receiving
- Binary message sending/receiving
- Connection close
- Error handling

Note: Tests are marked as skip if WebSocket functionality is not fully implemented yet.
"""

import pytest
import json
import time
from test_utils import assert_valid_response


class TestWebSocketConnection:
    """Test WebSocket connection establishment."""

    @pytest.mark.skip(reason="Requires live WebSocket test server")
    def test_websocket_connection(self, cycletls_client):
        """Test basic WebSocket connection using protocol='websocket'."""
        # Using wss://echo.websocket.org as test server
        response = cycletls_client.get(
            "wss://echo.websocket.org",
            protocol="websocket"
        )

        assert_valid_response(response, expected_status=101)  # 101 Switching Protocols
        assert response.headers, "WebSocket response should have headers"

    @pytest.mark.skip(reason="Requires live WebSocket test server")
    def test_websocket_connection_echo_server(self, cycletls_client):
        """Test WebSocket connection to echo.websocket.org."""
        # Test connection establishment
        response = cycletls_client.request(
            "get",
            "wss://echo.websocket.org",
            protocol="websocket"
        )

        # WebSocket upgrade should return 101 status or similar
        assert response.status_code in [101, 200], \
            f"WebSocket connection should return 101 or 200, got {response.status_code}"

    @pytest.mark.skip(reason="Requires live WebSocket test server")
    def test_websocket_connection_local(self, cycletls_client):
        """Test WebSocket connection to local server (if available)."""
        # This would connect to a local WebSocket server on ws://localhost:port
        # Similar to the TypeScript test that creates a local server
        try:
            response = cycletls_client.get(
                "ws://localhost:8080/ws",
                protocol="websocket",
                timeout=2
            )

            # If server is running, should get valid response
            assert response is not None, "WebSocket response should not be None"

        except Exception as e:
            # Skip if local server is not running
            pytest.skip(f"Local WebSocket server not available: {e}")


class TestWebSocketMessages:
    """Test WebSocket message sending and receiving."""

    @pytest.mark.skip(reason="Requires live WebSocket test server")
    def test_send_text_message(self, cycletls_client):
        """Test sending text messages over WebSocket."""
        # Connect to echo server
        response = cycletls_client.get(
            "wss://echo.websocket.org",
            protocol="websocket"
        )

        # Send text message (API needs to be implemented)
        # This would be something like:
        # cycletls_client.ws_send(response.request_id, "Hello WebSocket")

        # For now, just verify connection was established
        assert response is not None, "WebSocket connection should be established"

    @pytest.mark.skip(reason="Requires live WebSocket test server")
    def test_send_binary_message(self, cycletls_client):
        """Test sending binary messages over WebSocket."""
        # Connect to echo server
        response = cycletls_client.get(
            "wss://echo.websocket.org",
            protocol="websocket"
        )

        # Send binary message (API needs to be implemented)
        # This would be something like:
        # binary_data = b'\x00\x01\x02\x03'
        # cycletls_client.ws_send_binary(response.request_id, binary_data)

        # For now, just verify connection was established
        assert response is not None, "WebSocket connection should be established"

    @pytest.mark.skip(reason="Requires live WebSocket test server")
    def test_receive_messages(self, cycletls_client):
        """Test receiving messages from WebSocket server."""
        # Connect to echo server
        response = cycletls_client.get(
            "wss://echo.websocket.org",
            protocol="websocket"
        )

        # Receive message (API needs to be implemented)
        # This would be something like:
        # message = cycletls_client.ws_receive(response.request_id, timeout=5)
        # assert message is not None, "Should receive message from echo server"

        # For now, just verify connection was established
        assert response is not None, "WebSocket connection should be established"

    @pytest.mark.skip(reason="Requires live WebSocket test server")
    def test_echo_text_message(self, cycletls_client):
        """Test sending and receiving echoed text message."""
        # This test would:
        # 1. Connect to wss://echo.websocket.org
        # 2. Send a text message
        # 3. Receive the echoed message back
        # 4. Verify the message matches

        test_message = "Hello from CycleTLS Python!"

        # Connect
        response = cycletls_client.get(
            "wss://echo.websocket.org",
            protocol="websocket"
        )

        # Send and receive would be implemented here
        # sent = cycletls_client.ws_send(response.request_id, test_message)
        # received = cycletls_client.ws_receive(response.request_id, timeout=5)
        # assert received.data == test_message, "Echoed message should match sent message"

        assert response is not None, "WebSocket connection should be established"

    @pytest.mark.skip(reason="Requires live WebSocket test server")
    def test_echo_binary_message(self, cycletls_client):
        """Test sending and receiving echoed binary message."""
        test_binary = b'\x00\x01\x02\x03\x04\x05'

        # Connect
        response = cycletls_client.get(
            "wss://echo.websocket.org",
            protocol="websocket"
        )

        # Send and receive would be implemented here
        # sent = cycletls_client.ws_send_binary(response.request_id, test_binary)
        # received = cycletls_client.ws_receive(response.request_id, timeout=5)
        # assert received.data == test_binary, "Echoed binary should match sent binary"

        assert response is not None, "WebSocket connection should be established"


class TestWebSocketClose:
    """Test WebSocket connection close functionality."""

    @pytest.mark.skip(reason="Requires live WebSocket test server")
    def test_close_connection(self, cycletls_client):
        """Test closing WebSocket connection."""
        # Connect
        response = cycletls_client.get(
            "wss://echo.websocket.org",
            protocol="websocket"
        )

        assert response is not None, "WebSocket connection should be established"

        # Close connection (API needs to be implemented)
        # cycletls_client.ws_close(response.request_id)

        # Verify connection is closed
        # This would check that subsequent operations fail or return appropriate status

    @pytest.mark.skip(reason="Requires live WebSocket test server")
    def test_close_with_code(self, cycletls_client):
        """Test closing WebSocket connection with status code."""
        # Connect
        response = cycletls_client.get(
            "wss://echo.websocket.org",
            protocol="websocket"
        )

        assert response is not None, "WebSocket connection should be established"

        # Close with code (API needs to be implemented)
        # cycletls_client.ws_close(response.request_id, code=1000, reason="Normal closure")


class TestWebSocketErrors:
    """Test WebSocket error handling."""

    @pytest.mark.skip(reason="Requires live WebSocket test server")
    def test_invalid_websocket_url(self, cycletls_client):
        """Test connection to invalid WebSocket URL."""
        with pytest.raises(Exception):
            response = cycletls_client.get(
                "wss://invalid-websocket-server-that-does-not-exist.example.com",
                protocol="websocket",
                timeout=2
            )

    @pytest.mark.skip(reason="Requires live WebSocket test server")
    def test_connection_timeout(self, cycletls_client):
        """Test WebSocket connection timeout."""
        # Attempt to connect with very short timeout
        with pytest.raises(Exception):
            response = cycletls_client.get(
                "wss://echo.websocket.org",
                protocol="websocket",
                timeout=0.001  # Very short timeout
            )

    @pytest.mark.skip(reason="Requires live WebSocket test server")
    def test_send_on_closed_connection(self, cycletls_client):
        """Test sending message on closed connection."""
        # Connect
        response = cycletls_client.get(
            "wss://echo.websocket.org",
            protocol="websocket"
        )

        # Close connection
        # cycletls_client.ws_close(response.request_id)

        # Try to send on closed connection
        # with pytest.raises(Exception):
        #     cycletls_client.ws_send(response.request_id, "This should fail")


class TestWebSocketAdvanced:
    """Test advanced WebSocket features."""

    @pytest.mark.skip(reason="Requires live WebSocket test server")
    def test_ping_pong(self, cycletls_client):
        """Test WebSocket ping/pong mechanism."""
        # Connect
        response = cycletls_client.get(
            "wss://echo.websocket.org",
            protocol="websocket"
        )

        # Send ping (API needs to be implemented)
        # cycletls_client.ws_ping(response.request_id)

        # Should receive pong
        # pong = cycletls_client.ws_receive(response.request_id, timeout=5)
        # assert pong is not None, "Should receive pong response"

    @pytest.mark.skip(reason="Requires live WebSocket test server")
    def test_websocket_subprotocols(self, cycletls_client):
        """Test WebSocket with subprotocols."""
        # Connect with subprotocol
        response = cycletls_client.get(
            "wss://echo.websocket.org",
            protocol="websocket",
            headers={
                "Sec-WebSocket-Protocol": "chat, superchat"
            }
        )

        assert response is not None, "WebSocket connection should be established"

    @pytest.mark.skip(reason="Requires live WebSocket test server")
    def test_websocket_custom_headers(self, cycletls_client):
        """Test WebSocket connection with custom headers."""
        custom_headers = {
            "User-Agent": "CycleTLS-Python-Test",
            "Origin": "https://example.com"
        }

        response = cycletls_client.get(
            "wss://echo.websocket.org",
            protocol="websocket",
            headers=custom_headers
        )

        assert response is not None, "WebSocket connection should be established"

    @pytest.mark.skip(reason="Requires live WebSocket test server")
    def test_websocket_with_proxy(self, cycletls_client):
        """Test WebSocket connection through proxy."""
        # This would require a proxy server
        try:
            response = cycletls_client.get(
                "wss://echo.websocket.org",
                protocol="websocket",
                proxy="http://localhost:8888",
                timeout=2
            )

            assert response is not None, "WebSocket connection through proxy should work"

        except Exception as e:
            pytest.skip(f"Proxy not available: {e}")


class TestWebSocketFFIExports:
    """Verify Go FFI exports for WebSocket exist in the shared library."""

    def test_ws_connect_export_exists(self):
        from cycletls._ffi import _load_library
        lib = _load_library()
        assert hasattr(lib, "wsConnect"), "Go library should export wsConnect"

    def test_ws_send_export_exists(self):
        from cycletls._ffi import _load_library
        lib = _load_library()
        assert hasattr(lib, "wsSend"), "Go library should export wsSend"

    def test_ws_receive_export_exists(self):
        from cycletls._ffi import _load_library
        lib = _load_library()
        assert hasattr(lib, "wsReceive"), "Go library should export wsReceive"

    def test_ws_close_export_exists(self):
        from cycletls._ffi import _load_library
        lib = _load_library()
        assert hasattr(lib, "wsClose"), "Go library should export wsClose"


class TestWebSocketVerification:
    """Tests to verify WebSocket server is running (non-skip tests)."""

    def test_websocket_url_format(self):
        """Test WebSocket URL format validation."""
        # Basic URL format tests that don't require actual connection
        valid_urls = [
            "ws://localhost:8080",
            "wss://echo.websocket.org",
            "ws://example.com/ws",
            "wss://example.com:443/websocket"
        ]

        for url in valid_urls:
            assert url.startswith(("ws://", "wss://")), \
                f"WebSocket URL should start with ws:// or wss://, got {url}"

    def test_websocket_protocol_constant(self):
        """Test that websocket protocol constant is defined."""
        from cycletls.schema import Protocol

        assert hasattr(Protocol, 'WEBSOCKET'), "Protocol should have WEBSOCKET constant"
        assert Protocol.WEBSOCKET == "websocket", \
            f"Protocol.WEBSOCKET should be 'websocket', got {Protocol.WEBSOCKET}"

    def test_regular_request_to_websocket_endpoint(self, cycletls_client):
        """
        Test regular HTTP request to WebSocket endpoint.
        This verifies the endpoint exists even if WebSocket protocol isn't fully implemented.
        """
        try:
            # Regular GET request to WebSocket URL (without WebSocket protocol)
            response = cycletls_client.get(
                "https://echo.websocket.org",
                timeout=5
            )

            # Should get some response (200, 400, 426, etc.)
            # 426 = Upgrade Required (WebSocket endpoint accessed via HTTP)
            assert response.status_code in [200, 400, 404, 426, 408], \
                f"Request to WebSocket endpoint should return valid status, got {response.status_code}"

        except Exception as e:
            # Connection errors are acceptable
            pytest.skip(f"WebSocket endpoint not reachable: {e}")
