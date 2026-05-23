from playwright.sync_api import Page

from auth.base_login import BaseLogin


class AuthManager:
    """
    Handles authentication using injected strategy.
    """

    def __init__(
        self,
        strategy: BaseLogin
    ):

        self.strategy = strategy

    def authenticate(
        self,
        page: Page,
        username: str,
        password: str
    ) -> None:

        self.strategy.login(
            page,
            username,
            password
        )