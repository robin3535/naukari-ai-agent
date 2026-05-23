
from abc import ABC, abstractmethod

from playwright.sync_api import Page


class BaseLogin(ABC):
    """
    Abstract login contract.

    Every website-specific login strategy
    must implement this interface.
    """

    @abstractmethod
    def login(
        self,
        page: Page,
        username: str,
        password: str
    ) -> None:
        pass