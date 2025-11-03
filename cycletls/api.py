import json
import urllib.parse
import warnings
import threading
import weakref
from typing import Union
from websocket import create_connection
from .schema import Response, Request, Protocol
import subprocess
from time import sleep
import psutil
import platform
import os


def get_binary_path():
    """
    Detect the correct binary path based on platform and architecture.

    Returns:
        str: Path to the platform-specific CycleTLS binary
    """
    system = platform.system()
    arch = platform.machine().lower()

    # Map common architecture names
    if arch in ("x86_64", "amd64"):
        arch = "amd64"
    elif arch in ("aarch64", "arm64"):
        arch = "arm64"

    # Determine binary name based on platform
    if system == "Linux":
        binary = f"./dist/cycletls-linux-{arch}"
    elif system == "Darwin":  # macOS
        binary = f"./dist/cycletls-darwin-{arch}"
    elif system == "Windows":
        binary = f"./dist/cycletls-windows-{arch}.exe"
    else:
        # Fallback to generic binary
        binary = "./dist/cycletls"

    # Check if platform-specific binary exists, otherwise use generic
    if not os.path.exists(binary):
        binary = "./dist/cycletls"

    return binary


def kill(proc_pid):
    """
    Kill a process and all its children.

    Args:
        proc_pid: Process or PID to kill. If None, kills all 'cycletls' processes.
    """
    if proc_pid:
        process = psutil.Process(proc_pid.pid)
        for proc in process.children(recursive=True):
            proc.kill()
        process.kill()
    else:
        for proc in psutil.process_iter():
            # check whether the process name matches
            if proc.name() == "cycletls":
                proc.kill()


def _cleanup_cycletls_instance(ws, proc):
    """
    Cleanup function for weakref.finalize.

    This function has no self reference to avoid circular references.

    Args:
        ws: WebSocket connection
        proc: Subprocess instance
    """
    try:
        ws.close()
    except:
        pass

    try:
        if proc:
            kill(proc)
    except:
        pass


