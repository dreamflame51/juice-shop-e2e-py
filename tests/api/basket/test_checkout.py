import re
from typing import Final

import pytest

from juice_shop_e2e.api.client import JuiceShopClient
from juice_shop_e2e.api.models import AuthSession, OrderDetails
from juice_shop_e2e.data.factories import build_address, build_card

# TODO(lesson-10): allure epic "API: Shopping"; category "Performance" on the module
#   (flagged TS issue #1, ported as-is)

APPLE_JUICE_ID: Final = 1


@pytest.mark.smoke
def test_completes_an_order_end_to_end_and_returns_a_confirmation(
    api: JuiceShopClient, session: AuthSession
) -> None:
    # TODO(lesson-10): step 'add a product to the basket'
    api.add_to_basket(session.basket_id, APPLE_JUICE_ID, 2)
    products = api.get_basket(session.basket_id)
    assert len(products) == 1
    assert products[0].basket_item.quantity == 2

    # TODO(lesson-10): step 'create address and card'
    address_id = api.create_address(build_address())
    payment_id = api.create_card(build_card())

    # TODO(lesson-10): step 'check out'
    confirmation = api.checkout(
        session.basket_id,
        OrderDetails(address_id=address_id, payment_id=payment_id, delivery_method_id=3),
    )

    assert re.fullmatch(r"[0-9a-f]{4}-[0-9a-f]+", confirmation)


def test_empties_the_basket_once_the_order_is_placed(
    api: JuiceShopClient, session: AuthSession
) -> None:
    # TODO(lesson-10): category "Functional" (in addition to the module's "Performance":
    #   flagged TS issue #1)
    api.add_to_basket(session.basket_id, APPLE_JUICE_ID, 1)
    address_id = api.create_address(build_address())
    payment_id = api.create_card(build_card())
    api.checkout(
        session.basket_id,
        OrderDetails(address_id=address_id, payment_id=payment_id, delivery_method_id=3),
    )
    assert api.get_basket(session.basket_id) == []
