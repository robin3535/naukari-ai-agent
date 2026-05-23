
from pathlib import Path

from playwright.sync_api import (
    sync_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright
)


class BrowserManager:
    """
    Handles Playwright browser lifecycle.

    Uses storage_state session persistence.
    """

    SESSION_FILE = "storage/session.json"

    def __init__(
        self,
        headless: bool = True
    ):

        Path("storage").mkdir(
            exist_ok=True
        )

        self.playwright: Playwright = (
            sync_playwright().start()
        )

        self.browser: Browser = (
            self.playwright.chromium.launch(
                headless=headless,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu"
                ]
            )
        )

        # Restore session if exists
        if Path(
            self.SESSION_FILE
        ).exists():

            self.context: BrowserContext = (
                self.browser.new_context(
                    storage_state=self.SESSION_FILE
                )
            )

        else:

            self.context: BrowserContext = (
                self.browser.new_context()
            )

        self.page: Page = (
            self.context.new_page()
        )

    def save_session(self) -> None:
        """
        Saves authenticated session.
        """

        self.context.storage_state(
            path=self.SESSION_FILE
        )

    def close(self) -> None:

        self.context.close()

        self.browser.close()

        self.playwright.stop()
