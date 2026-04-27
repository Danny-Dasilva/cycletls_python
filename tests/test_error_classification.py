"""Regression tests for error classification in `_raise_for_error_response`.

These cases pin down a specific defect (the bare ``"ssl"`` substring matched
the entire error message including the request URL) so that any host whose
name contains ``ssl`` — e.g. ``self-signed.badssl.com`` — got every non-TLS
error misclassified as :class:`TLSError`.

The fix is to drop the bare ``"ssl"`` keyword from the URL-blind keyword
fallback. The remaining markers (``certificate``, ``x509:``,
``tls: failed to verify``) cover Go's actual TLS error vocabulary, plus the
``status == 495 + "handshake"`` branch above remains untouched.
"""

from __future__ import annotations

import pytest

from cycletls.exceptions import (
    ConnectionError as CycleConnectionError,
)
from cycletls.exceptions import (
    CycleTLSError,
    TLSError,
)
from cycletls.schema import _raise_for_error_response


class TestBadsslUrlNotMisclassifiedAsTLS:
    """The classifier must not raise TLSError purely because the URL contains 'ssl'."""

    def test_idle_close_against_badssl_url_is_connection_error_not_tls(self):
        # Go transport "server closed idle connection" against a host with
        # "ssl" in the name must classify as a connection error, not TLSError.
        data = {
            "Status": 0,
            "Body": ('Get "https://self-signed.badssl.com": http: server closed idle connection'),
        }
        with pytest.raises(CycleTLSError) as excinfo:
            _raise_for_error_response(data)
        # Must NOT be classified as TLSError.
        assert not isinstance(excinfo.value, TLSError), (
            "Idle-close error against a *.badssl.com URL was misclassified "
            "as TLSError because the keyword fallback matched 'ssl' in the "
            f"URL: {excinfo.value!r}"
        )

    def test_eof_against_badssl_url_is_connection_error_not_tls(self):
        # Bare EOF against a host with "ssl" in the name must classify as a
        # connection error (matched on the "eof" keyword above), never as
        # TLSError.
        data = {
            "Status": 0,
            "Body": 'Get "https://self-signed.badssl.com": EOF',
        }
        with pytest.raises(CycleConnectionError) as excinfo:
            _raise_for_error_response(data)
        assert not isinstance(excinfo.value, TLSError), (
            f"EOF against *.badssl.com was misclassified as TLSError: {excinfo.value!r}"
        )


class TestRealTLSErrorsStillClassified:
    """Regression checks: real TLS error vocabulary must still raise TLSError."""

    def test_status_495_handshake_failure_is_tls_error(self):
        data = {
            "Status": 495,
            "Body": (
                'Get "https://self-signed.badssl.com": tls: failed to '
                "verify certificate -> tls: handshake failure"
            ),
        }
        with pytest.raises(TLSError):
            _raise_for_error_response(data)

    def test_x509_unknown_authority_is_tls_error(self):
        data = {
            "Status": 0,
            "Body": (
                'Get "https://self-signed.badssl.com": x509: certificate '
                "signed by unknown authority"
            ),
        }
        with pytest.raises(TLSError):
            _raise_for_error_response(data)

    def test_tls_failed_to_verify_is_tls_error(self):
        data = {
            "Status": 0,
            "Body": ('Get "https://example.com": tls: failed to verify certificate'),
        }
        with pytest.raises(TLSError):
            _raise_for_error_response(data)
