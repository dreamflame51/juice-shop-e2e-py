from typing import Final

from playwright.sync_api import APIRequestContext, APIResponse

from juice_shop_e2e.api.models import (
    AuthSession,
    BasketProduct,
    BasketResponse,
    CheckoutResponse,
    CreatedResponse,
    LoginResponse,
    OrderDetails,
)
from juice_shop_e2e.data.factories import Address, Card, User

ADDRESSES: Final = "/api/Addresss/"
CARDS: Final = "/api/Cards/"
LOGIN: Final = "/rest/user/login"
USERS: Final = "/api/Users/"
BASKET_ITEMS: Final = "/api/BasketItems/"


def _basket(basket_id: int) -> str:
    return f"/rest/basket/{basket_id}"


def _checkout(basket_id: int) -> str:
    return f"{_basket(basket_id)}/checkout"


class ApiError(Exception):
    """Raised when the SUT answers with a non-2xx status."""


def _ensure_ok(response: APIResponse) -> APIResponse:
    if not response.ok:
        raise ApiError(f"{response.url} -> {response.status}: {response.text()}")
    return response


class JuiceShopClient:
    def __init__(self, request: APIRequestContext) -> None:
        self._request = request
        self._token: str | None = None

    @property
    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"} if self._token else {}

    def add_to_basket_raw(self, basket_id: int, product_id: int, quantity: int) -> APIResponse:
        # TODO(lesson-10): allure step + request/response attachments
        data = {"BasketId": basket_id, "ProductId": product_id, "quantity": quantity}
        return self._request.post(BASKET_ITEMS, headers=self._auth_headers, data=data)

    def add_to_basket(self, basket_id: int, product_id: int, quantity: int) -> None:
        _ensure_ok(self.add_to_basket_raw(basket_id, product_id, quantity))

    def get_basket_raw(self, basket_id: int) -> APIResponse:
        # TODO(lesson-10): allure step + request/response attachments
        return self._request.get(_basket(basket_id), headers=self._auth_headers)

    def get_basket(self, basket_id: int) -> list[BasketProduct]:
        response = _ensure_ok(self.get_basket_raw(basket_id))
        body = BasketResponse.model_validate(response.json())
        return body.data.products

    def create_address(self, address: Address) -> int:
        # TODO(lesson-10): allure step + request/response attachments
        response = _ensure_ok(
            self._request.post(
                ADDRESSES, headers=self._auth_headers, data=address.model_dump(by_alias=True)
            )
        )
        return CreatedResponse.model_validate(response.json()).data.id

    def create_card(self, card: Card) -> int:
        # TODO(lesson-10): allure step + request/response attachments
        response = _ensure_ok(
            self._request.post(
                CARDS, headers=self._auth_headers, data=card.model_dump(by_alias=True)
            )
        )
        return CreatedResponse.model_validate(response.json()).data.id

    def checkout_raw(self, basket_id: int, order_details: OrderDetails) -> APIResponse:
        # TODO(lesson-10): allure step + request/response attachments
        data = {"couponData": "", "orderDetails": order_details.model_dump(by_alias=True)}
        return self._request.post(_checkout(basket_id), headers=self._auth_headers, data=data)

    def checkout(self, basket_id: int, order_details: OrderDetails) -> str:
        response = _ensure_ok(self.checkout_raw(basket_id, order_details))
        return CheckoutResponse.model_validate(response.json()).order_confirmation

    def login_raw(self, email: str, password: str) -> APIResponse:
        # TODO(lesson-10): allure step + request/response attachments
        return self._request.post(LOGIN, data={"email": email, "password": password})

    def register(self, user: User) -> None:
        # TODO(lesson-10): allure step + request/response attachments
        data = {
            "email": user.email,
            "password": user.password,
            "passwordRepeat": user.password,
            "securityQuestion": {"id": 1},
            "securityAnswer": user.security_answer,
        }
        _ensure_ok(self._request.post(USERS, data=data))

    def login(self, user: User) -> AuthSession:
        # TODO(lesson-10): allure step + request/response attachments
        response = _ensure_ok(self.login_raw(user.email, user.password))
        body = LoginResponse.model_validate(response.json())
        self._token = body.authentication.token
        return AuthSession(token=body.authentication.token, basket_id=body.authentication.bid)
