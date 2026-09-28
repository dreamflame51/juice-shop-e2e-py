import time

from playwright.sync_api import Locator
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


def click_until_visible(
    trigger: Locator, target: Locator, *, timeout: float = 10_000, interval: float = 1_000
) -> None:
    """Clicks `trigger` until `target` becomes visible.

    Angular Material occasionally swallows the first click on a control that has
    rendered but is not yet wired up. Retrying the click is deterministic; a
    fixed sleep before it would not be.
    """
    deadline = time.monotonic() + timeout / 1000
    while True:
        trigger.click()
        try:
            target.wait_for(state="visible", timeout=interval)
            return
        # Deliberately narrower than the TS version (flagged issue #6): only a timeout is
        # retried; a real error (bad selector, detached element) fails immediately.
        except PlaywrightTimeoutError:
            if time.monotonic() >= deadline:
                raise
