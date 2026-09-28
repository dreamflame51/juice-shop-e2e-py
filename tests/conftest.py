from collections.abc import Iterator

import pytest
from playwright.sync_api import APIRequestContext, Playwright, expect

from juice_shop_e2e.api.client import JuiceShopClient
from juice_shop_e2e.config import get_settings
from juice_shop_e2e.data.factories import User, build_user

expect.set_options(timeout=10_000)


@pytest.fixture(scope="session")
def base_url() -> str:
    return str(get_settings().base_url)


@pytest.fixture
def api_request_context(playwright: Playwright, base_url: str) -> Iterator[APIRequestContext]:
    """Playwright API context. Not named `request`: that name is pytest's FixtureRequest."""
    context = playwright.request.new_context(base_url=base_url)
    yield context
    context.dispose()


@pytest.fixture
def api(api_request_context: APIRequestContext) -> JuiceShopClient:
    return JuiceShopClient(api_request_context)


@pytest.fixture
def test_user() -> User:
    """Freshly generated, NOT yet registered."""
    return build_user()


@pytest.fixture
def registered_user(api: JuiceShopClient, test_user: User) -> User:
    """Registered via the API: use when registration itself is not under test."""
    api.register(test_user)
    return test_user
