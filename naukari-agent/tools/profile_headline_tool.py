from pathlib import Path

from playwright.sync_api import Page, TimeoutError

from app_logging.logger_config import setup_logger


logger = setup_logger()
Path("screenshots").mkdir(exist_ok=True)


class ProfileHeadlineTool:
    """
    Opens the Naukri profile and updates the resume headline.
    """

    PROFILE_URL = "https://www.naukri.com/mnjuser/profile"
    MAX_HEADLINE_LENGTH = 256

    def open_profile(
        self,
        page: Page
    ) -> bool:
        """Load profile page."""
        logger.info("Opening profile page")

        page.goto(
            self.PROFILE_URL,
            wait_until="networkidle"
        )

        page.wait_for_timeout(1000)
        logger.info(f"Profile page URL: {page.url}")

        page.screenshot(
            path="screenshots/profile_page.png"
        )

        if "nlogin/login" in page.url or "login" in page.url:
            logger.info("Profile page redirected to login")
            return False

        return True

    def update_headline(
        self,
        page: Page,
        headline: str | None = None
    ) -> bool:
        """Update resume headline with provided text."""
        try:
            if not self.open_profile(page):
                logger.error("Not logged in")
                return False

            headline = headline.strip() if headline else self._get_current_headline(page)
            if not headline:
                raise TimeoutError("Could not read headline")

            # Find and click edit button
            edit_btn = page.locator("#lazyResumeHead .widgetHead .edit.icon")
            edit_btn.wait_for(timeout=5000)
            edit_btn.click(force=True)
            page.wait_for_timeout(300)

            # Wait for dialog
            dialog = page.locator(".lightbox:visible")
            dialog.wait_for(timeout=3000)

            # Find input and set value
            text_area = dialog.locator("textarea:visible")
            text_area.wait_for(timeout=2000)
            
            formatted_headline = self._format_headline(headline)
            text_area.fill(formatted_headline)
            page.wait_for_timeout(200)

            # Find and click save
            save_btn = dialog.locator('button:has-text("Save"):visible')
            save_btn.wait_for(timeout=2000)
            save_btn.click()
            page.wait_for_timeout(1500)

            page.screenshot(
                path="screenshots/headline_update_success.png"
            )

            logger.info("Headline updated successfully")
            return True

        except TimeoutError as error:
            logger.error(f"Element not found: {error}")
            page.screenshot(
                path="screenshots/headline_update_failure.png"
            )
            return False

        except Exception as error:
            logger.exception(f"Update failed: {error}")
            page.screenshot(
                path="screenshots/headline_update_failure.png"
            )
            return False

    def _get_current_headline(
        self,
        page: Page
    ) -> str | None:
        """Read current headline from profile."""
        try:
            locator = page.locator("#lazyResumeHead .widgetCont .prefill div")
            locator.wait_for(timeout=3000)
            headline = locator.inner_text().strip()
            if headline:
                logger.info("Current headline read from profile")
                return headline
        except Exception as error:
            logger.error(f"Cannot read headline: {error}")

        return None

    def _format_headline(
        self,
        headline: str
    ) -> str:
        """Format and validate headline."""
        headline = headline.strip()

        # Ensure ends with punctuation
        if not headline.endswith((".", "!", "?")):
            headline = f"{headline}."

        # Trim if too long
        if len(headline) > self.MAX_HEADLINE_LENGTH:
            headline = headline[:self.MAX_HEADLINE_LENGTH].rstrip()
            if not headline.endswith((".", "!", "?")):
                headline = f"{headline}."

        return headline
