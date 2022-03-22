import json
from websocket import create_connection
from .schema import Response, Request
import subprocess
from time import sleep
import psutil


def kill(proc_pid):
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


class CycleTLS:
    def __init__(self):
        try:
            self.ws = create_connection("ws://localhost:8080")
            self.proc = None
        except:

            self.proc = subprocess.Popen(["./dist/cycletls"], shell=True)
            # TODO remove this
            sleep(0.1)

            self.ws = create_connection("ws://localhost:8080")

    def request(self, method, url, **kwargs):
        request = Request(method=method, url=url, **kwargs)
        request = {
            "requestId": "requestId",
            "options": request.dict(by_alias=True, exclude_none=True),
        }
        self.ws.send(json.dumps(request))
        response = json.loads(self.ws.recv())

        return Response(**response)

    def get(self, url, params=None, **kwargs) -> Response:
        """Sends an GET request.
        Args:
            url (str): URL for the new :class:`Request` object.
            params (dict): (optional) Dictionary, list of tuples or bytes to send
            in the query string for the :class:`Request`.
            body (Optional[str]): Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
            url (str): URL for the new :class:`Request` object.
            headers (dict): Dictionary of HTTP Headers to send with the :class:`Request`.
            ja3 (str): JA3 token to send with :class:`Request`.
            user_agent (str): User Agent to send with :class:`Request`.
            proxy (str): Proxy to send request through  must be in format `http://username:password@hostname.com:443`
            cookies (dict): Dict object to send with the :class:`Request`.
            disable_redirect (bool): Disable GET/OPTIONS/POST/PUT/PATCH/DELETE/HEAD redirection. Defaults to ``False``.
            header_order (Optional[list]): Optional list setting request header order.
            order_headers_as_provided (Optional[bool]): Set header_order based on provided headers
        Returns:
            Response: Response object with (request_id, status_code, headers, body)
            properties.
        """
        return self.request("get", url, params=params, **kwargs)

    def options(self, url, params=None, **kwargs) -> Response:
        """Sends an OPTIONS request.
        Args:
            url (str): URL for the new :class:`Request` object.
            params (dict): (optional) Dictionary, list of tuples or bytes to send
            in the query string for the :class:`Request`.
            body (Optional[str]): Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
            url (str): URL for the new :class:`Request` object.
            headers (dict): Dictionary of HTTP Headers to send with the :class:`Request`.
            ja3 (str): JA3 token to send with :class:`Request`.
            user_agent (str): User Agent to send with :class:`Request`.
            proxy (str): Proxy to send request through  must be in format `http://username:password@hostname.com:443`
            cookies (dict): Dict object to send with the :class:`Request`.
            disable_redirect (bool): Disable GET/OPTIONS/POST/PUT/PATCH/DELETE/HEAD redirection. Defaults to ``False``.
            header_order (Optional[list]): Optional list setting request header order.
            order_headers_as_provided (Optional[bool]): Set header_order based on provided headers
        Returns:
            Response: Response object with (request_id, status_code, headers, body)
            properties.
        """
        return self.request("options", url, params=params, **kwargs)

    def head(self, url, params=None, **kwargs) -> Response:
        """Sends an HEAD request.
        Args:
            url (str): URL for the new :class:`Request` object.
            params (dict): (optional) Dictionary, list of tuples or bytes to send
            in the query string for the :class:`Request`.
            body (Optional[str]): Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
            url (str): URL for the new :class:`Request` object.
            headers (dict): Dictionary of HTTP Headers to send with the :class:`Request`.
            ja3 (str): JA3 token to send with :class:`Request`.
            user_agent (str): User Agent to send with :class:`Request`.
            proxy (str): Proxy to send request through  must be in format `http://username:password@hostname.com:443`
            cookies (dict): Dict object to send with the :class:`Request`.
            disable_redirect (bool): Disable GET/OPTIONS/POST/PUT/PATCH/DELETE/HEAD redirection. Defaults to ``False``.
            header_order (Optional[list]): Optional list setting request header order.
            order_headers_as_provided (Optional[bool]): Set header_order based on provided headers
        Returns:
            Response: Response object with (request_id, status_code, headers, body)
            properties.
        """
        return self.request("head", url, params=params, **kwargs)

    def post(self, url, params=None, **kwargs) -> Response:
        """Sends an POST request.
        Args:
            url (str): URL for the new :class:`Request` object.
            params (dict): (optional) Dictionary, list of tuples or bytes to send
            in the query string for the :class:`Request`.
            body (Optional[str]): Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
            url (str): URL for the new :class:`Request` object.
            headers (dict): Dictionary of HTTP Headers to send with the :class:`Request`.
            ja3 (str): JA3 token to send with :class:`Request`.
            user_agent (str): User Agent to send with :class:`Request`.
            proxy (str): Proxy to send request through  must be in format `http://username:password@hostname.com:443`
            cookies (dict): Dict object to send with the :class:`Request`.
            disable_redirect (bool): Disable GET/OPTIONS/POST/PUT/PATCH/DELETE/HEAD redirection. Defaults to ``False``.
            header_order (Optional[list]): Optional list setting request header order.
            order_headers_as_provided (Optional[bool]): Set header_order based on provided headers
        Returns:
            Response: Response object with (request_id, status_code, headers, body)
            properties.
        """
        return self.request("post", url, params=params, **kwargs)

    def put(self, url, params=None, **kwargs) -> Response:
        """Sends an PUT request.
        Args:
            url (str): URL for the new :class:`Request` object.
            params (dict): (optional) Dictionary, list of tuples or bytes to send
            in the query string for the :class:`Request`.
            body (Optional[str]): Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
            url (str): URL for the new :class:`Request` object.
            headers (dict): Dictionary of HTTP Headers to send with the :class:`Request`.
            ja3 (str): JA3 token to send with :class:`Request`.
            user_agent (str): User Agent to send with :class:`Request`.
            proxy (str): Proxy to send request through  must be in format `http://username:password@hostname.com:443`
            cookies (dict): Dict object to send with the :class:`Request`.
            disable_redirect (bool): Disable GET/OPTIONS/POST/PUT/PATCH/DELETE/HEAD redirection. Defaults to ``False``.
            header_order (Optional[list]): Optional list setting request header order.
            order_headers_as_provided (Optional[bool]): Set header_order based on provided headers
        Returns:
            Response: Response object with (request_id, status_code, headers, body)
            properties.
        """
        return self.request("put", url, params=params, **kwargs)

    def patch(self, url, params=None, **kwargs) -> Response:
        """Sends an PATCH request.
        Args:
            url (str): URL for the new :class:`Request` object.
            params (dict): (optional) Dictionary, list of tuples or bytes to send
            in the query string for the :class:`Request`.
            body (Optional[str]): Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
            url (str): URL for the new :class:`Request` object.
            headers (dict): Dictionary of HTTP Headers to send with the :class:`Request`.
            ja3 (str): JA3 token to send with :class:`Request`.
            user_agent (str): User Agent to send with :class:`Request`.
            proxy (str): Proxy to send request through  must be in format `http://username:password@hostname.com:443`
            cookies (dict): Dict object to send with the :class:`Request`.
            disable_redirect (bool): Disable GET/OPTIONS/POST/PUT/PATCH/DELETE/HEAD redirection. Defaults to ``False``.
            header_order (Optional[list]): Optional list setting request header order.
            order_headers_as_provided (Optional[bool]): Set header_order based on provided headers
        Returns:
            Response: Response object with (request_id, status_code, headers, body)
            properties.
        """
        return self.request("patch", url, params=params, **kwargs)

    def delete(self, url, params=None, **kwargs) -> Response:
        """Sends an DELETE request.
        Args:
            url (str): URL for the new :class:`Request` object.
            params (dict): (optional) Dictionary, list of tuples or bytes to send
            in the query string for the :class:`Request`.
            body (Optional[str]): Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
            url (str): URL for the new :class:`Request` object.
            headers (dict): Dictionary of HTTP Headers to send with the :class:`Request`.
            ja3 (str): JA3 token to send with :class:`Request`.
            user_agent (str): User Agent to send with :class:`Request`.
            proxy (str): Proxy to send request through  must be in format `http://username:password@hostname.com:443`
            cookies (dict): Dict object to send with the :class:`Request`.
            disable_redirect (bool): Disable GET/OPTIONS/POST/PUT/PATCH/DELETE/HEAD redirection. Defaults to ``False``.
            header_order (Optional[list]): Optional list setting request header order.
            order_headers_as_provided (Optional[bool]): Set header_order based on provided headers
        Returns:
            Response: Response object with (request_id, status_code, headers, body)
            properties.
        """
        return self.request("delete", url, params=params, **kwargs)

    def close(self):
        self.ws.close()

        kill(self.proc)
