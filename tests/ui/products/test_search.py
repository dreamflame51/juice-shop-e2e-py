import pytest
from playwright.sync_api import expect

from juice_shop_e2e.pages.products_page import ProductsPage

# TODO(lesson-10): allure epic "UI: Shopping", category "Functional"


@pytest.mark.smoke
def test_returns_only_products_matching_the_search_term(products_page: ProductsPage) -> None:
    # TODO(lesson-10): allure step 'open the catalogue and search for "apple"'
    products_page.open()
    products_page.search("apple")
    expect(products_page.product_cards).to_have_count(2)
    expect(products_page.product_cards).to_contain_text(["Apple Juice", "Apple Pomace"])


def test_shows_a_no_results_state_for_a_term_that_matches_nothing(
    products_page: ProductsPage,
) -> None:
    # TODO(lesson-10): allure step 'search for a term no product matches'
    products_page.open()
    products_page.search("zzzzznoresult")
    expect(products_page.no_results_message).to_be_visible()
