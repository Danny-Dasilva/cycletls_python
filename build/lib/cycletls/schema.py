from pydantic import BaseModel
import json
from typing import Optional

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
    cookies: Optional[list[Cookie]] = None
    timeout: int = 6
    disable_redirect: bool = False
    header_order: Optional[list] = None
    order_headers_as_provided: Optional[bool] = None

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



