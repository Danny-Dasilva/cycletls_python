"""Unit tests for WebSocket module (mocked FFI layer)."""

import base64
import pytest
from unittest.mock import MagicMock, patch

import ormsgpack  # Drop-in replacement for msgpack, 10-30% faster (Rust-based)

from cycletls.websocket import (
    MessageType,
    WebSocketMessage,
    WebSocketError,
    WebSocketConnection,
)


class TestMessageType:
    """Tests for MessageType enum."""

    def test_message_types(self):
        """Test message type values."""
        assert MessageType.TEXT == 1
        assert MessageType.BINARY == 2
        assert MessageType.CLOSE == 8
        assert MessageType.PING == 9
        assert MessageType.PONG == 10


class TestWebSocketMessage:
    """Tests for WebSocketMessage dataclass."""

    def test_text_message(self):
        """Test creating a text message."""
        msg = WebSocketMessage(type=MessageType.TEXT, data="Hello, World!")
        assert msg.is_text
        assert not msg.is_binary
        assert not msg.is_close
        assert msg.data == "Hello, World!"

    def test_binary_message(self):
        """Test creating a binary message."""
        msg = WebSocketMessage(type=MessageType.BINARY, data=b"\x00\x01\x02")
        assert not msg.is_text
        assert msg.is_binary
        assert not msg.is_close
        assert msg.data == b"\x00\x01\x02"

    def test_close_message(self):
        """Test creating a close message."""
        msg = WebSocketMessage(type=MessageType.CLOSE, data="")
        assert not msg.is_text
        assert not msg.is_binary
        assert msg.is_close


class TestWebSocketConnection:
    """Tests for WebSocketConnection class."""

    def test_init(self):
        """Test initializing a WebSocket connection."""
        ws = WebSocketConnection(
            url="wss://example.com/socket",
            headers={"Authorization": "Bearer token"},
            ja3="custom_ja3",
            user_agent="Test/1.0",
            proxy="socks5://localhost:1080",
            timeout=60,
        )
        assert ws.url == "wss://example.com/socket"
        assert ws.headers == {"Authorization": "Bearer token"}
        assert ws.ja3 == "custom_ja3"
        assert ws.user_agent == "Test/1.0"
        assert ws.proxy == "socks5://localhost:1080"
        assert ws.timeout == 60
        assert not ws.connected

    def test_not_connected_by_default(self):
        """Test that connection is not connected by default."""
        ws = WebSocketConnection("wss://example.com")
        assert not ws.connected
        assert ws._handle is None

    def test_send_without_connect_raises(self):
        """Test that sending without connecting raises error."""
        ws = WebSocketConnection("wss://example.com")
        with pytest.raises(WebSocketError, match="not connected"):
            ws.send("test")

    def test_receive_without_connect_raises(self):
        """Test that receiving without connecting raises error."""
        ws = WebSocketConnection("wss://example.com")
        with pytest.raises(WebSocketError, match="not connected"):
            ws.receive()

    @patch("cycletls.websocket._load_library")
    def test_connect_no_wsconnect(self, mock_load_library):
        """Test that connect raises error if wsConnect not available."""
        mock_lib = MagicMock()
        del mock_lib.wsConnect  # Remove the attribute
        mock_load_library.return_value = mock_lib

        ws = WebSocketConnection("wss://example.com")
        with pytest.raises(WebSocketError, match="requires rebuilding"):
            ws.connect()

    @patch("cycletls.websocket._load_library")
    def test_connect_success(self, mock_load_library):
        """Test successful connection."""
        mock_lib = MagicMock()
        mock_lib.wsConnect.return_value = 12345  # Non-zero handle
        mock_load_library.return_value = mock_lib

        ws = WebSocketConnection("wss://example.com")
        ws.connect()

        assert ws.connected
        assert ws._handle == 12345
        mock_lib.wsConnect.assert_called_once()

    @patch("cycletls.websocket._load_library")
    def test_connect_failure(self, mock_load_library):
        """Test connection failure."""
        mock_lib = MagicMock()
        mock_lib.wsConnect.return_value = 0  # Zero indicates failure
        mock_load_library.return_value = mock_lib

        ws = WebSocketConnection("wss://example.com")
        with pytest.raises(WebSocketError, match="Failed to connect"):
            ws.connect()

        assert not ws.connected

    @patch("cycletls.websocket._load_library")
    def test_close(self, mock_load_library):
        """Test closing a connection."""
        mock_lib = MagicMock()
        mock_lib.wsConnect.return_value = 12345
        mock_load_library.return_value = mock_lib

        ws = WebSocketConnection("wss://example.com")
        ws.connect()
        ws.close()

        assert not ws.connected
        assert ws._handle is None
        mock_lib.wsClose.assert_called_once_with(12345)

    @patch("cycletls.websocket._load_library")
    def test_context_manager(self, mock_load_library):
        """Test using connection as context manager."""
        mock_lib = MagicMock()
        mock_lib.wsConnect.return_value = 12345
        mock_load_library.return_value = mock_lib

        with WebSocketConnection("wss://example.com") as ws:
            assert ws.connected

        assert not ws.connected
        mock_lib.wsClose.assert_called_once()


class TestWebSocketMessageParsing:
    """Tests for message parsing logic."""

    def test_message_type_from_int(self):
        """Test creating MessageType from integer."""
        assert MessageType(1) == MessageType.TEXT
        assert MessageType(2) == MessageType.BINARY
        assert MessageType(8) == MessageType.CLOSE
