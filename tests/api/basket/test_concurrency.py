from typing import Final
from urllib.parse import urljoin

import allure
import pytest

from juice_shop_e2e.api.client import BASKET_ITEMS, JuiceShopClient
from juice_shop_e2e.api.models import AuthSession
from juice_shop_e2e.utils.concurrent_http import post_json_concurrently

pytestmark = [allure.epic("API: Shopping"), allure.label("category", "Functional")]

APPLE_JUICE_ID: Final = 1
CONCURRENT_ADDS: Final = 5


@pytest.mark.smoke
@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "Known Juice Shop race: concurrent POST /api/BasketItems/ for the same product "
        "race on the 'row exists' check, all but one answer 500"
    ),
)
def test_concurrent_adds_of_the_same_product_are_not_lost(
    api: JuiceShopClient, session: AuthSession, base_url: str
) -> None:
    responses = post_json_concurrently(
        urljoin(base_url, BASKET_ITEMS),
        payload={
            "BasketId": session.basket_id,
            "ProductId": APPLE_JUICE_ID,
            "quantity": 1,
        },
        headers={"Authorization": f"Bearer {session.token}"},
        times=CONCURRENT_ADDS,
    )

    assert all(response.status == 200 for response in responses)
    products = api.get_basket(session.basket_id)
    assert sum(product.basket_item.quantity for product in products) == CONCURRENT_ADDS
