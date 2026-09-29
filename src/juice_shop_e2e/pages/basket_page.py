from playwright.sync_api import Locator, Page


class BasketPage:
    def __init__(self, page: Page) -> None:
        self._page = page
        self.rows = page.locator("mat-row")
        self.checkout_button = page.locator("#checkoutButton")

    def open(self) -> None:
        self._page.goto("/#/basket")

    def row(self, product_name: str) -> Locator:
        return self.rows.filter(has_text=product_name)

    def quantity_of(self, product_name: str) -> Locator:
        return self.row(product_name).locator(".mat-column-quantity")
