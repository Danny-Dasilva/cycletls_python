"""Tests for version consistency and license correctness."""

import re


def test_version_attribute_exists():
    """Test that cycletls exposes __version__."""
    import cycletls

    assert hasattr(cycletls, "__version__")
    assert isinstance(cycletls.__version__, str)
    assert len(cycletls.__version__) > 0


def test_version_is_valid_semver():
    """Test that the version string is valid semver (major.minor.patch)."""
    import cycletls

    pattern = r"^\d+\.\d+\.\d+([a-zA-Z0-9.+-]*)?$"
    assert re.match(pattern, cycletls.__version__), (
        f"Version '{cycletls.__version__}' is not valid semver"
    )


def test_version_matches_version_file():
    """Test that __init__.__version__ matches __version__.__version__."""
    import cycletls
    from cycletls.__version__ import __version__ as file_version

    assert cycletls.__version__ == file_version, (
        f"__init__.__version__ ({cycletls.__version__}) != "
        f"__version__.__version__ ({file_version})"
    )


def test_license_is_mit():
    """Test that __version__.py license is MIT (matching pyproject.toml)."""
    from cycletls.__version__ import __license__

    assert __license__ == "MIT", f"License is '{__license__}', expected 'MIT'"
