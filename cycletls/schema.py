"""Data models shared across the CycleTLS Python client."""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from .exceptions import HTTPError

from .structures import CaseInsensitiveDict, CookieJar


class Protocol(str, Enum):
    """Protocol type for requests."""

    HTTP1 = "http1"
    HTTP2 = "http2"
    HTTP3 = "http3"
    WEBSOCKET = "websocket"
    SSE = "sse"


@dataclass
class Cookie:
    """Cookie model with full attributes."""

    name: str
    value: str
    path: Optional[str] = None
    domain: Optional[str] = None
    expires: Optional[datetime] = None
    max_age: Optional[int] = None
    secure: bool = False
    http_only: bool = False
    same_site: Optional[str] = None

    def __repr__(self) -> str:
        """Return detailed string representation of the Cookie."""
        return f"<Cookie {self.name}={self.value} for {self.domain or 'any domain'}>"

    def __str__(self) -> str:
        """Return user-friendly string representation of the Cookie."""
        return f"{self.name}={self.value}"


@dataclass
class Request:
    """Enhanced request model with all CycleTLS features."""

    url: str
    method: str
    body: str = ""
    body_bytes: Optional[bytes] = None
    headers: dict = field(default_factory=dict)

    # TLS Fingerprinting options
    ja3: str = (
        "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0"
    )
    ja4r: Optional[str] = None
    http2_fingerprint: Optional[str] = None
    quic_fingerprint: Optional[str] = None
    disable_grease: bool = False

    # TLS Configuration
    server_name: Optional[str] = None
    insecure_skip_verify: bool = False
    tls13_auto_retry: bool = True

    # Protocol options
    force_http1: bool = False
    force_http3: bool = False
    protocol: Optional[Protocol] = None

    # Connection options
    user_agent: str = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0"
    proxy: str = ""
    cookies: Optional[List[Cookie]] = None
    timeout: int = 6
    disable_redirect: bool = False
    enable_connection_reuse: bool = True

    # Header options
    header_order: Optional[List[str]] = None
    order_headers_as_provided: Optional[bool] = None

    def __repr__(self) -> str:
        """Return detailed string representation of the Request."""
        proxy_info = f" via {self.proxy}" if self.proxy else ""
        return f"<Request [{self.method} {self.url}{proxy_info}]>"

    def __str__(self) -> str:
        """Return user-friendly string representation of the Request."""
        return f"{self.method} {self.url}"

    def to_dict(self) -> dict:
        """Convert Request to dictionary for serialization (optimized)."""
        # Build dict with required fields (batch assignment is faster)
        result = {
            "url": self.url,
            "method": self.method,
            "body": self.body,
            "headers": self.headers,
            "ja3": self.ja3,
            "disableGrease": self.disable_grease,
            "insecureSkipVerify": self.insecure_skip_verify,
            "tls13AutoRetry": self.tls13_auto_retry,
            "forceHTTP1": self.force_http1,
            "forceHTTP3": self.force_http3,
            "userAgent": self.user_agent,
            "proxy": self.proxy,
            "timeout": self.timeout,
            "disableRedirect": self.disable_redirect,
            "enableConnectionReuse": self.enable_connection_reuse,
        }

        # Add optional fields only if set (minimize conditionals)
        if self.body_bytes is not None:
            result["bodyBytes"] = self.body_bytes  # Let msgpack handle binary
        if self.ja4r is not None:
            result["ja4r"] = self.ja4r
        if self.http2_fingerprint is not None:
            result["http2Fingerprint"] = self.http2_fingerprint
        if self.quic_fingerprint is not None:
            result["quicFingerprint"] = self.quic_fingerprint
        if self.server_name is not None:
            result["serverName"] = self.server_name
        if self.protocol is not None:
            result["protocol"] = self.protocol.value
        if self.cookies is not None:
            result["cookies"] = [_cookie_to_dict(c) for c in self.cookies]
        if self.header_order is not None:
            result["headerOrder"] = self.header_order
        if self.order_headers_as_provided is not None:
            result["orderHeadersAsProvided"] = self.order_headers_as_provided

        return result


