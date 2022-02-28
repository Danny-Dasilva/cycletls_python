import websocket
import json
from websocket import create_connection
from typing import Optional
from pydantic import BaseModel
	# URL             string            `json:"url"`
	# Method          string            `json:"method"`
	# Headers         map[string]string `json:"headers"`
	# Body            string            `json:"body"`
	# Ja3             string            `json:"ja3"`
	# UserAgent       string            `json:"userAgent"`
	# Proxy           string            `json:"proxy"`
	# Cookies         []Cookie          `json:"cookies"`
	# Timeout         int               `json:"timeout"`
	# DisableRedirect bool              `json:"disableRedirect"`
	# HeaderOrder     []string          `json:"headerOrder"`
	# OrderAsProvided bool              `json:"orderAsProvided"` /
class Cookie(BaseModel):
    test: int
class Request(BaseModel):
    url: str
    method: str
    body: str = ""
    headers: dict = {}
    ja3: str = ""
    user_agent: str = ""
    proxy: str = ""
    cookies: Optional[list[Cookie]]
    timeout: int =  6 
    disable_redirect: bool = False
    header_order: Optional[list]  
    order_headers_as_provided: Optional[bool]


class Response(BaseModel):
    request_id: str
    status_code: int
    headers: dict 
    body: str

    def json(self):
        return json.loads(self.body)

class CycleTLS():
    def __init__(self):
        self.ws = create_connection("ws://localhost:9112")

    def request(self, method, url, **kwargs):
        request =  Request(method=method,url=url, **kwargs)
        self.ws.send(json.dumps(request.dict()))
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
        return self.request('get', url, params=params, **kwargs)
    
    def close(self):
        self.ws.close()

cycle = CycleTLS()
result = cycle.get("https://ja3er.com")
print(result, "return")
print(result.json())
cycle.close()
