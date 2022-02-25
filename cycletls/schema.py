from typing import Optional
from pydantic import BaseModel
class Cookie(BaseModel):
    test: int
class Request(BaseModel):
    url: str
    method: str
    headers: dict = {}
    body: str = ""
    ja3: str = ""
    proxy: str = ""
    cookies: Optional[list[Cookie]]
    timeout: int =  6 
    disable_redirect: bool = False
    header_order: Optional[list]  
    order_as_provided: Optional[bool]


class Response(BaseModel):
    request_id: str
    status_code: int
    headers: dict 
    body: str

    def json(self):
        return json.loads(self.body)


