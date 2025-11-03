"""
Tests for insecure_skip_verify functionality.
Based on CycleTLS/tests/insecureSkipVerify.test.ts
"""

import pytest
from cycletls import CycleTLS


@pytest.fixture
def client():
    """Create a CycleTLS client instance"""
    cycle = CycleTLS()
    yield cycle
    cycle.close()


@pytest.fixture
def firefox_ja3():
    """Firefox 87 JA3 fingerprint"""
    return "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0"


@pytest.fixture
def firefox_user_agent():
    """Firefox 87 User Agent"""
    return "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0"


def test_expired_certificate_error_without_skip_verify(client, firefox_ja3, firefox_user_agent):
    """Test that expired certificate causes error when insecure_skip_verify is False"""
    url = "https://expired.badssl.com"

    # Should raise an exception or return error status for expired certificate
    with pytest.raises(Exception) as exc_info:
        client.get(
            url,
            ja3=firefox_ja3,
            user_agent=firefox_user_agent,
            insecure_skip_verify=False
        )

    # Error message should contain certificate or verification related text
    error_msg = str(exc_info.value).lower()
    assert any(word in error_msg for word in ['certificate', 'expired', 'verify', 'x509', 'tls'])


def test_expired_certificate_accepted_with_skip_verify(client, firefox_ja3, firefox_user_agent):
    """Test that expired certificate is accepted when insecure_skip_verify is True"""
    url = "https://expired.badssl.com"

    result = client.get(
        url,
        ja3=firefox_ja3,
        user_agent=firefox_user_agent,
        insecure_skip_verify=True
    )

    # Should successfully connect despite expired certificate
    assert result.status_code == 200
    assert len(result.text) > 0


def test_self_signed_certificate_error_without_skip_verify(client, firefox_ja3, firefox_user_agent):
    """Test that self-signed certificate causes error when insecure_skip_verify is False"""
    url = "https://self-signed.badssl.com"

    # Should raise an exception for self-signed certificate
    with pytest.raises(Exception) as exc_info:
        client.get(
            url,
            ja3=firefox_ja3,
            user_agent=firefox_user_agent,
            insecure_skip_verify=False
        )

    # Error message should contain certificate related text
    error_msg = str(exc_info.value).lower()
    assert any(word in error_msg for word in ['certificate', 'verify', 'self-signed', 'authority', 'x509'])


def test_self_signed_certificate_accepted_with_skip_verify(client, firefox_ja3, firefox_user_agent):
    """Test that self-signed certificate is accepted when insecure_skip_verify is True"""
    url = "https://self-signed.badssl.com"

    result = client.get(
        url,
        ja3=firefox_ja3,
        user_agent=firefox_user_agent,
        insecure_skip_verify=True
    )

    # Should successfully connect despite self-signed certificate
    assert result.status_code == 200
    assert len(result.text) > 0


def test_wrong_host_certificate_error_without_skip_verify(client, firefox_ja3, firefox_user_agent):
    """Test that wrong host certificate causes error when insecure_skip_verify is False"""
    url = "https://wrong.host.badssl.com"

    # Should raise an exception for wrong host certificate
    with pytest.raises(Exception) as exc_info:
        client.get(
            url,
            ja3=firefox_ja3,
            user_agent=firefox_user_agent,
            insecure_skip_verify=False
        )

    # Error message should contain certificate or hostname related text
    error_msg = str(exc_info.value).lower()
    assert any(word in error_msg for word in ['certificate', 'verify', 'hostname', 'name', 'x509'])


def test_wrong_host_certificate_accepted_with_skip_verify(client, firefox_ja3, firefox_user_agent):
    """Test that wrong host certificate is accepted when insecure_skip_verify is True"""
    url = "https://wrong.host.badssl.com"

    result = client.get(
        url,
        ja3=firefox_ja3,
        user_agent=firefox_user_agent,
        insecure_skip_verify=True
    )

    # Should successfully connect despite wrong host certificate
    assert result.status_code == 200
    assert len(result.text) > 0


def test_untrusted_root_certificate_error_without_skip_verify(client, firefox_ja3, firefox_user_agent):
    """Test that untrusted root certificate causes error when insecure_skip_verify is False"""
    url = "https://untrusted-root.badssl.com"

    # Should raise an exception for untrusted root certificate
    with pytest.raises(Exception) as exc_info:
        client.get(
            url,
            ja3=firefox_ja3,
            user_agent=firefox_user_agent,
            insecure_skip_verify=False
        )

    # Error message should contain certificate related text
    error_msg = str(exc_info.value).lower()
    assert any(word in error_msg for word in ['certificate', 'verify', 'untrusted', 'authority', 'root', 'x509'])


def test_untrusted_root_certificate_accepted_with_skip_verify(client, firefox_ja3, firefox_user_agent):
    """Test that untrusted root certificate is accepted when insecure_skip_verify is True"""
    url = "https://untrusted-root.badssl.com"

    result = client.get(
        url,
        ja3=firefox_ja3,
        user_agent=firefox_user_agent,
        insecure_skip_verify=True
    )

    # Should successfully connect despite untrusted root certificate
    assert result.status_code == 200
    assert len(result.text) > 0


def test_valid_certificate_works_with_skip_verify_disabled(client, firefox_ja3, firefox_user_agent):
    """Test that valid certificate works normally when insecure_skip_verify is False"""
    url = "https://httpbin.org/get"

    result = client.get(
        url,
        ja3=firefox_ja3,
        user_agent=firefox_user_agent,
        insecure_skip_verify=False
    )

    # Valid certificate should work fine with verification enabled
    assert result.status_code == 200
    assert len(result.text) > 0


def test_connection_refused_error_handling(client, firefox_ja3, firefox_user_agent):
    """Test proper handling of connection refused errors"""
    url = "https://localhost:9999"

    # Should raise an exception for connection refused
    with pytest.raises(Exception) as exc_info:
        client.get(
            url,
            ja3=firefox_ja3,
            user_agent=firefox_user_agent,
            timeout=5
        )

    # Error message should indicate connection issue
    error_msg = str(exc_info.value).lower()
    assert any(word in error_msg for word in ['connection', 'refused', 'connect', 'syscall', 'dial'])


@pytest.mark.parametrize("url,expected_error_keywords", [
    ("https://expired.badssl.com", ["certificate", "expired"]),
    ("https://self-signed.badssl.com", ["certificate", "self-signed", "authority"]),
    ("https://wrong.host.badssl.com", ["certificate", "hostname", "name"]),
    ("https://untrusted-root.badssl.com", ["certificate", "untrusted", "authority"]),
])
def test_certificate_errors_parametrized(client, firefox_ja3, firefox_user_agent, url, expected_error_keywords):
    """Parametrized test for various certificate errors"""
    # Test with verification enabled - should fail
    with pytest.raises(Exception) as exc_info:
        client.get(
            url,
            ja3=firefox_ja3,
            user_agent=firefox_user_agent,
            insecure_skip_verify=False
        )

    error_msg = str(exc_info.value).lower()
    # At least one of the expected keywords should be in the error message
    assert any(
        any(keyword in error_msg for keyword in keywords)
        for keywords in [expected_error_keywords]
    )

    # Test with verification disabled - should succeed
    result = client.get(
        url,
        ja3=firefox_ja3,
        user_agent=firefox_user_agent,
        insecure_skip_verify=True
    )
    assert result.status_code == 200
