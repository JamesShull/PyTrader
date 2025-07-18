from pydantic import BaseModel, Field
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
    exp: datetime
    scopes: list[str] = Field(default_factory=list)

# User models
class UserInDB(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None
    scopes: list[str] = Field(default_factory=list)
    hashed_password: str
