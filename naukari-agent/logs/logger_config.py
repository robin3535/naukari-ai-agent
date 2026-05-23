import logging
from pathlib import Path


# Ensure logs directory exists
Path("logs").mkdir(exist_ok=True)


def setup_logger() -> logging.Logger:
    """
    Creates application-wide logger.

    Why centralized logger?
    - Consistent formatting
    - Reusable across modules
    - Easy future integration with cloud logging
    """

    logger = logging.getLogger("naukri_agent")

    # Prevent duplicate handlers during reloads/tests
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    # Persist logs for debugging/history
    file_handler = logging.FileHandler("logs/app.log")

    file_handler.setFormatter(formatter)

    # Console logs help during local development
    console_handler = logging.StreamHandler()

    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger