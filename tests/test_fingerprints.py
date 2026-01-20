"""Tests for the fingerprint plugin system."""

import json
import tempfile
from pathlib import Path

import pytest

from cycletls.fingerprints import (
    TLSFingerprint,
    FingerprintRegistry,
    CHROME_120,
    CHROME_121,
    FIREFOX_121,
    SAFARI_17,
    EDGE_120,
    CHROME_ANDROID,
    SAFARI_IOS,
)
from cycletls.plugins import (
    load_fingerprints_from_dir,
    load_fingerprint_from_file,
    create_fingerprint_template,
)


class TestTLSFingerprint:
    """Tests for TLSFingerprint dataclass."""

    def test_create_basic_fingerprint(self):
        """Test creating a basic fingerprint."""
        fp = TLSFingerprint(
            name="test_browser",
            ja3="771,4865-4866-4867,0-23-65281-10-11,29-23-24,0",
        )
        assert fp.name == "test_browser"
        assert fp.ja3.startswith("771")
        assert fp.user_agent is None

    def test_create_full_fingerprint(self):
        """Test creating a fingerprint with all options."""
        fp = TLSFingerprint(
            name="full_browser",
            ja3="771,4865-4866-4867,0-23-65281-10-11,29-23-24,0",
            ja4r="d41d8cd98f",
            http2_fingerprint="1:65536,2:0,3:1000",
            quic_fingerprint="test_quic",
            user_agent="Test/1.0",
            header_order=["host", "user-agent", "accept"],
            disable_grease=True,
            force_http1=False,
            force_http3=True,
        )
        assert fp.ja4r == "d41d8cd98f"
        assert fp.http2_fingerprint == "1:65536,2:0,3:1000"
        assert fp.user_agent == "Test/1.0"
        assert fp.header_order == ["host", "user-agent", "accept"]
        assert fp.disable_grease is True
        assert fp.force_http3 is True

    def test_from_dict(self):
        """Test creating fingerprint from dictionary."""
        data = {
            "name": "dict_browser",
            "ja3": "771,4865-4866-4867,0-23-65281-10-11,29-23-24,0",
            "user_agent": "Dict/1.0",
            "header_order": ["host", "accept"],
        }
        fp = TLSFingerprint.from_dict(data)
        assert fp.name == "dict_browser"
        assert fp.user_agent == "Dict/1.0"

    def test_to_dict(self):
        """Test converting fingerprint to dictionary."""
        fp = TLSFingerprint(
            name="test",
            ja3="771,4865-4866-4867,0-23-65281-10-11,29-23-24,0",
            user_agent="Test/1.0",
        )
        data = fp.to_dict()
        assert data["name"] == "test"
        assert data["ja3"].startswith("771")
        assert data["user_agent"] == "Test/1.0"
        # Optional None fields should not be included
        assert "ja4r" not in data
        assert "http2_fingerprint" not in data

    def test_from_json_and_to_json(self):
        """Test JSON serialization round-trip."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "name": "json_browser",
                    "ja3": "771,4865-4866-4867,0-23-65281-10-11,29-23-24,0",
                    "user_agent": "JSON/1.0",
                },
                f,
            )
            f.flush()

            fp = TLSFingerprint.from_json(f.name)
            assert fp.name == "json_browser"
            assert fp.user_agent == "JSON/1.0"

            # Test to_json
            output_path = Path(f.name).with_suffix(".out.json")
            fp.to_json(output_path)
            fp2 = TLSFingerprint.from_json(output_path)
            assert fp2.name == fp.name
            assert fp2.ja3 == fp.ja3

            # Cleanup
            output_path.unlink()
            Path(f.name).unlink()

    def test_apply_to_kwargs(self):
        """Test applying fingerprint to request kwargs."""
        fp = TLSFingerprint(
            name="test",
            ja3="custom_ja3",
            user_agent="Custom/1.0",
            header_order=["host", "accept"],
        )

        # Empty kwargs - should apply all
        kwargs = {}
        result = fp.apply_to_kwargs(kwargs)
        assert result["ja3"] == "custom_ja3"
        assert result["user_agent"] == "Custom/1.0"
        assert result["header_order"] == ["host", "accept"]

        # Kwargs with existing ja3 - should not override
        kwargs = {"ja3": "existing_ja3"}
        result = fp.apply_to_kwargs(kwargs)
        assert result["ja3"] == "existing_ja3"  # Not overridden
        assert result["user_agent"] == "Custom/1.0"  # Applied


class TestFingerprintRegistry:
    """Tests for FingerprintRegistry."""

    def test_builtin_profiles_registered(self):
        """Test that built-in profiles are auto-registered."""
        profiles = FingerprintRegistry.list()
        assert "chrome_120" in profiles
        assert "chrome_121" in profiles
        assert "firefox_121" in profiles
        assert "safari_17" in profiles
        assert "edge_120" in profiles
        assert "chrome_android" in profiles
        assert "safari_ios" in profiles

    def test_get_builtin_profile(self):
        """Test getting a built-in profile."""
        chrome = FingerprintRegistry.get("chrome_120")
        assert chrome.name == "chrome_120"
        assert chrome.ja3.startswith("771")
        assert "Chrome" in chrome.user_agent

    def test_get_nonexistent_profile(self):
        """Test getting a non-existent profile raises KeyError."""
        with pytest.raises(KeyError):
            FingerprintRegistry.get("nonexistent_browser")

    def test_get_or_none(self):
        """Test get_or_none returns None for missing profiles."""
        assert FingerprintRegistry.get_or_none("nonexistent") is None
        assert FingerprintRegistry.get_or_none("chrome_120") is not None

    def test_register_and_unregister(self):
        """Test registering and unregistering custom profiles."""
        custom = TLSFingerprint(
            name="custom_test_browser",
            ja3="771,4865-4866-4867,0-23-65281-10-11,29-23-24,0",
        )

        # Register
        FingerprintRegistry.register(custom)
        assert "custom_test_browser" in FingerprintRegistry.list()
        assert FingerprintRegistry.get("custom_test_browser") == custom

        # Unregister
        result = FingerprintRegistry.unregister("custom_test_browser")
        assert result is True
        assert "custom_test_browser" not in FingerprintRegistry.list()

        # Unregister non-existent
        result = FingerprintRegistry.unregister("nonexistent")
        assert result is False

    def test_all(self):
        """Test getting all profiles."""
        all_profiles = FingerprintRegistry.all()
        assert isinstance(all_profiles, dict)
        assert "chrome_120" in all_profiles
        assert all_profiles["chrome_120"].name == "chrome_120"


class TestBuiltinProfiles:
    """Tests for built-in browser profiles."""

    def test_chrome_120(self):
        """Test Chrome 120 profile."""
        assert CHROME_120.name == "chrome_120"
        assert "Chrome/120" in CHROME_120.user_agent
        assert CHROME_120.http2_fingerprint is not None
        assert CHROME_120.header_order is not None
        assert "host" in CHROME_120.header_order

    def test_firefox_121(self):
        """Test Firefox 121 profile."""
        assert FIREFOX_121.name == "firefox_121"
        assert "Firefox/121" in FIREFOX_121.user_agent

    def test_safari_17(self):
        """Test Safari 17 profile."""
        assert SAFARI_17.name == "safari_17"
        assert "Safari" in SAFARI_17.user_agent

    def test_mobile_profiles(self):
        """Test mobile browser profiles."""
        assert "Android" in CHROME_ANDROID.user_agent
        assert "iPhone" in SAFARI_IOS.user_agent


class TestPluginLoading:
    """Tests for plugin loading utilities."""

    def test_load_fingerprints_from_dir(self):
        """Test loading fingerprints from a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some fingerprint files
            for i in range(3):
                path = Path(tmpdir) / f"browser_{i}.json"
                with open(path, "w") as f:
                    json.dump(
                        {
                            "name": f"dir_browser_{i}",
                            "ja3": "771,4865-4866-4867,0-23-65281-10-11,29-23-24,0",
                        },
                        f,
                    )

            # Load from directory
            count = load_fingerprints_from_dir(tmpdir)
            assert count == 3

            # Verify they're registered
            for i in range(3):
                fp = FingerprintRegistry.get(f"dir_browser_{i}")
                assert fp.name == f"dir_browser_{i}"

            # Cleanup
            for i in range(3):
                FingerprintRegistry.unregister(f"dir_browser_{i}")

    def test_load_from_nonexistent_dir(self):
        """Test loading from non-existent directory returns 0."""
        count = load_fingerprints_from_dir("/nonexistent/path")
        assert count == 0

    def test_load_fingerprint_from_file(self):
        """Test loading a single fingerprint file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "name": "single_file_browser",
                    "ja3": "771,4865-4866-4867,0-23-65281-10-11,29-23-24,0",
                },
                f,
            )
            f.flush()

            fp = load_fingerprint_from_file(f.name)
            assert fp.name == "single_file_browser"
            assert "single_file_browser" in FingerprintRegistry.list()

            # Cleanup
            FingerprintRegistry.unregister("single_file_browser")
            Path(f.name).unlink()

    def test_create_fingerprint_template(self):
        """Test creating a fingerprint template file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            create_fingerprint_template(f.name, name="template_browser")

            # Load and verify
            fp = TLSFingerprint.from_json(f.name)
            assert fp.name == "template_browser"
            assert fp.ja3.startswith("771")
            assert fp.user_agent is not None

            # Cleanup
            Path(f.name).unlink()


class TestIntegration:
    """Integration tests for fingerprint usage with requests."""

    def test_fingerprint_in_api_kwargs(self):
        """Test that fingerprint can be passed to request kwargs."""
        # This is a unit test of the apply logic, not an actual HTTP test
        chrome = FingerprintRegistry.get("chrome_120")

        kwargs = {"timeout": 30}
        chrome.apply_to_kwargs(kwargs)

        assert kwargs["ja3"] == chrome.ja3
        assert kwargs["user_agent"] == chrome.user_agent
        assert kwargs["timeout"] == 30  # Original arg preserved

    def test_fingerprint_does_not_override_explicit(self):
        """Test that fingerprint doesn't override explicitly set values."""
        chrome = FingerprintRegistry.get("chrome_120")

        kwargs = {
            "ja3": "explicit_ja3",
            "user_agent": "Explicit/1.0",
        }
        chrome.apply_to_kwargs(kwargs)

        assert kwargs["ja3"] == "explicit_ja3"
        assert kwargs["user_agent"] == "Explicit/1.0"
