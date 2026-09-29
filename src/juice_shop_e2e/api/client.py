from typing import Final

from playwright.sync_api import APIRequestContext, APIResponse

from juice_shop_e2e.api.models import AuthSession, LoginResponse
from juice_shop_e2e.data.factories import User

LOGIN: Final = "/rest/user/login"
USERS: Final = "/api/Users/"
BASKET_ITEMS: Final = "/api/BasketItems/"


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
