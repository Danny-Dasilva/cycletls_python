"""
Session support for CycleTLS.

This module provides a Session class that maintains persistent cookies
and headers across multiple requests, similar to requests.Session.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from .api import CycleTLS, ParamsType
from .fingerprints import TLSFingerprint
from .schema import Cookie, Response
from .structures import CaseInsensitiveDict, CookieJar


def _merge_cookie(merged_cookies: List[Cookie], new_cookie: Cookie) -> None:
    """Merge a cookie into the list, replacing by name if exists."""
    for i, existing in enumerate(merged_cookies):
        if existing.name == new_cookie.name:
            merged_cookies[i] = new_cookie
            return
    merged_cookies.append(new_cookie)


class Session(CycleTLS):
    """
    A session object that maintains persistent cookies and headers.

    Similar to requests.Session, this class extends CycleTLS to provide
    automatic cookie and header persistence across requests.

    Attributes:
        cookies (CookieJar): Persistent cookie jar shared across requests
        headers (CaseInsensitiveDict): Persistent headers sent with all requests
        base_url (Optional[str]): Base URL prepended to relative URLs
        auth (Optional[Tuple[str, str]]): Default (username, password) for Basic auth

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

    def __init__(
        self,
        base_url: Optional[str] = None,
        auth: Optional[Tuple[str, str]] = None,
        use_batching: bool = False,
        batch_size: int = 32,
        flush_interval: float = 0.0001,
    ):
        """Initialize a Session.

        Args:
            base_url: Base URL prepended to relative URLs (e.g. 'https://api.example.com')
            auth: Default (username, password) tuple for HTTP Basic authentication
            use_batching: If True, route individual requests through the batch
                FFI path for higher throughput.
            batch_size: Maximum number of requests to accumulate per batch.
            flush_interval: Maximum time (seconds) to wait before flushing a
                partial batch.
        """
        super().__init__(
            use_batching=use_batching,
            batch_size=batch_size,
            flush_interval=flush_interval,
        )
        self.cookies = CookieJar([])
        self.headers = CaseInsensitiveDict({})
        self.base_url = base_url.rstrip("/") if base_url else None
        self.auth = auth

    def _prepare_url(self, url: str) -> str:
        """Prepend base_url to relative URLs."""
        if self.base_url and not url.startswith(("http://", "https://")):
            return f"{self.base_url}/{url.lstrip('/')}"
        return url

    def _merge_session_state(
        self, kwargs: Dict[str, Any], auth: Optional[Tuple[str, str]] = None
    ) -> Optional[Tuple[str, str]]:
        """Merge session-level headers, cookies, and auth into request kwargs.

        Returns the effective auth tuple (request-level overrides session-level).
        """
        # Merge session headers with request headers
        merged_headers = CaseInsensitiveDict(self.headers)
        if "headers" in kwargs and kwargs["headers"]:
            merged_headers.update(kwargs["headers"])
        kwargs["headers"] = dict(merged_headers)

        # Merge session cookies with request cookies
        merged_cookies = list(self.cookies.get_cookies())

        # Add request-specific cookies (overriding session cookies by name)
        request_cookies = kwargs.get("cookies")
        if request_cookies:
            if isinstance(request_cookies, dict):
                for name, value in request_cookies.items():
                    _merge_cookie(merged_cookies, Cookie(name=name, value=value))
            elif hasattr(request_cookies, "get_cookies"):
                for cookie in request_cookies.get_cookies():
                    _merge_cookie(merged_cookies, cookie)
            elif isinstance(request_cookies, list):
                for cookie in request_cookies:
                    _merge_cookie(merged_cookies, cookie)

        kwargs["cookies"] = merged_cookies if merged_cookies else None

        # Apply session-level auth if no request-level auth provided
        if auth is None and self.auth is not None:
            auth = self.auth
        return auth

    def _update_cookies_from_response(self, response: Response) -> None:
        """Update session cookies from a response."""
        if response.cookies and len(response.cookies) > 0:
            for name in response.cookies:
                cookie_value = response.cookies[name]
                self.cookies.set(name, cookie_value)

    def request(
        self,
        method: str,
        url: str,
        params: Optional[ParamsType] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        fingerprint: Optional[Union[str, TLSFingerprint]] = None,
        auth: Optional[Tuple[str, str]] = None,
        **kwargs: Any,
    ) -> Response:
        """
        Send an HTTP request with session persistence.

        Session cookies, headers, auth, and base_url are all applied automatically.
        Request-specific values take precedence over session values.

        Args:
            method: HTTP method
            url: Target URL (relative URLs are joined with base_url)
            params: Query parameters
            data: Request body data
            json_data: JSON request body
            json: Alias for json_data
            files: File uploads
            fingerprint: TLS fingerprint profile
            auth: (username, password) tuple (overrides session.auth)
            **kwargs: Additional request options

        Returns:
            Response: Response object with status, headers, body, etc.
        """
        url = self._prepare_url(url)
        effective_auth = self._merge_session_state(kwargs, auth=auth)

        response = super().request(
            method,
            url,
            params=params,
            data=data,
            json_data=json_data,
            json=json,
            files=files,
            fingerprint=fingerprint,
            auth=effective_auth,
            **kwargs,
        )

        self._update_cookies_from_response(response)
        return response

    async def arequest(
        self,
        method: str,
        url: str,
        params: Optional[ParamsType] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        fingerprint: Optional[Union[str, TLSFingerprint]] = None,
        auth: Optional[Tuple[str, str]] = None,
        poll_interval: float = 0.0,
        timeout: float = 30.0,
        use_callback: bool = False,
        **kwargs: Any,
    ) -> Response:
        """
        Send an async HTTP request with session persistence.

        Async counterpart of :meth:`request`. Session cookies, headers,
        auth, and base_url are all applied the same way.

        Args:
            method: HTTP method
            url: Target URL (relative URLs are joined with base_url)
            params: Query parameters
            data: Request body data
            json_data: JSON request body
            json: Alias for json_data
            files: File uploads
            fingerprint: TLS fingerprint profile
            auth: (username, password) tuple (overrides session.auth)
            poll_interval: Time between polls (default: 0 = adaptive)
            timeout: Maximum wait time in seconds (default: 30s)
            use_callback: Use pipe-based notification instead of polling.
            **kwargs: Additional request options

        Returns:
            Response: Response object
        """
        url = self._prepare_url(url)
        effective_auth = self._merge_session_state(kwargs, auth=auth)

        response = await super().arequest(
            method,
            url,
            params=params,
            data=data,
            json_data=json_data,
            json=json,
            files=files,
            fingerprint=fingerprint,
            auth=effective_auth,
            poll_interval=poll_interval,
            timeout=timeout,
            use_callback=use_callback,
            **kwargs,
        )

        self._update_cookies_from_response(response)
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
