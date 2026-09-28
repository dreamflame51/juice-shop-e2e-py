import re

import pytest
from playwright.sync_api import Page, expect

from juice_shop_e2e.data.factories import User
from juice_shop_e2e.pages.login_page import LoginPage
from juice_shop_e2e.pages.registration_page import RegistrationPage

# TODO(lesson-10): allure epic "UI: Authentication", category "Functional"


@pytest.mark.smoke
def test_a_new_customer_can_register_and_then_log_in(
    page: Page, registration_page: RegistrationPage, login_page: LoginPage, test_user: User
) -> None:
    # TODO(lesson-10): step 'register a brand new customer'
    registration_page.open()
    registration_page.register(test_user)
    expect(page).to_have_url(re.compile(r"#/login"))
    # TODO(lesson-10): step 'log in with the credentials just registered'
    login_page.login(test_user.email, test_user.password)
    expect(page).to_have_url(re.compile(r"#/search"))


def test_blocks_submission_when_the_repeated_password_does_not_match(
    registration_page: RegistrationPage, test_user: User
) -> None:
    registration_page.open()
    registration_page.email.fill(test_user.email)
    registration_page.password.fill(test_user.password)
    registration_page.repeat_password.fill(f"{test_user.password}-mismatch")
    registration_page.security_answer.click()
    expect(registration_page.submit_button).to_be_disabled()