@dataclass
class WebSocketMessage:
    """WebSocket message model."""

    message_type: int  # 1 = text, 2 = binary
    data: Union[str, bytes]
    type: str = "websocket"


@dataclass
class SSEEvent:
    """Server-Sent Event model."""

    data: str
    event: str = "message"
    id: Optional[str] = None
    retry: Optional[int] = None


@dataclass
class Response:
    """Enhanced response model with binary data and cookies."""

    request_id: str
    status_code: int
    raw_headers: dict = field(default_factory=dict)
    body: str = ""
    body_bytes: Optional[bytes] = None
    raw_cookies: Optional[List[Cookie]] = None
    final_url: Optional[str] = None

    def __post_init__(self):
        """Initialize cached properties."""
        self._headers_dict: Optional[CaseInsensitiveDict] = None
        self._cookie_jar: Optional[CookieJar] = None

    @property
    def text(self) -> str:
        """Alias for body. Returns the response body as a string."""
        return self.body

    @property
    def content(self) -> bytes:
        """Return the response body as bytes."""
        return self.body_bytes if self.body_bytes is not None else self.body.encode("utf-8")

    @property
    def headers(self) -> CaseInsensitiveDict:
        """Return headers as a case-insensitive dictionary."""
        if self._headers_dict is None:
            self._headers_dict = CaseInsensitiveDict(self.raw_headers)
        return self._headers_dict

    @property
    def cookies(self) -> CookieJar:
        """Return cookies as a CookieJar object."""
        if self._cookie_jar is None:
            self._cookie_jar = CookieJar(self.raw_cookies or [])
        return self._cookie_jar

    @property
    def ok(self) -> bool:
        """Return True if status code indicates success (200-399)."""
        return 200 <= self.status_code < 400

    @property
    def is_redirect(self) -> bool:
        """Return True if status code indicates a redirect (300-399)."""
        return 300 <= self.status_code < 400

    @property
    def is_client_error(self) -> bool:
        """Return True if status code indicates a client error (400-499)."""
        return 400 <= self.status_code < 500

    @property
    def is_server_error(self) -> bool:
        """Return True if status code indicates a server error (500-599)."""
        return 500 <= self.status_code < 600

    @property
    def is_error(self) -> bool:
        """Return True if status code indicates any error (400+)."""
        return self.status_code >= 400

    @property
    def reason(self) -> str:
        """Return the HTTP reason phrase for the status code."""
        return self._get_reason()

    @property
    def url(self) -> Optional[str]:
        """Alias for final_url. Returns the final URL after redirects."""
        return self.final_url

    @property
    def encoding(self) -> str:
        """Detect encoding from Content-Type header, default to 'utf-8'."""
        content_type = self.headers.get("content-type", "")
        match = re.search(r"charset=([^\s;]+)", content_type, re.IGNORECASE)
        if match:
            return match.group(1).strip("\"'")
        return "utf-8"

    def _get_reason(self) -> str:
        """Helper to get HTTP reason phrases for status codes."""
        status_phrases = {
            # 1xx Informational
            100: "Continue",
            101: "Switching Protocols",
            102: "Processing",
            103: "Early Hints",
            # 2xx Success
            200: "OK",
            201: "Created",
            202: "Accepted",
            203: "Non-Authoritative Information",
            204: "No Content",
            205: "Reset Content",
            206: "Partial Content",
            207: "Multi-Status",
            208: "Already Reported",
            226: "IM Used",
            # 3xx Redirection
            300: "Multiple Choices",
            301: "Moved Permanently",
            302: "Found",
            303: "See Other",
            304: "Not Modified",
            305: "Use Proxy",
            307: "Temporary Redirect",
            308: "Permanent Redirect",
            # 4xx Client Error
            400: "Bad Request",
            401: "Unauthorized",
            402: "Payment Required",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            406: "Not Acceptable",
            407: "Proxy Authentication Required",
            408: "Request Timeout",
            409: "Conflict",
            410: "Gone",
            411: "Length Required",
            412: "Precondition Failed",
            413: "Payload Too Large",
            414: "URI Too Long",
            415: "Unsupported Media Type",
            416: "Range Not Satisfiable",
            417: "Expectation Failed",
            418: "I'm a teapot",
            421: "Misdirected Request",
            422: "Unprocessable Entity",
            423: "Locked",
            424: "Failed Dependency",
            425: "Too Early",
            426: "Upgrade Required",
            428: "Precondition Required",
            429: "Too Many Requests",
            431: "Request Header Fields Too Large",
            451: "Unavailable For Legal Reasons",
            # 5xx Server Error
            500: "Internal Server Error",
            501: "Not Implemented",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout",
            505: "HTTP Version Not Supported",
            506: "Variant Also Negotiates",
            507: "Insufficient Storage",
            508: "Loop Detected",
            510: "Not Extended",
            511: "Network Authentication Required",
        }
        return status_phrases.get(self.status_code, "Unknown")

    def raise_for_status(self) -> None:
        """Raise HTTPError if the response status indicates an error."""
        if self.is_error:
            from .exceptions import HTTPError  # Local import to avoid cycle

            error_msg = f"{self.status_code} {self.reason}"
            if self.final_url:
                error_msg += f" for url: {self.final_url}"
            raise HTTPError(error_msg, response=self)

    def json(self) -> dict:
        """Parse response body as JSON."""
        return json.loads(self.body)

    def __repr__(self) -> str:
        """Return detailed string representation of the Response."""
        return f"<Response [{self.status_code} {self.reason}]>"

    def __str__(self) -> str:
        """Return user-friendly string representation of the Response."""
        return f"<Response [{self.status_code}]>"


