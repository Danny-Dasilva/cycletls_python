from pydantic import BaseModel, Field

class UserResource(BaseModel):
    id: int = Field(alias="identifier")
    name: str = Field(alias="fullname")

te = {"identifier": 1, "fullname": "test"}
test = UserResource(**te)
print(test)
