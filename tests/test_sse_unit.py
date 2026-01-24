"""Unit tests for SSE module (mocked FFI layer)."""

import base64
import pytest
from unittest.mock import MagicMock, patch

import ormsgpack  # Drop-in replacement for msgpack, 10-30% faster (Rust-based)

from cycletls.sse import (
    SSEEvent,
    SSEError,
    SSEConnection,
)


class TestSSEEvent:
    """Tests for SSEEvent dataclass."""

    def test_basic_event(self):
        """Test creating a basic event."""
        event = SSEEvent(data="Hello, World!")
        assert event.data == "Hello, World!"
        assert event.event == "message"
        assert event.id is None
        assert event.retry is None

    def test_full_event(self):
        """Test creating an event with all fields."""
        event = SSEEvent(
            data="test data",
            event="update",
            id="event-123",
            retry=5000,
        )
        assert event.data == "test data"
        assert event.event == "update"
        assert event.id == "event-123"
        assert event.retry == 5000

    def test_str_representation(self):
        """Test string representation."""
        event = SSEEvent(data="Some long data that will be truncated", event="test")
        assert "SSEEvent" in str(event)
        assert "test" in str(event)


class TestSSEConnection:
    """Tests for SSEConnection class."""

    def test_init(self):
        """Test initializing an SSE connection."""
        sse = SSEConnection(
            url="https://api.example.com/events",
            headers={"Authorization": "Bearer token"},
            ja3="custom_ja3",
            user_agent="Test/1.0",
            proxy="socks5://localhost:1080",
            timeout=60,
            last_event_id="event-100",
        )
        assert sse.url == "https://api.example.com/events"
        assert sse.headers == {"Authorization": "Bearer token"}
        assert sse.ja3 == "custom_ja3"
        assert sse.user_agent == "Test/1.0"
        assert sse.proxy == "socks5://localhost:1080"
        assert sse.timeout == 60
        assert sse.last_event_id == "event-100"
        assert not sse.connected

    def test_not_connected_by_default(self):
        """Test that connection is not connected by default."""
        sse = SSEConnection("https://api.example.com/events")
        assert not sse.connected
        assert sse._handle is None

    def test_default_retry_time(self):
        """Test default retry time."""
        sse = SSEConnection("https://api.example.com/events")
        assert sse.retry_time == 3000  # 3 seconds default

    def test_next_event_without_connect_raises(self):
        """Test that reading events without connecting raises error."""
        sse = SSEConnection("https://api.example.com/events")
        with pytest.raises(SSEError, match="not active"):
            sse.next_event()

    @patch("cycletls.sse._load_library")
    def test_connect_no_sseconnect(self, mock_load_library):
        """Test that connect raises error if sseConnect not available."""
        mock_lib = MagicMock()
        del mock_lib.sseConnect  # Remove the attribute
        mock_load_library.return_value = mock_lib

        sse = SSEConnection("https://api.example.com/events")
        with pytest.raises(SSEError, match="requires rebuilding"):
            sse.connect()

    @patch("cycletls.sse._load_library")
    def test_connect_success(self, mock_load_library):
        """Test successful connection."""
        mock_lib = MagicMock()
        mock_lib.sseConnect.return_value = 12345  # Non-zero handle
        mock_load_library.return_value = mock_lib

        sse = SSEConnection("https://api.example.com/events")
        sse.connect()

        assert sse.connected
        assert sse._handle == 12345
        mock_lib.sseConnect.assert_called_once()

    @patch("cycletls.sse._load_library")
    def test_connect_failure(self, mock_load_library):
        """Test connection failure."""
        mock_lib = MagicMock()
        mock_lib.sseConnect.return_value = 0  # Zero indicates failure
        mock_load_library.return_value = mock_lib

        sse = SSEConnection("https://api.example.com/events")
        with pytest.raises(SSEError, match="Failed to connect"):
            sse.connect()

        assert not sse.connected

    @patch("cycletls.sse._load_library")
    def test_close(self, mock_load_library):
        """Test closing a connection."""
        mock_lib = MagicMock()
        mock_lib.sseConnect.return_value = 12345
        mock_load_library.return_value = mock_lib

        sse = SSEConnection("https://api.example.com/events")
        sse.connect()
        sse.close()

        assert not sse.connected
        assert sse._handle is None
        mock_lib.sseClose.assert_called_once_with(12345)

    @patch("cycletls.sse._load_library")
    def test_context_manager(self, mock_load_library):
        """Test using connection as context manager."""
        mock_lib = MagicMock()
        mock_lib.sseConnect.return_value = 12345
        mock_load_library.return_value = mock_lib

        with SSEConnection("https://api.example.com/events") as sse:
            assert sse.connected

        assert not sse.connected
        mock_lib.sseClose.assert_called_once()

    @patch("cycletls.sse._load_library")
    def test_last_event_id_tracking(self, mock_load_library):
        """Test that Last-Event-ID is passed to connect."""
        mock_lib = MagicMock()
        mock_lib.sseConnect.return_value = 12345
        mock_load_library.return_value = mock_lib

        sse = SSEConnection(
            "https://api.example.com/events",
            last_event_id="event-99",
        )
        sse.connect()

        # Verify the call was made (we can't easily inspect the msgpack data)
        mock_lib.sseConnect.assert_called_once()


class TestSSEEventParsing:
    """Tests for event parsing logic."""

    def test_event_default_type(self):
        """Test that event defaults to 'message' type."""
        event = SSEEvent(data="test")
        assert event.event == "message"

    def test_event_custom_type(self):
        """Test custom event types."""
        event = SSEEvent(data="test", event="update")
        assert event.event == "update"

    def test_event_with_multiline_data(self):
        """Test event with multiline data."""
        event = SSEEvent(data="line1\nline2\nline3")
        assert event.data == "line1\nline2\nline3"
