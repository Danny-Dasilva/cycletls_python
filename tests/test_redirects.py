"""
Tests for redirect handling functionality in CycleTLS.

This module tests:
- Following redirects (default behavior)
- Disabling redirects with disable_redirect flag
- Final URL tracking after redirects
- Various redirect types (301, 302, absolute redirects)
"""

import pytest
from cycletls import CycleTLS


@pytest.fixture
def firefox_ja3():
    """Firefox 87 JA3 fingerprint."""
    return "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0"


@pytest.fixture
def firefox_user_agent():
    """Firefox 87 user agent."""
    return "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0"


class TestRedirectFollowing:
    """Tests for following redirects (default behavior)."""

    def test_follow_redirect_default(self, cycletls_client_function, firefox_ja3, firefox_user_agent):
        """Test that redirects are followed by default."""
        response = cycletls_client_function.get(
            "https://httpbin.org/redirect/1",
            ja3=firefox_ja3,
            user_agent=firefox_user_agent
        )

        assert response.status_code == 200
        assert "get" in response.final_url.lower()

    def test_follow_multiple_redirects(self, cycletls_client_function, firefox_ja3, firefox_user_agent):
        """Test following multiple redirects (3 hops)."""
        response = cycletls_client_function.get(
            "https://httpbin.org/redirect/3",
            ja3=firefox_ja3,
            user_agent=firefox_user_agent
        )

        assert response.status_code == 200
        assert "get" in response.final_url.lower()

    def test_follow_absolute_redirect(self, cycletls_client_function, firefox_ja3, firefox_user_agent):
        """Test following absolute redirects."""
        response = cycletls_client_function.get(
            "https://httpbin.org/absolute-redirect/1",
            ja3=firefox_ja3,
            user_agent=firefox_user_agent
        )

        assert response.status_code == 200
        assert "get" in response.final_url.lower()

    def test_redirect_to_specific_url(self, cycletls_client_function, firefox_ja3, firefox_user_agent):
        """Test redirect to a specific URL."""
        target_url = "https://httpbin.org/get"
        response = cycletls_client_function.get(
            f"https://httpbin.org/redirect-to?url={target_url}",
            ja3=firefox_ja3,
            user_agent=firefox_user_agent
        )

        assert response.status_code == 200
        assert response.final_url == target_url


class TestRedirectDisabled:
    """Tests for disabled redirect functionality."""

    def test_disable_redirect_returns_redirect_status(self, cycletls_client_function, firefox_ja3, firefox_user_agent):
        """Test that disabling redirects returns the redirect status code."""
        response = cycletls_client_function.get(
            "https://httpbin.org/redirect/1",
            ja3=firefox_ja3,
            user_agent=firefox_user_agent,
            disable_redirect=True
        )

        assert response.status_code == 302
        assert "Location" in response.headers

    def test_disable_redirect_multiple_hops(self, cycletls_client_function, firefox_ja3, firefox_user_agent):
        """Test that with redirects disabled, only the first redirect is returned."""
        response = cycletls_client_function.get(
            "https://httpbin.org/redirect/3",
            ja3=firefox_ja3,
            user_agent=firefox_user_agent,
            disable_redirect=True
        )

        assert response.status_code == 302
        assert "Location" in response.headers

    def test_disable_redirect_absolute(self, cycletls_client_function, firefox_ja3, firefox_user_agent):
        """Test disabling redirects with absolute redirect."""
        response = cycletls_client_function.get(
            "https://httpbin.org/absolute-redirect/1",
            ja3=firefox_ja3,
            user_agent=firefox_user_agent,
            disable_redirect=True
        )

        assert response.status_code == 302
        assert "Location" in response.headers

    def test_disable_redirect_to_specific_url(self, cycletls_client_function, firefox_ja3, firefox_user_agent):
        """Test disabling redirects when redirecting to specific URL."""
        target_url = "https://httpbin.org/get"
        response = cycletls_client_function.get(
            f"https://httpbin.org/redirect-to?url={target_url}",
            ja3=firefox_ja3,
            user_agent=firefox_user_agent,
            disable_redirect=True
        )

        assert response.status_code == 302
        assert "Location" in response.headers
        assert response.headers["Location"] == target_url


