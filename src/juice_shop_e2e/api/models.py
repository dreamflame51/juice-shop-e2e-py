from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class Authentication(BaseModel):
    token: str
    bid: int
    umail: str


class LoginResponse(BaseModel):
    authentication: Authentication


class AuthSession(BaseModel):
    token: str
    basket_id: int


class BasketItem(BaseModel):
    quantity: int


class BasketProduct(BaseModel):
    id: int
    name: str
    price: float
    basket_item: BasketItem = Field(alias="BasketItem")


class BasketData(BaseModel):
    products: list[BasketProduct] = Field(alias="Products")


class BasketResponse(BaseModel):
    data: BasketData


class CreatedEntity(BaseModel):
    id: int


class CreatedResponse(BaseModel):
    """Shape of Juice Shop's `POST /api/<Entity>/` responses: {"data": {"id": ...}}."""

    data: CreatedEntity


class OrderDetails(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True)
    address_id: int
    payment_id: int
    delivery_method_id: int


class CheckoutResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True)
    order_confirmation: str
