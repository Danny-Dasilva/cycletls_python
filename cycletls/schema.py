from pydantic import BaseModel
import json
import re
from typing import Optional, List, Union, TYPE_CHECKING
from enum import Enum
from datetime import datetime

if TYPE_CHECKING:
    from .exceptions import HTTPError

from .structures import CaseInsensitiveDict, CookieJar


class Protocol(str, Enum):
    """Protocol type for requests"""
    HTTP1 = "http1"
    HTTP2 = "http2"
    HTTP3 = "http3"
    WEBSOCKET = "websocket"
    SSE = "sse"


class Cookie(BaseModel):
    """Cookie model with full attributes"""
    name: str
    value: str
    path: Optional[str] = None
    domain: Optional[str] = None
    expires: Optional[datetime] = None
    max_age: Optional[int] = None
    secure: bool = False
    http_only: bool = False
    same_site: Optional[str] = None

    class Config:
        fields = {
            "http_only": "httpOnly",
            "same_site": "sameSite",
            "max_age": "maxAge",
        }


class Request(BaseModel):
    """Enhanced request model with all CycleTLS features"""
    url: str
    method: str
    body: str = ""
    body_bytes: Optional[bytes] = None  # Binary request body
    headers: dict = {}

    # TLS Fingerprinting options
    ja3: str = "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0"
    ja4r: Optional[str] = None  # JA4 raw format
    http2_fingerprint: Optional[str] = None  # HTTP/2 fingerprinting
    quic_fingerprint: Optional[str] = None  # QUIC fingerprinting
    disable_grease: bool = False  # Disable GREASE for exact JA4 matching

    # TLS Configuration
    server_name: Optional[str] = None  # Custom SNI override
    insecure_skip_verify: bool = False  # Skip TLS certificate verification
    tls13_auto_retry: bool = True  # Auto-retry with TLS 1.3 compatible curves

    # Protocol options
    force_http1: bool = False  # Force HTTP/1.1 protocol
    force_http3: bool = False  # Force HTTP/3 protocol
    protocol: Optional[Protocol] = None  # Explicit protocol selection

    # Connection options
    user_agent: str = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0"
    proxy: str = ""
    cookies: Optional[List[Cookie]] = None
    timeout: int = 6
    disable_redirect: bool = False
    enable_connection_reuse: bool = True  # Connection pooling

    # Header options
    header_order: Optional[List[str]] = None
    order_headers_as_provided: Optional[bool] = None

    class Config:
        fields = {
            "user_agent": "userAgent",
            "body_bytes": "bodyBytes",
            "ja4r": "ja4r",
            "http2_fingerprint": "http2Fingerprint",
            "quic_fingerprint": "quicFingerprint",
            "disable_grease": "disableGrease",
            "server_name": "serverName",
            "insecure_skip_verify": "insecureSkipVerify",
            "tls13_auto_retry": "tls13AutoRetry",
            "force_http1": "forceHTTP1",
            "force_http3": "forceHTTP3",
            "disable_redirect": "disableRedirect",
            "enable_connection_reuse": "enableConnectionReuse",
            "header_order": "headerOrder",
            "order_headers_as_provided": "orderHeadersAsProvided",
        }


class WebSocketMessage(BaseModel):
    """WebSocket message model"""
    type: str = "websocket"
    message_type: int  # 1 = text, 2 = binary
    data: Union[str, bytes]

    class Config:
        fields = {
            "message_type": "messageType",
        }


class SSEEvent(BaseModel):
    """Server-Sent Event model"""
    event: str = "message"
    data: str
    id: Optional[str] = None
    retry: Optional[int] = None


