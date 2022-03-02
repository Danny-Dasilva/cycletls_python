import websocket
import json
from websocket import create_connection
from typing import Optional
from pprint import pprint
from pydantic import BaseModel, Field


class Cookie(BaseModel):
    test: int


class Request(BaseModel):
    url: str
    method: str
    body: str = ""
    headers: dict = {}
    ja3: str = "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0"
    user_agent: str = (
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0"
    )
    proxy: str = ""
    cookies: Optional[list[Cookie]]
    timeout: int = 6
    disable_redirect: bool = False
    header_order: Optional[list]
    order_headers_as_provided: Optional[bool]

    class Config:
        fields = {
            "user_agent": "userAgent",
            "disable_redirect": "disableRedirect",
        }


class Response(BaseModel):
    request_id: str
    status_code: int
    headers: dict
    body: str

    class Config:
        fields = {
            "request_id": "RequestID",
            "status_code": "Status",
            "headers": "Headers",
            "body": "Body",
        }

    def json(self) -> dict:
        return json.loads(self.body)


class CycleTLS:
    def __init__(self):
        self.ws = create_connection("ws://localhost:8080/ws")

    def request(self, method, url, **kwargs):
        request = Request(method=method, url=url, **kwargs)
        request = {"requestId": "testreqeust", "options": request.dict(by_alias=True)}
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

    def close(self):
        self.ws.close()







cycle = CycleTLS()
result = cycle.get("https://ja3er.com/json")

print(result)

print("\n")

pprint(result.json())

cycle.close()