class TestFinalURL:
    """Tests for final URL tracking after redirects."""

    def test_final_url_with_redirect_disabled(self, cycletls_client_function, firefox_ja3, firefox_user_agent):
        """Test that final_url matches original URL when redirects are disabled."""
        url = "https://httpbin.org/redirect/1"
        response = cycletls_client_function.get(
            url,
            ja3=firefox_ja3,
            user_agent=firefox_user_agent,
            disable_redirect=True
        )

        assert response.status_code == 302
        assert response.final_url == url

    def test_final_url_with_redirect_enabled(self, cycletls_client_function, firefox_ja3, firefox_user_agent):
        """Test that final_url is updated after following redirects."""
        url = "https://httpbin.org/redirect/1"
        response = cycletls_client_function.get(
            url,
            ja3=firefox_ja3,
            user_agent=firefox_user_agent,
            disable_redirect=False
        )

        assert response.status_code == 200
        assert response.final_url != url
        assert "get" in response.final_url.lower()

    def test_final_url_multiple_redirects(self, cycletls_client_function, firefox_ja3, firefox_user_agent):
        """Test final_url after multiple redirect hops."""
        url = "https://httpbin.org/redirect/3"
        response = cycletls_client_function.get(
            url,
            ja3=firefox_ja3,
            user_agent=firefox_user_agent,
            disable_redirect=False
        )

        assert response.status_code == 200
        assert response.final_url != url
        assert "get" in response.final_url.lower()

    def test_final_url_no_redirect(self, cycletls_client_function, firefox_ja3, firefox_user_agent):
        """Test that final_url matches original URL when no redirect occurs."""
        url = "https://httpbin.org/get"
        response = cycletls_client_function.get(
            url,
            ja3=firefox_ja3,
            user_agent=firefox_user_agent
        )

        assert response.status_code == 200
        assert response.final_url == url


class TestRedirectWithRealSites:
    """Tests redirects with real-world sites (e.g., google.com)."""

    def test_google_redirect_disabled(self, cycletls_client_function, firefox_ja3, firefox_user_agent):
        """Test that google.com returns 301 with redirects disabled."""
        response = cycletls_client_function.get(
            "https://google.com",
            ja3=firefox_ja3,
            user_agent=firefox_user_agent,
            disable_redirect=True
        )

        assert response.status_code == 301
        assert "Location" in response.headers

    def test_google_redirect_enabled(self, cycletls_client_function, firefox_ja3, firefox_user_agent):
        """Test that google.com returns 200 with redirects enabled."""
        response = cycletls_client_function.get(
            "https://google.com",
            ja3=firefox_ja3,
            user_agent=firefox_user_agent,
            disable_redirect=False
        )

        assert response.status_code == 200
        assert "google.com" in response.final_url.lower()


class TestRedirectWithDifferentMethods:
    """Tests redirect handling with different HTTP methods."""

    def test_post_redirect(self, cycletls_client_function, firefox_ja3, firefox_user_agent):
        """Test POST request redirect handling."""
        response = cycletls_client_function.post(
            "https://httpbin.org/redirect-to?url=https://httpbin.org/post",
            ja3=firefox_ja3,
            user_agent=firefox_user_agent,
            body='{"test": "data"}',
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200

    def test_post_redirect_disabled(self, cycletls_client_function, firefox_ja3, firefox_user_agent):
        """Test POST request with redirects disabled."""
        response = cycletls_client_function.post(
            "https://httpbin.org/redirect-to?url=https://httpbin.org/post",
            ja3=firefox_ja3,
            user_agent=firefox_user_agent,
            disable_redirect=True,
            body='{"test": "data"}',
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 302
        assert "Location" in response.headers
