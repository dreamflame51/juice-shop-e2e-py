import pytest
from playwright.sync_api import BrowserContext, Page

from juice_shop_e2e.pages.products_page import ProductsPage


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