class CycleTLS:
    """
    CycleTLS client for making HTTP requests with advanced TLS fingerprinting.

    Supports:
    - JA3 and JA4 TLS fingerprinting
    - HTTP/1.1, HTTP/2, and HTTP/3 protocols
    - WebSocket and Server-Sent Events (SSE)
    - Connection pooling and reuse
    - Advanced proxy support (HTTP, HTTPS, SOCKS4, SOCKS5)
    - Binary data handling
    - Custom TLS configuration
    """

    def __init__(self, port=9112):
        """
        Initialize CycleTLS client.

        Args:
            port (int): WebSocket port to use (default: 9112)
        """
        self.port = port
        self.ws_url = f"ws://localhost:{port}"
        self._lock = threading.RLock()  # Thread-safe WebSocket access

        try:
            self.ws = create_connection(self.ws_url)
            self.proc = None
        except:
            # Start the Go binary subprocess
            binary_path = get_binary_path()
            env = os.environ.copy()
            env["WS_PORT"] = str(port)

            self.proc = subprocess.Popen([binary_path], shell=True, env=env)
            # Wait for server to start
            sleep(0.1)

            self.ws = create_connection(self.ws_url)

        # Register weakref finalizer for automatic cleanup
        self._finalizer = weakref.finalize(
            self,
            _cleanup_cycletls_instance,
            self.ws,
            self.proc
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.close()
        return False

    def __del__(self):
        """Safe cleanup on deletion."""
        try:
            self.close()
        except:
            pass

    def request(self, method, url, params=None, data=None, json_data=None, files=None, **kwargs):
        """
        Send an HTTP request with enhanced data handling.

        Args:
            method (str): HTTP method (GET, POST, PUT, etc.)
            url (str): Target URL
            params (Optional[Dict]): Query parameters to append to URL
            data (Optional[Union[Dict, str, bytes]]): Form data or raw body
                - If dict: URL-encoded and Content-Type set to application/x-www-form-urlencoded
                - If str/bytes: Sent as-is
            json_data (Optional[Dict]): JSON data (auto-serialized with Content-Type: application/json)
            files (Optional[Dict]): File uploads (TODO: Not yet implemented)
            **kwargs: Additional options (headers, cookies, proxy, timeout, etc.)

        Returns:
            Response: Response object with status, headers, body, cookies, etc.

        Examples:
            # Send JSON data
            response = client.request('POST', url, json_data={'key': 'value'})

            # Send form data
            response = client.request('POST', url, data={'username': 'john', 'password': 'secret'})

            # Send raw data
            response = client.request('POST', url, data=b'raw bytes')

            # Use cookies as dict
            response = client.request('GET', url, cookies={'session': 'abc123'})
        """
        # Handle deprecated body/body_bytes parameters
        if 'body' in kwargs:
            warnings.warn(
                "The 'body' parameter is deprecated. Use 'data' instead.",
                DeprecationWarning,
                stacklevel=2
            )
            if data is None:
                data = kwargs.pop('body')

        if 'body_bytes' in kwargs:
            warnings.warn(
                "The 'body_bytes' parameter is deprecated. Use 'data' instead.",
                DeprecationWarning,
                stacklevel=2
            )
            if data is None:
                data = kwargs.pop('body_bytes')

        # Initialize headers if not provided
        headers = kwargs.get('headers', {})
        if headers is None:
            headers = {}

        # Handle json parameter
        if json_data is not None:
            if data is not None:
                raise ValueError("Cannot specify both 'data' and 'json_data' parameters")
            data = json.dumps(json_data)
            headers['Content-Type'] = 'application/json'

        # Handle data parameter
        if data is not None:
            if isinstance(data, dict):
                # URL-encode form data
                data = urllib.parse.urlencode(data)
                if 'Content-Type' not in headers:
                    headers['Content-Type'] = 'application/x-www-form-urlencoded'
            elif isinstance(data, bytes):
                # Pass bytes through, use body_bytes
                kwargs['body_bytes'] = data
                data = None
            elif isinstance(data, str):
                # Pass string through as body
                kwargs['body'] = data
                data = None

        # Handle files parameter
        if files is not None:
            # TODO: Implement multipart/form-data file upload support
            raise NotImplementedError(
                "File uploads are not yet implemented. "
                "This feature will be added in a future release."
            )

        # Update headers in kwargs
        if headers:
            kwargs['headers'] = headers

        # Simplify cookie input - handle dict or CookieJar
        if 'cookies' in kwargs and kwargs['cookies'] is not None:
            cookies = kwargs['cookies']
            if isinstance(cookies, dict):
                # Convert dict to list of Cookie objects
                from .schema import Cookie
                kwargs['cookies'] = [Cookie(name=k, value=v) for k, v in cookies.items()]
            elif hasattr(cookies, '_cookies'):
                # Handle CookieJar
                kwargs['cookies'] = list(cookies._cookies.values())
            # Otherwise pass through as-is (assume it's already a list of Cookie objects)

        # Build and send request
        request = Request(method=method, url=url, params=params, **kwargs)
        request = {
            "requestId": "requestId",
            "options": request.dict(by_alias=True, exclude_none=True),
        }

        # Thread-safe WebSocket communication
        with self._lock:
            self.ws.send(json.dumps(request))
            response = json.loads(self.ws.recv())

        return Response(**response)

    def get(self, url, params=None, **kwargs) -> Response:
        """Sends a GET request.

        Args:
            url (str): URL for the new :class:`Request` object.
            params (dict): (optional) Dictionary to send in query string.
            data (Optional[Union[Dict, str, bytes]]): Form data or raw body.
                - If dict: URL-encoded with Content-Type: application/x-www-form-urlencoded
                - If str/bytes: Sent as-is
            json_data (Optional[Dict]): JSON data (auto-serialized with Content-Type: application/json)
            files (Optional[Dict]): File uploads (not yet implemented)
            headers (dict): Dictionary of HTTP Headers to send.
            cookies (Optional[Union[Dict, List[Cookie]]]): Cookies as dict or list.
                Dict will be auto-converted to Cookie objects.

            TLS Fingerprinting:
            ja3 (str): JA3 fingerprint string.
            ja4r (Optional[str]): JA4 raw format fingerprint.
            http2_fingerprint (Optional[str]): HTTP/2 fingerprint string.
            quic_fingerprint (Optional[str]): QUIC fingerprint string.
            disable_grease (bool): Disable GREASE for exact JA4 matching.

            TLS Configuration:
            server_name (Optional[str]): Custom SNI (Server Name Indication).
            insecure_skip_verify (bool): Skip TLS certificate verification.
            tls13_auto_retry (bool): Auto-retry with TLS 1.3 compatible curves.

            Protocol Options:
            force_http1 (bool): Force HTTP/1.1 protocol.
            force_http3 (bool): Force HTTP/3 protocol.
            protocol (Optional[Protocol]): Explicit protocol selection (http1, http2, http3, websocket, sse).

            Connection Options:
            user_agent (str): User Agent string.
            proxy (str): Proxy URL (format: http://username:password@hostname.com:443)
                Supports HTTP, HTTPS, SOCKS4, SOCKS5.
            timeout (int): Request timeout in seconds.
            disable_redirect (bool): Disable automatic redirects.
            enable_connection_reuse (bool): Enable connection pooling.

            Header Options:
            header_order (Optional[list]): Custom header ordering.
            order_headers_as_provided (Optional[bool]): Use provided header order.

        Returns:
            Response: Response object with request_id, status_code, headers, body,
                body_bytes, cookies, and final_url properties.

        Examples:
            # Simple GET with query params
            response = client.get(url, params={'q': 'search'})

            # GET with cookies as dict
            response = client.get(url, cookies={'session': 'abc123'})
        """
        return self.request("get", url, params=params, **kwargs)

    def options(self, url, params=None, **kwargs) -> Response:
        """Sends an OPTIONS request.

        See get() method for full parameter documentation.
        """
        return self.request("options", url, params=params, **kwargs)

    def head(self, url, params=None, **kwargs) -> Response:
        """Sends a HEAD request.

        See get() method for full parameter documentation.
        """
        return self.request("head", url, params=params, **kwargs)

    def post(self, url, params=None, data=None, json_data=None, **kwargs) -> Response:
        """Sends a POST request.

        Args:
            url (str): URL for the request.
            params (dict): (optional) Query parameters.
            data (Optional[Union[Dict, str, bytes]]): Form data or raw body.
            json_data (Optional[Dict]): JSON payload (auto-serialized).
            **kwargs: See get() method for all available options.

        Returns:
            Response: Response object.

        Examples:
            # Send JSON data
            response = client.post(url, json_data={'username': 'john', 'age': 30})

            # Send form data
            response = client.post(url, data={'username': 'john', 'password': 'secret'})

            # Send raw bytes
            response = client.post(url, data=b'raw binary data')
        """
        return self.request("post", url, params=params, data=data, json_data=json_data, **kwargs)

    def put(self, url, params=None, data=None, json_data=None, **kwargs) -> Response:
        """Sends a PUT request.

        Args:
            url (str): URL for the request.
            params (dict): (optional) Query parameters.
            data (Optional[Union[Dict, str, bytes]]): Form data or raw body.
            json_data (Optional[Dict]): JSON payload (auto-serialized).
            **kwargs: See get() method for all available options.

        Examples:
            # Update resource with JSON
            response = client.put(url, json_data={'status': 'active'})
        """
        return self.request("put", url, params=params, data=data, json_data=json_data, **kwargs)

    def patch(self, url, params=None, data=None, json_data=None, **kwargs) -> Response:
        """Sends a PATCH request.

        Args:
            url (str): URL for the request.
            params (dict): (optional) Query parameters.
            data (Optional[Union[Dict, str, bytes]]): Form data or raw body.
            json_data (Optional[Dict]): JSON payload (auto-serialized).
            **kwargs: See get() method for all available options.

        Examples:
            # Partial update with JSON
            response = client.patch(url, json_data={'name': 'New Name'})
        """
        return self.request("patch", url, params=params, data=data, json_data=json_data, **kwargs)

    def delete(self, url, params=None, **kwargs) -> Response:
        """Sends a DELETE request.

        See get() method for full parameter documentation.
        """
        return self.request("delete", url, params=params, **kwargs)

    def close(self):
        """Close the client and cleanup resources gracefully."""
        try:
            self.ws.close()
        except:
            pass

        # Graceful termination with escalation
        if self.proc is not None:
            try:
                self.proc.terminate()  # Try graceful shutdown first
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # If graceful shutdown times out, force kill
                self.proc.kill()
                try:
                    self.proc.wait(timeout=1)
                except:
                    pass
            except:
                # Best effort kill
                try:
                    self.proc.kill()
                except:
                    pass
