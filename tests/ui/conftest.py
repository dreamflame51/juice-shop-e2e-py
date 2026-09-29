import json

import pytest
from playwright.sync_api import BrowserContext, Page

from juice_shop_e2e.api.models import AuthSession
from juice_shop_e2e.pages.basket_page import BasketPage
from juice_shop_e2e.pages.login_page import LoginPage
from juice_shop_e2e.pages.products_page import ProductsPage
from juice_shop_e2e.pages.registration_page import RegistrationPage


@pytest.fixture
def context(context: BrowserContext, base_url: str) -> BrowserContext:
    """Dismisses Juice Shop's welcome banner and cookie notice, forces the English UI."""
    context.add_cookies(
        [
            {"name": "cookieconsent_status", "value": "dismiss", "url": base_url},
            {"name": "welcomebanner_status", "value": "dismiss", "url": base_url},
            {"name": "language", "value": "en", "url": base_url},
        ]
    )
    context.add_init_script(
        """
        window.localStorage.setItem('welcomebanner_status', 'dismiss');
        window.localStorage.setItem('cookieconsent_status', 'dismiss');
        """
    )
    return context


@pytest.fixture
def products_page(page: Page) -> ProductsPage:
    return ProductsPage(page)


@pytest.fixture
def login_page(page: Page) -> LoginPage:
    return LoginPage(page)


@pytest.fixture
def registration_page(page: Page) -> RegistrationPage:
    return RegistrationPage(page)


@pytest.fixture
def authed_page(page: Page, context: BrowserContext, session: AuthSession, base_url: str) -> Page:
    """Browser page already authenticated as `registered_user` (no UI login)."""
    context.add_cookies([{"name": "token", "value": session.token, "url": base_url}])
    context.add_init_script(
        f"""
        window.localStorage.setItem('token', {json.dumps(session.token)});
        window.sessionStorage.setItem('bid', {json.dumps(str(session.basket_id))});
        """
    )
    page.goto("/")
    return page


@pytest.fixture
def basket_page(page: Page) -> BasketPage:
    return BasketPage(page)
