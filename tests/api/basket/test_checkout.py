import re
from typing import Final

import allure
import pytest

from juice_shop_e2e.api.client import JuiceShopClient
from juice_shop_e2e.api.models import AuthSession, OrderDetails
from juice_shop_e2e.data.factories import build_address, build_card

# Module-wide "Performance" category is flagged TS issue #1 (likely wrong), ported as-is.
pytestmark = [allure.epic("API: Shopping"), allure.label("category", "Performance")]

APPLE_JUICE_ID: Final = 1


@pytest.mark.smoke
def test_completes_an_order_end_to_end_and_returns_a_confirmation(
    api: JuiceShopClient, session: AuthSession
) -> None:
    with allure.step("add a product to the basket"):
        api.add_to_basket(session.basket_id, APPLE_JUICE_ID, 2)

    products = api.get_basket(session.basket_id)
    assert len(products) == 1
    assert products[0].basket_item.quantity == 2

    with allure.step("create address and card"):
        address_id = api.create_address(build_address())
        payment_id = api.create_card(build_card())

    with allure.step("check out"):
        confirmation = api.checkout(
            session.basket_id,
            OrderDetails(address_id=address_id, payment_id=payment_id, delivery_method_id=3),
        )

    assert re.fullmatch(r"[0-9a-f]{4}-[0-9a-f]+", confirmation)


# Second category label on top of the module's "Performance": flagged TS issue #1, ported as-is.
@allure.label("category", "Functional")
def test_empties_the_basket_once_the_order_is_placed(
    api: JuiceShopClient, session: AuthSession
) -> None:
    api.add_to_basket(session.basket_id, APPLE_JUICE_ID, 1)
    address_id = api.create_address(build_address())
    payment_id = api.create_card(build_card())
    api.checkout(
        session.basket_id,
        OrderDetails(address_id=address_id, payment_id=payment_id, delivery_method_id=3),
    )
    assert api.get_basket(session.basket_id) == []
