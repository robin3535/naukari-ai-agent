
import os
import sys

from dotenv import load_dotenv

from ai.headline_generator import generate_headline_from_env
from auth.auth_manager import AuthManager
from auth.naukri_login import NaukriLogin
from browser.playwright_manager import BrowserManager
from app_logging.logger_config import setup_logger
from tools.profile_headline_tool import (
    ProfileHeadlineTool
)


load_dotenv()

logger = setup_logger()


def should_run_headless() -> bool:
    value = os.getenv("HEADLESS", "true").strip().lower()
    return value not in {"0", "false", "no"}


def get_headline_input() -> str | None:
    """
    Returns fallback headline text from env.
    """

    value = os.getenv("NAUKRI_HEADLINE")
    if value and value.strip():
        logger.info("Using fallback headline from NAUKRI_HEADLINE")
        return value.strip()

    return None


def log_runtime_config() -> None:
    logger.info(
        "Runtime config: "
        f"OPENAI_API_KEY={bool(os.getenv('OPENAI_API_KEY'))}, "
        f"GEMINI_API_KEY={bool(os.getenv('GEMINI_API_KEY'))}, "
        f"NAUKRI_HEADLINE={bool(os.getenv('NAUKRI_HEADLINE'))}, "
        f"HEADLESS={should_run_headless()}"
    )


def is_logged_in(page) -> bool:
    """
    Basic authentication validation.

    This will be improved later using
    dashboard/profile selectors.
    """

    return (
        "nlogin/login" not in page.url
        and "login" not in page.url
    )


def main() -> None:

    logger.info("Starting Naukri agent")
    log_runtime_config()

    browser_manager = None

    try:
        browser_manager = BrowserManager(
            headless=should_run_headless()
        )

        page = browser_manager.page

        headline_tool = ProfileHeadlineTool()

        logger.info(
            "Checking authenticated profile access"
        )

        has_profile_access = headline_tool.open_profile(
            page
        )

        if has_profile_access and is_logged_in(page):

            logger.info(
                "Existing authenticated session found"
            )

        else:

            logger.info(
                "No active session found, attempting login"
            )

            username = os.getenv(
                "NAUKRI_EMAIL"
            )

            password = os.getenv(
                "NAUKRI_PASSWORD"
            )

            if not username or not password:
                raise ValueError(
                    "Naukri credentials missing in .env"
                )

            logger.info("Attempting login with configured username")

            auth_manager = AuthManager(
                strategy=NaukriLogin()
            )

            auth_manager.authenticate(
                page=page,
                username=username,
                password=password
            )

            logger.info(
                "Login completed, saving authenticated session"
            )

            browser_manager.save_session()

            has_profile_access = headline_tool.open_profile(
                page
            )

            if not has_profile_access:
                raise ValueError(
                    "Login finished, but profile page is still not accessible"
                )

        logger.info(
            "Login automation completed successfully"
        )

        generated_headline = generate_headline_from_env()
        headline = generated_headline or get_headline_input()

        if not headline:
            raise ValueError(
                "No headline source configured. Set GEMINI_API_KEY for AI generation "
                "or set NAUKRI_HEADLINE as fallback in Railway Variables."
            )

        headline_success = headline_tool.update_headline(
            page=page,
            headline=headline
        )

        if headline_success:
            logger.info("Headline update succeeded")
        else:
            logger.error("Headline update failed")
            raise RuntimeError("Headline update failed")

        page.wait_for_timeout(5000)

    except Exception as error:

        logger.exception(
            f"Application failed: {error}"
        )
        sys.exit(1)

    finally:

        logger.info("Closing browser")

        if browser_manager:
            browser_manager.close()


if __name__ == "__main__":
    main()
