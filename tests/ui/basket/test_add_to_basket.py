import re
from typing import Final

import allure
import pytest
from playwright.sync_api import expect

from juice_shop_e2e.api.client import JuiceShopClient
from juice_shop_e2e.api.models import AuthSession
from juice_shop_e2e.pages.basket_page import BasketPage
from juice_shop_e2e.pages.products_page import ProductsPage

pytestmark = [allure.epic("UI: Shopping"), allure.label("category", "Functional")]

PRODUCT: Final = "Apple Juice (1000ml)"


@pytest.mark.smoke
@pytest.mark.usefixtures("authed_page")
def test_an_authenticated_user_can_add_a_product_to_the_basket(
    products_page: ProductsPage, basket_page: BasketPage
) -> None:
    with allure.step("add the product from the catalogue"):
        products_page.open()
        products_page.add_to_basket(PRODUCT)

    expect(products_page.snackbar).to_contain_text(
        re.compile(r"placed .* into basket", re.IGNORECASE)
    )

    with allure.step("open the basket"):
        basket_page.open()

    expect(basket_page.row(PRODUCT)).to_be_visible()
    # Flagged TS issue #2: /1/ also matches "10", "21"; kept as in the TS source.
    expect(basket_page.quantity_of(PRODUCT)).to_have_text(re.compile(r"1"))
    expect(basket_page.checkout_button).to_be_enabled()


@pytest.mark.usefixtures("authed_page")
def test_basket_seeded_through_the_api_is_reflected_in_the_ui(
    api: JuiceShopClient, session: AuthSession, basket_page: BasketPage
) -> None:
    with allure.step("seed two units via the API"):
        api.add_to_basket(session.basket_id, 1, 2)

    basket_page.open()
    # Flagged TS issue #2: /2/ also matches "12", "20"; kept as in the TS source.
    expect(basket_page.quantity_of(PRODUCT)).to_have_text(re.compile(r"2"))
