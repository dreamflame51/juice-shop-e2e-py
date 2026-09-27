from pydantic import BaseModel


class Authentication(BaseModel):
    token: str
    bid: int
    umail: str


class LoginResponse(BaseModel):
    authentication: Authentication


class AuthSession(BaseModel):
    token: str
    basket_id: int
