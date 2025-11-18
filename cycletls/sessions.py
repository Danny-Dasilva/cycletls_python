"""
Session support for CycleTLS.

This module provides a Session class that maintains persistent cookies
and headers across multiple requests, similar to requests.Session.
"""

from typing import Any, Dict, Optional, Union
from .api import CycleTLS, ParamsType
from .structures import CookieJar, CaseInsensitiveDict
from .schema import Response, Cookie


class Session(CycleTLS):
    """
    A session object that maintains persistent cookies and headers.

    Similar to requests.Session, this class extends CycleTLS to provide
    automatic cookie and header persistence across requests.

    Attributes:
        cookies (CookieJar): Persistent cookie jar shared across requests
        headers (CaseInsensitiveDict): Persistent headers sent with all requests

    Example:
        >>> with Session() as session:
        ...     # Set persistent headers
        ...     session.headers['Authorization'] = 'Bearer token123'
        ...
        ...     # Login - cookies are automatically saved
        ...     session.post('/login', json_data={'user': 'admin', 'pass': 'secret'})
        ...
        ...     # Subsequent requests include cookies and headers automatically
        ...     response = session.get('/profile')
        ...     assert 'session_id' in response.cookies
    """

    def __init__(self, port=9112):
        """
        Initialize a Session.

        Args:
            port (int): WebSocket port for the CycleTLS backend (default: 9112)
        """
        super().__init__(port)
        self.cookies = CookieJar([])
        self.headers = CaseInsensitiveDict({})

    def request(
        self,
        method: str,
        url: str,
        params: Optional[ParamsType] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Response:
        """
        Send an HTTP request with session persistence.

        Session cookies and headers are automatically merged with request-specific
        cookies and headers. Request-specific values take precedence over session values.

        Args:
            method (str): HTTP method
            url (str): Target URL
            params (Optional[Dict]): Query parameters
            data (Optional[Any]): Request body data
            json_data (Optional[Dict]): JSON request body
            files (Optional[Dict]): File uploads
            **kwargs: Additional request options

        Returns:
            Response: Response object with status, headers, body, etc.

        Example:
            >>> session = Session()
            >>> session.headers['User-Agent'] = 'CustomBot/1.0'
            >>> session.cookies.set('pref', 'dark_mode')
            >>>
            >>> # Both headers and cookies are sent automatically
            >>> response = session.get('https://api.example.com/data')
        """
        # Merge session headers with request headers
        merged_headers = CaseInsensitiveDict(self.headers)
        if "headers" in kwargs and kwargs["headers"]:
            merged_headers.update(kwargs["headers"])
        kwargs["headers"] = dict(merged_headers)

        # Merge session cookies with request cookies
        merged_cookies = []

        # Add session cookies
        for cookie in self.cookies.get_cookies():
            merged_cookies.append(cookie)

        # Add request-specific cookies
        if "cookies" in kwargs and kwargs["cookies"]:
            request_cookies = kwargs["cookies"]

            # Handle dict cookies
            if isinstance(request_cookies, dict):
                for name, value in request_cookies.items():
                    # Override session cookie if same name
                    existing = None
                    for i, cookie in enumerate(merged_cookies):
                        if cookie.name == name:
                            existing = i
                            break

                    new_cookie = Cookie(name=name, value=value)
                    if existing is not None:
                        merged_cookies[existing] = new_cookie
                    else:
                        merged_cookies.append(new_cookie)

            # Handle CookieJar
            elif hasattr(request_cookies, "get_cookies"):
                for cookie in request_cookies.get_cookies():
                    # Override session cookie if same name
                    existing = None
                    for i, existing_cookie in enumerate(merged_cookies):
                        if existing_cookie.name == cookie.name:
                            existing = i
                            break

                    if existing is not None:
                        merged_cookies[existing] = cookie
                    else:
                        merged_cookies.append(cookie)

            # Handle list of Cookie objects
            elif isinstance(request_cookies, list):
                for cookie in request_cookies:
                    # Override session cookie if same name
                    existing = None
                    for i, existing_cookie in enumerate(merged_cookies):
                        if existing_cookie.name == cookie.name:
                            existing = i
                            break

                    if existing is not None:
                        merged_cookies[existing] = cookie
                    else:
                        merged_cookies.append(cookie)

        kwargs["cookies"] = merged_cookies if merged_cookies else None

        # Make the request using parent class
        response = super().request(method, url, params, data, json_data, files, **kwargs)

        # Update session cookies from response
        if response.cookies and len(response.cookies) > 0:
            for name in response.cookies:
                cookie_value = response.cookies[name]
                self.cookies.set(name, cookie_value)

        return response

    def close(self):
        """
        Close the session and cleanup resources.

        This clears the session cookies and headers, then closes the
        underlying CycleTLS connection.
        """
        # Clear session state
        self.cookies = CookieJar([])
        self.headers = CaseInsensitiveDict({})

        # Close parent connection
        super().close()
