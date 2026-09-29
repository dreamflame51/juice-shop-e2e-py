from typing import Final

import allure
import pytest
from playwright.sync_api import APIRequestContext

from juice_shop_e2e.api.client import JuiceShopClient
from juice_shop_e2e.api.models import AuthSession, OrderDetails
from juice_shop_e2e.data.factories import build_address, build_card, build_user

pytestmark = [allure.epic("API: Shopping"), allure.label("category", "Security")]

APPLE_JUICE_ID: Final = 1


@pytest.fixture
def attacker(api_request_context: APIRequestContext) -> JuiceShopClient:
    """A second, independently registered and logged-in user."""
    attacker_user = build_user()
    attacker = JuiceShopClient(api_request_context)
    attacker.register(attacker_user)
    attacker.login(attacker_user)
    return attacker


def test_rejects_adding_items_to_another_users_basket(
    session: AuthSession, attacker: JuiceShopClient
) -> None:
    response = attacker.add_to_basket_raw(session.basket_id, APPLE_JUICE_ID, 1)
    assert response.status == 401


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="Known Juice Shop vulnerability: missing ownership check on GET /rest/basket/:id",
)
def test_does_not_let_another_user_read_a_victims_basket_contents(
    api: JuiceShopClient, session: AuthSession, attacker: JuiceShopClient
) -> None:
    with allure.step("victim adds an item to their own basket"):
        api.add_to_basket(session.basket_id, APPLE_JUICE_ID, 1)

    response = attacker.get_basket_raw(session.basket_id)
    assert response.status == 403


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "Known Juice Shop vulnerability: missing ownership check on POST /rest/basket/:id/checkout"
    ),
)
def test_does_not_let_another_user_check_out_a_victims_basket(
    api: JuiceShopClient, session: AuthSession, attacker: JuiceShopClient
) -> None:
    with allure.step("victim adds an item to their own basket"):
        api.add_to_basket(session.basket_id, APPLE_JUICE_ID, 1)

    with allure.step("attacker creates their own address and card"):
        address_id = attacker.create_address(build_address())
        payment_id = attacker.create_card(build_card())

    response = attacker.checkout_raw(
        session.basket_id,
        OrderDetails(address_id=address_id, payment_id=payment_id, delivery_method_id=3),
    )
    assert response.status == 403
