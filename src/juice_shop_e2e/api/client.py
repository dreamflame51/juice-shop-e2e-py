from typing import Final

from playwright.sync_api import APIRequestContext, APIResponse

LOGIN: Final = "/rest/user/login"


class JuiceShopClient:
    def __init__(self, request: APIRequestContext) -> None:
        self._request = request

    def login_raw(self, email: str, password: str) -> APIResponse:
        # TODO(lesson-10): allure step + request/response attachments
        return self._request.post(LOGIN, data={"email": email, "password": password})
