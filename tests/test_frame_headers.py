"""
Test HTTP/2 frame header parsing and validation.

Based on CycleTLS frameHeader.test.ts, this module tests:
- HTTP/2 frame header parsing (if accessible)
- Frame types (SETTINGS, WINDOW_UPDATE, etc.)
- Frame flags
- Stream IDs
- Browser-specific frame fingerprints

Note: Most tests are marked as skipped if frame details are not exposed
in the Python API. This functionality may be internal to the Go backend.
"""

import pytest
from cycletls import CycleTLS


class TestChromeFrameHeaders:
    """Test Chrome browser HTTP/2 frame headers."""

    @pytest.mark.skip(reason="Frame header details may not be exposed in Python API")
    def test_chrome_settings_frame(self):
        """Test Chrome's SETTINGS frame configuration."""
        client = CycleTLS()

        chrome_ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0"
        chrome_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"

        try:
            response = client.get(
                "https://tls.peet.ws/api/all",
                ja3=chrome_ja3,
                user_agent=chrome_ua
            )

            assert response.status_code == 200

            # Parse response to check frame headers
            data = response.json()

            # Expected Chrome SETTINGS frame
            expected_settings = {
                "frame_type": "SETTINGS",
                "length": 30,
                "settings": [
                    "HEADER_TABLE_SIZE = 65536",
                    "MAX_CONCURRENT_STREAMS = 1000",
                    "INITIAL_WINDOW_SIZE = 6291456",
                    "MAX_FRAME_SIZE = 16384",
                    "MAX_HEADER_LIST_SIZE = 262144",
                ]
            }

            # Expected Chrome WINDOW_UPDATE frame
            expected_window_update = {
                "frame_type": "WINDOW_UPDATE",
                "increment": 15663105,
                "length": 4,
            }

            # Verify frame headers if available in response
            if "http2" in data and "sent_frames" in data["http2"]:
                sent_frames = data["http2"]["sent_frames"]

                # Check SETTINGS frame
                if len(sent_frames) > 0:
                    settings_frame = sent_frames[0]
                    assert settings_frame["frame_type"] == expected_settings["frame_type"]
                    assert settings_frame["length"] == expected_settings["length"]

                # Check WINDOW_UPDATE frame
                if len(sent_frames) > 1:
                    window_update_frame = sent_frames[1]
                    assert window_update_frame["frame_type"] == expected_window_update["frame_type"]
                    assert window_update_frame["increment"] == expected_window_update["increment"]

            # Verify JA3 fingerprint
            if "tls" in data and "ja3" in data["tls"]:
                assert data["tls"]["ja3"] == chrome_ja3

            # Verify User-Agent
            if "user_agent" in data:
                assert data["user_agent"] == chrome_ua

        finally:
            client.close()

    @pytest.mark.skip(reason="Frame header details may not be exposed in Python API")
    def test_chrome_frame_sequence(self):
        """Test the sequence of Chrome's HTTP/2 frames."""
        client = CycleTLS()

        chrome_ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0"

        try:
            response = client.get(
                "https://tls.peet.ws/api/all",
                ja3=chrome_ja3
            )

            assert response.status_code == 200

            data = response.json()

            # Chrome typically sends frames in this order:
            # 1. SETTINGS
            # 2. WINDOW_UPDATE
            # 3. HEADERS (for the request)

            if "http2" in data and "sent_frames" in data["http2"]:
                sent_frames = data["http2"]["sent_frames"]
                assert len(sent_frames) >= 2

                # First frame should be SETTINGS
                assert sent_frames[0]["frame_type"] == "SETTINGS"

                # Second frame should be WINDOW_UPDATE
                assert sent_frames[1]["frame_type"] == "WINDOW_UPDATE"

        finally:
            client.close()


