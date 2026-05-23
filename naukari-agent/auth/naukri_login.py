import re

from playwright.sync_api import Page

from auth.base_login import BaseLogin
from logs.logger_config import setup_logger


logger = setup_logger()


class NaukriLogin(BaseLogin):

    LOGIN_URL = "https://www.naukri.com/nlogin/login"

    def login(
        self,
        page: Page,
        username: str,
        password: str
    ) -> None:
        """
        Handles Naukri authentication flow.
        """

        try:

            logger.info("Opening Naukri login page")

            page.goto(
                self.LOGIN_URL,
                wait_until="domcontentloaded"
            )

            page.wait_for_load_state(
                "domcontentloaded"
            )

            logger.info(f"Current URL: {page.url}")

            # Wait for domcontentloaded (more lenient than networkidle for pages with continuous network activity)
            page.wait_for_load_state("domcontentloaded", timeout=10000)

            logger.info("Page loaded, taking screenshot for debugging")

            # Useful for debugging UI changes/CAPTCHA
            page.screenshot(
                path="screenshots/naukri_login_page.png"
            )

            logger.info("Waiting for username input")

            username_input = None
            selectors = [
                'input[placeholder*="Enter Email ID / Username"]',
                'input[placeholder*="Email ID"]',
                'input[placeholder*="Username"]',
                'input[name="email"]',
                'input[id*="usernameField"]',
            ]
            
            for selector in selectors:
                try:
                    locator = page.locator(selector)
                    locator.wait_for(timeout=2000)
                    logger.info(f"Found username input with selector: {selector}")
                    username_input = locator.first
                    break
                except Exception as e:
                    logger.debug(f"Selector {selector} not found: {e}")
                    continue
            
            if not username_input:
                raise ValueError("Could not find username input field")

            logger.info("Entering username")

            username_input.fill(username)

            logger.info("Waiting for password input")

            password_input = page.locator(
                'input[type="password"]'
            )

            password_input.wait_for()

            logger.info("Entering password")

            password_input.fill(password)

            # Small delay to ensure form is ready
            page.wait_for_timeout(500)

            logger.info("Submitting login form")

            submit_button = page.get_by_role(
                "button",
                name=re.compile(r"^login$", re.IGNORECASE)
            )

            try:
                submit_button.wait_for(timeout=5000)
            except Exception:
                submit_button = page.locator(
                    'button[type="submit"], button.blue-btn'
                ).first
                submit_button.wait_for(timeout=5000)

            submit_button.click()

            try:
                page.wait_for_url(
                    lambda url: "nlogin/login" not in str(url),
                    timeout=20000
                )
            except Exception:
                page.screenshot(
                    path="screenshots/naukri_login_still_on_login.png"
                )
                raise ValueError(
                    "Login did not leave the login page. Check credentials, CAPTCHA, or OTP requirement."
                )

            logger.info(
                "Naukri login completed successfully"
            )

        except Exception as error:

            logger.exception(
                f"Naukri login failed: {error}"
            )

            page.screenshot(
                path="screenshots/naukri_login_failure.png"
            )

            raise
