from playwright.sync_api import Page


class LoginPage:
    def __init__(self, page: Page) -> None:
        self._page = page
        self.email = page.locator("#email")
        self.password = page.locator("#password")
        self.submit_button = page.locator("#loginButton")
        self.error_message = page.locator(".error")
        self.register_link = page.locator("#newCustomerLink")

    def open(self) -> None:
        self._page.goto("/#/login")

    def login(self, email: str, password: str) -> None:
        self.email.fill(email)
        self.password.fill(password)
        self.submit_button.click()
