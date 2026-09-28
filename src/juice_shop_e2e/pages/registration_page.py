from playwright.sync_api import Page

from juice_shop_e2e.data.factories import User
from juice_shop_e2e.utils.wait import click_until_visible


class RegistrationPage:
    def __init__(self, page: Page) -> None:
        self._page = page
        self.email = page.locator("#emailControl")
        self.password = page.locator("#passwordControl")
        self.repeat_password = page.locator("#repeatPasswordControl")
        self.security_question = page.locator('mat-select[name="securityQuestion"]')
        self.security_question_options = page.locator("mat-option")
        self.security_answer = page.locator("#securityAnswerControl")
        self.submit_button = page.locator("#registerButton")

    def open(self) -> None:
        self._page.goto("/#/register")

    def select_first_security_question(self) -> None:
        first_option = self.security_question_options.first
        click_until_visible(self.security_question, first_option)
        first_option.click()

    def register(self, user: User) -> None:
        self.email.fill(user.email)
        self.password.fill(user.password)
        self.repeat_password.fill(user.password)
        self.select_first_security_question()
        self.security_answer.fill(user.security_answer)
        self.submit_button.click()
