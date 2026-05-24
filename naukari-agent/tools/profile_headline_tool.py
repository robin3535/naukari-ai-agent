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

    def open_profile(
        self,
        page: Page
    ) -> bool:
        logger.info("Opening profile page")

        page.goto(
            self.PROFILE_URL,
            wait_until="domcontentloaded"
        )

        page.wait_for_load_state(
            "domcontentloaded",
            timeout=10000
        )

        page.wait_for_timeout(2000)
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
        try:
            if not self.open_profile(page):
                logger.error("Cannot update headline because user is not logged in")
                return False

            headline = headline.strip() if headline else self._get_current_headline(page)
            if not headline:
                raise TimeoutError("Could not read headline text")

            edit_control = self._find_headline_edit_control(page)
            if not edit_control:
                raise TimeoutError("Could not find headline edit control")

            edit_control.click(force=True)

            dialog = self._wait_for_headline_dialog(page)
            if not dialog:
                raise TimeoutError("Headline edit dialog did not open")

            headline_input = self._find_headline_input(dialog)
            if not headline_input:
                raise TimeoutError("Could not find headline input")

            self._set_headline_value(
                page=page,
                locator=headline_input,
                value=self._ensure_terminal_punctuation(headline)
            )

            save_button = self._find_dialog_save_button(dialog)
            if not save_button:
                raise TimeoutError("Could not find headline dialog save button")

            save_button.click()
            page.wait_for_timeout(3000)
            page.screenshot(
                path="screenshots/headline_update_success.png"
            )

            logger.info("Headline update completed")
            return True

        except TimeoutError as error:
            logger.error(f"Headline update control not found: {error}")
            page.screenshot(
                path="screenshots/headline_update_timeout.png"
            )
            return False

        except Exception as error:
            logger.exception(f"Headline update failed: {error}")
            page.screenshot(
                path="screenshots/headline_update_failure.png"
            )
            return False

    def _find_headline_edit_control(
        self,
        page: Page
    ):
        selectors = [
            '.widgetHead:has-text("Resume headline") .edit.icon',
            '.widgetHead:has-text("Resume headline") .edit',
            '.widgetHead:has-text("Profile headline") .edit.icon',
            '.widgetHead:has-text("Profile headline") .edit',
        ]

        for selector in selectors:
            try:
                locator = page.locator(selector).first
                locator.wait_for(timeout=3000)
                logger.info(f"Found headline edit control with selector: {selector}")
                return locator
            except Exception as error:
                logger.debug(f"Headline edit selector failed: {selector} | {error}")

        return None

    def _get_current_headline(
        self,
        page: Page
    ) -> str | None:
        selectors = [
            '.widgetHead:has-text("Resume headline") + .widgetCont .prefill div',
            '.widgetHead:has-text("Resume headline") + .widgetCont .prefill',
            '.widgetHead:has-text("Profile headline") + .widgetCont .prefill div',
            '.widgetHead:has-text("Profile headline") + .widgetCont .prefill',
        ]

        for selector in selectors:
            try:
                locator = page.locator(selector).first
                locator.wait_for(timeout=3000)
                headline = locator.inner_text().strip()
                if headline:
                    logger.info("Using current headline from profile page")
                    return headline
            except Exception as error:
                logger.debug(f"Current headline selector failed: {selector} | {error}")

        return None

    def _wait_for_headline_dialog(
        self,
        page: Page
    ):
        selectors = [
            '[role="dialog"]:visible',
            '.modal:visible',
            '.lightbox:visible',
            '.popup:visible',
            'form:has-text("Resume headline"):visible',
            'div:has-text("Resume headline"):has(textarea):visible',
        ]

        for selector in selectors:
            try:
                locator = page.locator(selector).last
                locator.wait_for(timeout=5000)
                logger.info(f"Found headline dialog with selector: {selector}")
                page.screenshot(path="screenshots/headline_dialog_open.png")
                return locator
            except Exception as error:
                logger.debug(f"Headline dialog selector failed: {selector} | {error}")

        return None

    def _find_headline_input(
        self,
        dialog
    ):
        selectors = [
            'textarea[name*="headline" i]:visible',
            'textarea[id*="headline" i]:visible',
            'textarea[placeholder*="headline" i]:visible',
            'textarea:visible',
            'input[name*="headline" i]:visible',
            'input[id*="headline" i]:visible',
            'input[type="text"]:visible',
            '[contenteditable="true"]:visible',
        ]

        for selector in selectors:
            try:
                locator = dialog.locator(selector).first
                locator.wait_for(timeout=3000)
                logger.info(f"Found headline input with selector: {selector}")
                return locator
            except Exception as error:
                logger.debug(f"Headline input selector failed: {selector} | {error}")

        return None

    def _set_headline_value(
        self,
        page: Page,
        locator,
        value: str
    ) -> None:
        locator.click(force=True)
        locator.fill(value)
        locator.evaluate(
            """
            (element, value) => {
                if ("value" in element) {
                    element.value = value;
                } else {
                    element.textContent = value;
                }
                element.dispatchEvent(new Event("input", { bubbles: true }));
                element.dispatchEvent(new Event("change", { bubbles: true }));
            }
            """,
            value
        )
        page.wait_for_timeout(500)

    def _find_dialog_save_button(
        self,
        dialog
    ):
        selectors = [
            'button:has-text("Save"):visible',
            'input[type="submit"][value*="Save" i]:visible',
            '[role="button"]:has-text("Save"):visible',
        ]

        for selector in selectors:
            try:
                locator = dialog.locator(selector).first
                locator.wait_for(timeout=3000)
                logger.info(f"Found headline save button with selector: {selector}")
                return locator
            except Exception as error:
                logger.debug(f"Headline save selector failed: {selector} | {error}")

        return None

    def _ensure_terminal_punctuation(
        self,
        headline: str
    ) -> str:
        headline = headline.strip()

        if headline.endswith((".", "!", "?")):
            return headline

        return f"{headline}."