class Response(BaseModel):
    """Enhanced response model with binary data and cookies"""
    request_id: str
    status_code: int
    _headers: dict
    body: str = ""
    body_bytes: Optional[bytes] = None  # Binary response body
    _cookies: Optional[List[Cookie]] = None  # Response cookies
    final_url: Optional[str] = None  # Final URL after redirects

    class Config:
        fields = {
            "request_id": "RequestID",
            "status_code": "Status",
            "_headers": "Headers",
            "body": "Body",
            "body_bytes": "BodyBytes",
            "_cookies": "Cookies",
            "final_url": "FinalUrl",
        }

    def __init__(self, **data):
        super().__init__(**data)
        self._headers_dict: Optional[CaseInsensitiveDict] = None
        self._cookie_jar: Optional[CookieJar] = None

    @property
    def text(self) -> str:
        """
        Alias for body. Returns the response body as a string.

        Returns:
            str: The response body text
        """
        return self.body

    @property
    def content(self) -> bytes:
        """
        Returns the response body as bytes.

        If body_bytes is available, returns that. Otherwise, encodes
        the body string to UTF-8 bytes.

        Returns:
            bytes: The response body as bytes
        """
        return self.body_bytes if self.body_bytes is not None else self.body.encode('utf-8')

    @property
    def headers(self) -> CaseInsensitiveDict:
        """
        Returns headers as a case-insensitive dictionary.

        The dictionary is cached for efficiency.

        Returns:
            CaseInsensitiveDict: Case-insensitive headers dictionary
        """
        if self._headers_dict is None:
            self._headers_dict = CaseInsensitiveDict(self._headers)
        return self._headers_dict

    @property
    def cookies(self) -> CookieJar:
        """
        Returns cookies as a CookieJar object.

        The CookieJar is cached for efficiency.

        Returns:
            CookieJar: Cookie jar containing response cookies
        """
        if self._cookie_jar is None:
            self._cookie_jar = CookieJar(self._cookies or [])
        return self._cookie_jar

    @property
    def ok(self) -> bool:
        """
        Returns True if status code indicates success (200-399).

        Returns:
            bool: True if 200 <= status_code < 400
        """
        return 200 <= self.status_code < 400

    @property
    def is_redirect(self) -> bool:
        """
        Returns True if status code indicates a redirect (300-399).

        Returns:
            bool: True if 300 <= status_code < 400
        """
        return 300 <= self.status_code < 400

    @property
    def is_client_error(self) -> bool:
        """
        Returns True if status code indicates a client error (400-499).

        Returns:
            bool: True if 400 <= status_code < 500
        """
        return 400 <= self.status_code < 500

    @property
    def is_server_error(self) -> bool:
        """
        Returns True if status code indicates a server error (500-599).

        Returns:
            bool: True if 500 <= status_code < 600
        """
        return 500 <= self.status_code < 600

    @property
    def is_error(self) -> bool:
        """
        Returns True if status code indicates any error (400+).

        Returns:
            bool: True if status_code >= 400
        """
        return self.status_code >= 400

    @property
    def reason(self) -> str:
        """
        Returns the HTTP reason phrase for the status code.

        Returns:
            str: HTTP reason phrase (e.g., "OK", "Not Found")
        """
        return self._get_reason()

    @property
    def url(self) -> Optional[str]:
        """
        Alias for final_url. Returns the final URL after redirects.

        Returns:
            Optional[str]: The final URL after following redirects
        """
        return self.final_url

    @property
    def encoding(self) -> str:
        """
        Detects encoding from Content-Type header, defaults to 'utf-8'.

        Parses the Content-Type header to extract the charset parameter.
        If not found, returns 'utf-8' as the default encoding.

        Returns:
            str: Character encoding (e.g., 'utf-8', 'iso-8859-1')
        """
        content_type = self.headers.get('content-type', '')
        # Parse charset from Content-Type header
        match = re.search(r'charset=([^\s;]+)', content_type, re.IGNORECASE)
        if match:
            return match.group(1).strip('"\'')
        return 'utf-8'

    def _get_reason(self) -> str:
        """
        Helper method to get HTTP reason phrases for status codes.

        Returns:
            str: HTTP reason phrase
        """
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
        """
        Raises HTTPError if the response status indicates an error.

        Checks if the response status code is in the error range (400+).
        If so, raises an HTTPError with a detailed message including
        the status code, reason phrase, and URL.

        Raises:
            HTTPError: If status_code >= 400
        """
        if self.is_error:
            from .exceptions import HTTPError

            error_msg = f"{self.status_code} {self.reason}"
            if self.final_url:
                error_msg += f" for url: {self.final_url}"

            raise HTTPError(error_msg, response=self)

    def json(self) -> dict:
        """Parse response body as JSON"""
        return json.loads(self.body)