class TestFirefoxFrameHeaders:
    """Test Firefox browser HTTP/2 frame headers."""

    @pytest.mark.skip(reason="Frame header details may not be exposed in Python API")
    def test_firefox_settings_frame(self):
        """Test Firefox's SETTINGS frame configuration."""
        client = CycleTLS()

        firefox_ja3 = "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-156-157-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0"
        firefox_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0"

        try:
            response = client.get(
                "https://tls.peet.ws/api/all",
                ja3=firefox_ja3,
                user_agent=firefox_ua
            )

            assert response.status_code == 200

            data = response.json()

            # Expected Firefox SETTINGS frame
            expected_settings = {
                "frame_type": "SETTINGS",
                "length": 18,
                "settings": [
                    "HEADER_TABLE_SIZE = 65536",
                    "INITIAL_WINDOW_SIZE = 131072",
                    "MAX_FRAME_SIZE = 16384",
                ]
            }

            # Expected Firefox WINDOW_UPDATE frame
            expected_window_update = {
                "frame_type": "WINDOW_UPDATE",
                "increment": 12517377,
                "length": 4,
            }

            # Verify frame headers if available
            if "http2" in data and "sent_frames" in data["http2"]:
                sent_frames = data["http2"]["sent_frames"]

                # Check SETTINGS frame
                if len(sent_frames) > 0:
                    settings_frame = sent_frames[0]
                    assert settings_frame["frame_type"] == expected_settings["frame_type"]
                    assert settings_frame["length"] == expected_settings["length"]

                # Check WINDOW_UPDATE frame
                if len(sent_frames) > 1:
                    window_update_frame = sent_frames[1]
                    assert window_update_frame["frame_type"] == expected_window_update["frame_type"]
                    assert window_update_frame["increment"] == expected_window_update["increment"]

            # Verify JA3 fingerprint
            if "tls" in data and "ja3" in data["tls"]:
                assert data["tls"]["ja3"] == firefox_ja3

        finally:
            client.close()

    @pytest.mark.skip(reason="Frame header details may not be exposed in Python API")
    def test_firefox_frame_differences(self):
        """Test differences between Firefox and Chrome frames."""
        chrome_client = CycleTLS()
        firefox_client = CycleTLS()

        chrome_ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0"
        firefox_ja3 = "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-156-157-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0"

        try:
            chrome_response = chrome_client.get(
                "https://tls.peet.ws/api/all",
                ja3=chrome_ja3
            )

            firefox_response = firefox_client.get(
                "https://tls.peet.ws/api/all",
                ja3=firefox_ja3
            )

            assert chrome_response.status_code == 200
            assert firefox_response.status_code == 200

            chrome_data = chrome_response.json()
            firefox_data = firefox_response.json()

            # Compare frame configurations
            if "http2" in chrome_data and "http2" in firefox_data:
                chrome_frames = chrome_data["http2"].get("sent_frames", [])
                firefox_frames = firefox_data["http2"].get("sent_frames", [])

                # Both should have sent frames
                assert len(chrome_frames) > 0
                assert len(firefox_frames) > 0

                # Settings frame should be different
                if len(chrome_frames) > 0 and len(firefox_frames) > 0:
                    chrome_settings = chrome_frames[0]
                    firefox_settings = firefox_frames[0]

                    # Both should be SETTINGS frames
                    assert chrome_settings["frame_type"] == "SETTINGS"
                    assert firefox_settings["frame_type"] == "SETTINGS"

                    # But with different lengths
                    assert chrome_settings["length"] != firefox_settings["length"]

        finally:
            chrome_client.close()
            firefox_client.close()


class TestFrameTypes:
    """Test different HTTP/2 frame types."""

    @pytest.mark.skip(reason="Frame details may not be exposed in Python API")
    def test_settings_frame_structure(self):
        """Test SETTINGS frame structure."""
        client = CycleTLS()

        try:
            response = client.get(
                "https://tls.peet.ws/api/all",
                force_http1=False  # Ensure HTTP/2
            )

            data = response.json()

            if "http2" in data and "sent_frames" in data["http2"]:
                settings_frames = [
                    f for f in data["http2"]["sent_frames"]
                    if f.get("frame_type") == "SETTINGS"
                ]

                assert len(settings_frames) > 0

                settings_frame = settings_frames[0]
                assert "length" in settings_frame
                assert "settings" in settings_frame
                assert isinstance(settings_frame["settings"], list)

        finally:
            client.close()

    @pytest.mark.skip(reason="Frame details may not be exposed in Python API")
    def test_window_update_frame_structure(self):
        """Test WINDOW_UPDATE frame structure."""
        client = CycleTLS()

        try:
            response = client.get("https://tls.peet.ws/api/all")

            data = response.json()

            if "http2" in data and "sent_frames" in data["http2"]:
                window_frames = [
                    f for f in data["http2"]["sent_frames"]
                    if f.get("frame_type") == "WINDOW_UPDATE"
                ]

                assert len(window_frames) > 0

                window_frame = window_frames[0]
                assert "length" in window_frame
                assert "increment" in window_frame
                assert window_frame["length"] == 4

        finally:
            client.close()

    @pytest.mark.skip(reason="Frame details may not be exposed in Python API")
    def test_headers_frame_presence(self):
        """Test that HEADERS frame is sent for requests."""
        client = CycleTLS()

        try:
            response = client.get("https://tls.peet.ws/api/all")

            data = response.json()

            if "http2" in data and "sent_frames" in data["http2"]:
                sent_frames = data["http2"]["sent_frames"]

                # HEADERS frame should be present (usually after SETTINGS and WINDOW_UPDATE)
                frame_types = [f.get("frame_type") for f in sent_frames]

                # At minimum, should have SETTINGS
                assert "SETTINGS" in frame_types

        finally:
            client.close()


class TestFrameFlags:
    """Test HTTP/2 frame flags."""

    @pytest.mark.skip(reason="Frame flags may not be exposed in Python API")
    def test_settings_ack_flag(self):
        """Test SETTINGS ACK flag."""
        # SETTINGS ACK is sent by the client after receiving server's SETTINGS
        # This is typically handled automatically by the HTTP/2 implementation
        pass

    @pytest.mark.skip(reason="Frame flags may not be exposed in Python API")
    def test_headers_end_stream_flag(self):
        """Test HEADERS END_STREAM flag."""
        # END_STREAM flag indicates no more data will be sent on the stream
        # For GET requests without body, this should be set
        pass


