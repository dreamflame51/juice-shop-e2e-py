import json
from collections.abc import Callable
from typing import Final

import allure
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

USERS: Final = "/api/Users/"
LOGIN: Final = "/rest/user/login"
BASKET_ITEMS: Final = "/api/BasketItems/"
ADDRESSES: Final = "/api/Addresss/"  # sic: the real Juice Shop route
CARDS: Final = "/api/Cards/"


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

    def _call(
        self, step_name: str, request_body: object, send: Callable[[], APIResponse]
    ) -> APIResponse:
        """Runs an API call inside an Allure step, attaching request/response payloads."""
        with allure.step(step_name):
            if request_body is not None:
                allure.attach(
                    json.dumps(request_body, indent=2),
                    name="Request",
                    attachment_type=allure.attachment_type.JSON,
                )
            response = send()
            allure.attach(
                f"{response.status} {response.url}\n{response.text()}",
                name="Response",
                attachment_type=allure.attachment_type.TEXT,
            )
            return response

    def register(self, user: User) -> None:
        data = {
            "email": user.email,
            "password": user.password,
            "passwordRepeat": user.password,
            "securityQuestion": {"id": 1},
            "securityAnswer": user.security_answer,
        }
        _ensure_ok(self._call(f"POST {USERS}", data, lambda: self._request.post(USERS, data=data)))

    def login_raw(self, email: str, password: str) -> APIResponse:
        data = {"email": email, "password": password}
        return self._call(f"POST {LOGIN}", data, lambda: self._request.post(LOGIN, data=data))

    def login(self, user: User) -> AuthSession:
        response = _ensure_ok(self.login_raw(user.email, user.password))
        body = LoginResponse.model_validate(response.json())
        self._token = body.authentication.token
        return AuthSession(token=body.authentication.token, basket_id=body.authentication.bid)

    def add_to_basket_raw(self, basket_id: int, product_id: int, quantity: int) -> APIResponse:
        data = {"BasketId": basket_id, "ProductId": product_id, "quantity": quantity}
        return self._call(
            f"POST {BASKET_ITEMS}",
            data,
            lambda: self._request.post(BASKET_ITEMS, headers=self._auth_headers, data=data),
        )

    def add_to_basket(self, basket_id: int, product_id: int, quantity: int) -> None:
        _ensure_ok(self.add_to_basket_raw(basket_id, product_id, quantity))

    def get_basket_raw(self, basket_id: int) -> APIResponse:
        url = _basket(basket_id)
        return self._call(
            f"GET {url}", None, lambda: self._request.get(url, headers=self._auth_headers)
        )

    def get_basket(self, basket_id: int) -> list[BasketProduct]:
        response = _ensure_ok(self.get_basket_raw(basket_id))
        return BasketResponse.model_validate(response.json()).data.products

    def create_address(self, address: Address) -> int:
        data = address.model_dump(by_alias=True)
        response = _ensure_ok(
            self._call(
                f"POST {ADDRESSES}",
                data,
                lambda: self._request.post(ADDRESSES, headers=self._auth_headers, data=data),
            )
        )
        return CreatedResponse.model_validate(response.json()).data.id

    def create_card(self, card: Card) -> int:
        data = card.model_dump(by_alias=True)
        response = _ensure_ok(
            self._call(
                f"POST {CARDS}",
                data,
                lambda: self._request.post(CARDS, headers=self._auth_headers, data=data),
            )
        )
        return CreatedResponse.model_validate(response.json()).data.id

    def checkout_raw(self, basket_id: int, order_details: OrderDetails) -> APIResponse:
        url = _checkout(basket_id)
        data = {"couponData": "", "orderDetails": order_details.model_dump(by_alias=True)}
        return self._call(
            f"POST {url}",
            data,
            lambda: self._request.post(url, headers=self._auth_headers, data=data),
        )

    def checkout(self, basket_id: int, order_details: OrderDetails) -> str:
        response = _ensure_ok(self.checkout_raw(basket_id, order_details))
        return CheckoutResponse.model_validate(response.json()).order_confirmation
