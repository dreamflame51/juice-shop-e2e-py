import re

import allure
import pytest
from playwright.sync_api import Page, expect

from juice_shop_e2e.data.factories import User, build_user
from juice_shop_e2e.pages.login_page import LoginPage

pytestmark = [allure.epic("UI: Authentication")]


@pytest.mark.smoke
@allure.label("category", "Functional")
def test_a_registered_user_can_log_in(
    page: Page, login_page: LoginPage, registered_user: User
) -> None:
    with allure.step("open the login page"):
        login_page.open()
    with allure.step("submit valid credentials"):
        login_page.login(registered_user.email, registered_user.password)

    expect(page).to_have_url(re.compile(r"#/search"))
    # Flagged TS issue #4: inline locator in a spec, kept as in the TS source.
    expect(page.locator("#navbarAccount")).to_be_visible()


@allure.label("category", "Security")
def test_rejects_invalid_credentials_without_revealing_whether_the_account_exists(
    login_page: LoginPage, registered_user: User
) -> None:
    with allure.step("wrong password for a registered account"):
        login_page.open()
        login_page.login(registered_user.email, "definitely-not-the-password")
        expect(login_page.error_message).to_have_text(
            re.compile(r"invalid email or password", re.IGNORECASE)
        )

    with allure.step("an account that was never registered"):
        unregistered = build_user()
        login_page.open()
        login_page.login(unregistered.email, unregistered.password)
        expect(login_page.error_message).to_have_text(
            re.compile(r"invalid email or password", re.IGNORECASE)
        )
