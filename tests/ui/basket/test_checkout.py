import re
from typing import Final

import pytest
from playwright.sync_api import Page, expect

from juice_shop_e2e.api.client import JuiceShopClient
from juice_shop_e2e.data.factories import build_address, build_card
from juice_shop_e2e.pages.basket_page import BasketPage
from juice_shop_e2e.pages.checkout_page import CheckoutPage
from juice_shop_e2e.pages.products_page import ProductsPage

# TODO(lesson-10): allure epic "UI: Shopping", category "Functional"

PRODUCT: Final = "Apple Juice (1000ml)"


@pytest.mark.smoke
@pytest.mark.usefixtures("session")
def test_a_user_can_complete_checkout_end_to_end(
    api: JuiceShopClient,
    authed_page: Page,
    products_page: ProductsPage,
    basket_page: BasketPage,
    checkout_page: CheckoutPage,
) -> None:
    # TODO(lesson-10): step 'seed a delivery address and payment card via the API'
    api.create_address(build_address())
    api.create_card(build_card())

    # TODO(lesson-10): step 'add the product to the basket'
    products_page.open()
    products_page.add_to_basket(PRODUCT)
    expect(products_page.snackbar).to_contain_text(
        re.compile(r"placed .* into basket", re.IGNORECASE)
    )

    # TODO(lesson-10): step 'go to checkout'
    basket_page.open()
    basket_page.checkout_button.click()

    # TODO(lesson-10): steps 'select the delivery address', 'select the delivery method',
    #   'select the payment method', 'place the order'
    checkout_page.select_address()
    checkout_page.select_delivery_method()
    checkout_page.select_payment()
    checkout_page.place_order()

    expect(checkout_page.confirmation_heading).to_be_visible()
    expect(authed_page).to_have_url(re.compile(r"#/order-completion/[0-9a-f-]+$"))
