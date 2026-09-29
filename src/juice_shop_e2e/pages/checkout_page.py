import re

from playwright.sync_api import Page


class CheckoutPage:
    """Drives the address -> delivery -> payment -> review checkout wizard.

    Assumes an address and a card already exist.
    """

    def __init__(self, page: Page) -> None:
        self._page = page
        # Each step shows exactly one radio table; the locator is re-resolved on every action.
        self.first_option = page.get_by_role("radio").first
        # Accessible name is "Proceed to ..." on every wizard step.
        self.continue_button = page.get_by_role("button", name=re.compile(r"^Proceed to"))
        self.place_order_button = page.get_by_role("button", name="Complete your purchase")
        self.confirmation_heading = page.get_by_role("heading", name="Thank you for your purchase!")

    def _pick_first_option_and_continue(self) -> None:
        # mat-radio's inner circle overlays the input and intercepts plain clicks.
        self.first_option.click(force=True)
        self.continue_button.click()

    def select_address(self) -> None:
        self._pick_first_option_and_continue()

    def select_delivery_method(self) -> None:
        self._pick_first_option_and_continue()

    def select_payment(self) -> None:
        self._pick_first_option_and_continue()

    def place_order(self) -> None:
        self.place_order_button.click()
