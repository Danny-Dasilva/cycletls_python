"""
CycleTLS custom exceptions.

This module provides a hierarchy of exceptions for CycleTLS,
following the pattern established by the requests library.
"""

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .schema import Response


class CycleTLSError(Exception):
    """
    Base exception for all CycleTLS errors.

    All CycleTLS-specific exceptions inherit from this class,
    making it easy to catch any CycleTLS-related error.
    """
    pass


class RequestException(CycleTLSError):
    """
    Base class for all request-related exceptions.

    This is the base exception for errors that occur during
    the request/response cycle.
    """
    pass


class HTTPError(RequestException):
    """
    An HTTP error occurred (4xx or 5xx status code).

    This exception is raised when raise_for_status() is called
    on a Response with a 4xx or 5xx status code.

    Attributes:
        response: The Response object (if available)
    """

    def __init__(self, message: str, response: Optional['Response'] = None):
        """
        Initialize HTTPError.

        Args:
            message: Error message
            response: Response object that triggered the error
        """
        super().__init__(message)
        self.response = response


class ConnectionError(RequestException):
    """
    A connection error occurred.

    Raised when a request fails due to network connectivity issues,
    such as DNS lookup failures or connection refused errors.
    """
    pass


class Timeout(RequestException):
    """
    The request timed out.

    Raised when a request exceeds the specified timeout duration.
    This includes both connection timeouts and read timeouts.
    """
    pass


class TooManyRedirects(RequestException):
    """
    Too many redirects occurred.

    Raised when the maximum number of redirects is exceeded.
    """
    pass


class InvalidURL(RequestException):
    """
    The URL provided was invalid.

    Raised when attempting to make a request with a malformed
    or invalid URL.
    """
    pass


class TLSError(RequestException):
    """
    A TLS/SSL error occurred.

    Raised when there are issues with TLS/SSL certificates,
    protocol version mismatches, or other TLS-related errors.
    """
    pass


class ProxyError(RequestException):
    """
    A proxy error occurred.

    Raised when there are issues connecting to or communicating
    through a proxy server.
    """
    pass


class InvalidHeader(RequestException):
    """
    Invalid header name or value.

    Raised when attempting to use an invalid HTTP header name
    or value.
    """
    pass


# Aliases for backward compatibility with other HTTP libraries
ConnectTimeout = Timeout
ReadTimeout = Timeout
