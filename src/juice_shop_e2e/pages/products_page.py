from playwright.sync_api import Page


class ProductsPage:
    def __init__(self, page: Page) -> None:
        self._page = page
        self.product_cards = page.locator("mat-card")
        self._search_toggle = page.locator(".mat-search_icon-search")
        self._search_input = page.locator(".mat-search_field input")
        self.no_results_message = page.get_by_text("No results found")

    def open(self) -> None:
        self._page.goto("/#/search")

    def search(self, term: str) -> None:
        self._search_toggle.click()
        self._search_input.fill(term)
        self._search_input.press("Enter")