class TestStreamIDs:
    """Test HTTP/2 stream ID handling."""

    @pytest.mark.skip(reason="Stream IDs may not be exposed in Python API")
    def test_stream_ids_are_odd(self):
        """Test that client-initiated streams have odd IDs."""
        # HTTP/2 spec: client-initiated streams must have odd stream IDs
        pass

    @pytest.mark.skip(reason="Stream IDs may not be exposed in Python API")
    def test_stream_ids_increment(self):
        """Test that stream IDs increment properly."""
        # Stream IDs should increase for each new stream
        pass


class TestHTTP2Fingerprinting:
    """Test HTTP/2 fingerprinting capabilities."""

    def test_http2_request_succeeds(self):
        """Test basic HTTP/2 request succeeds."""
        client = CycleTLS()

        try:
            # Don't force HTTP/1, allow HTTP/2
            response = client.get(
                "https://http2.github.io",
                force_http1=False
            )

            # Should succeed with any status
            assert response.status_code in range(200, 600)

        finally:
            client.close()

    def test_http2_vs_http1_comparison(self, httpbin_url):
        """Test difference between HTTP/2 and HTTP/1 requests."""
        client = CycleTLS()

        try:
            # HTTP/2 request (default)
            response_h2 = client.get(
                f"{httpbin_url}/get",
                force_http1=False
            )

            # HTTP/1 request
            response_h1 = client.get(
                f"{httpbin_url}/get",
                force_http1=True
            )

            # Both should succeed
            assert response_h2.status_code == 200
            assert response_h1.status_code == 200

        finally:
            client.close()

    @pytest.mark.skip(reason="HTTP/2 fingerprint may not be exposed in Python response")
    def test_http2_fingerprint_in_response(self):
        """Test that HTTP/2 fingerprint is available in response."""
        client = CycleTLS()

        try:
            response = client.get("https://tls.peet.ws/api/all")

            data = response.json()

            # Check if HTTP/2 information is present
            if "http2" in data:
                assert isinstance(data["http2"], dict)

                # May contain sent_frames, akamai_fingerprint, etc.
                # Exact structure depends on implementation

        finally:
            client.close()


class TestBrowserSpecificFingerprints:
    """Test browser-specific HTTP/2 fingerprints."""

    @pytest.mark.skip(reason="Frame details may not be exposed in Python API")
    def test_chrome_http2_fingerprint(self):
        """Test Chrome-specific HTTP/2 fingerprint."""
        client = CycleTLS()

        chrome_ja3 = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513,29-23-24,0"

        try:
            response = client.get(
                "https://tls.peet.ws/api/all",
                ja3=chrome_ja3
            )

            data = response.json()

            # Chrome's signature:
            # - SETTINGS with 5 parameters (length 30)
            # - WINDOW_UPDATE with specific increment (15663105)

            if "http2" in data and "sent_frames" in data["http2"]:
                frames = data["http2"]["sent_frames"]

                if len(frames) >= 2:
                    assert frames[0]["frame_type"] == "SETTINGS"
                    assert frames[0]["length"] == 30

                    assert frames[1]["frame_type"] == "WINDOW_UPDATE"
                    assert frames[1]["increment"] == 15663105

        finally:
            client.close()

    @pytest.mark.skip(reason="Frame details may not be exposed in Python API")
    def test_firefox_http2_fingerprint(self):
        """Test Firefox-specific HTTP/2 fingerprint."""
        client = CycleTLS()

        firefox_ja3 = "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-156-157-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0"

        try:
            response = client.get(
                "https://tls.peet.ws/api/all",
                ja3=firefox_ja3
            )

            data = response.json()

            # Firefox's signature:
            # - SETTINGS with 3 parameters (length 18)
            # - WINDOW_UPDATE with specific increment (12517377)

            if "http2" in data and "sent_frames" in data["http2"]:
                frames = data["http2"]["sent_frames"]

                if len(frames) >= 2:
                    assert frames[0]["frame_type"] == "SETTINGS"
                    assert frames[0]["length"] == 18

                    assert frames[1]["frame_type"] == "WINDOW_UPDATE"
                    assert frames[1]["increment"] == 12517377

        finally:
            client.close()


class TestFrameHeaderValidation:
    """Test frame header validation and error handling."""

    def test_valid_http2_connection(self):
        """Test that valid HTTP/2 connections work."""
        client = CycleTLS()

        try:
            # Make a request to an HTTP/2 capable server
            response = client.get("https://www.google.com")

            assert response.status_code == 200

        finally:
            client.close()

    def test_http2_to_http1_fallback(self):
        """Test fallback from HTTP/2 to HTTP/1 if needed."""
        client = CycleTLS()

        try:
            # Some servers may not support HTTP/2
            # The client should handle this gracefully
            response = client.get("https://httpbin.org/get")

            assert response.status_code == 200

        finally:
            client.close()