def _cookie_to_dict(cookie: Cookie) -> dict:
    """Convert Cookie to dictionary for serialization."""
    result = {
        "name": cookie.name,
        "value": cookie.value,
        "secure": cookie.secure,
        "httpOnly": cookie.http_only,
    }
    if cookie.path is not None:
        result["path"] = cookie.path
    if cookie.domain is not None:
        result["domain"] = cookie.domain
    if cookie.expires is not None:
        result["expires"] = cookie.expires.isoformat()
    if cookie.max_age is not None:
        result["maxAge"] = cookie.max_age
    if cookie.same_site is not None:
        result["sameSite"] = cookie.same_site
    return result


def _dict_to_cookie(data: dict) -> Cookie:
    """Convert dictionary to Cookie object."""
    expires = None
    if "expires" in data and data["expires"]:
        expires = datetime.fromisoformat(data["expires"])

    return Cookie(
        name=data["name"],
        value=data["value"],
        path=data.get("path"),
        domain=data.get("domain"),
        expires=expires,
        max_age=data.get("maxAge"),
        secure=data.get("secure", False),
        http_only=data.get("httpOnly", False),
        same_site=data.get("sameSite"),
    )


def _dict_to_response(data: dict) -> Response:
    """Convert dictionary to Response object."""
    # Decode base64 body_bytes if present
    body_bytes = None
    if "BodyBytes" in data and data["BodyBytes"]:
        try:
            body_bytes = base64.b64decode(data["BodyBytes"])
        except Exception:
            pass

    # Convert cookies
    raw_cookies = None
    if "Cookies" in data and data["Cookies"]:
        raw_cookies = [_dict_to_cookie(c) for c in data["Cookies"]]

    return Response(
        request_id=data.get("RequestID", ""),
        status_code=data.get("Status", 0),
        raw_headers=data.get("Headers", {}),
        body=data.get("Body", ""),
        body_bytes=body_bytes,
        raw_cookies=raw_cookies,
        final_url=data.get("FinalUrl"),
    )
