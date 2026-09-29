import re

from playwright.sync_api import Locator, Page


class ProductsPage:
    def __init__(self, page: Page) -> None:
        self._page = page
        self.product_cards = page.locator("mat-card")
        self._search_toggle = page.locator(".mat-search_icon-search")
        self._search_input = page.locator(".mat-search_field input")
        self.no_results_message = page.get_by_text("No results found")
        self.snackbar = page.locator(".mat-simple-snack-bar-content")

    def open(self) -> None:
        self._page.goto("/#/search")

    def search(self, term: str) -> None:
        self._search_toggle.click()
        self._search_input.fill(term)
        self._search_input.press("Enter")

    def product_card(self, name: str) -> Locator:
        return self.product_cards.filter(has_text=name)

    def add_to_basket(self, name: str) -> None:
        self.product_card(name).get_by_role(
            "button", name=re.compile(r"add to basket", re.IGNORECASE)
        ).click()
