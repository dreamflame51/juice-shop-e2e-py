from collections.abc import Iterator

import pytest
from playwright.sync_api import APIRequestContext, Playwright

from juice_shop_e2e.api.client import JuiceShopClient
from juice_shop_e2e.config import get_settings


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
