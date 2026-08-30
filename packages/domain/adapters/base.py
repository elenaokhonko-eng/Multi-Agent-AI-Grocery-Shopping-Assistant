import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class RetailerAdapter(ABC):
    """
    Abstract interface for retailer adapters (e.g. FairPrice, Little Farms).
    Adapters are responsible for securely scraping account info and executing
    the final browser checkout flow using Playwright.
    """

    def __init__(self, store_name: str, domain: str):
        self.store_name = store_name
        self.domain = domain

    @abstractmethod
    def get_checkout_details(self) -> dict[str, str]:
        """
        Returns a dictionary with 'address' and 'payment_method'.
        This method MUST use the user's saved store cabinet login
        to retrieve this securely, without extracting raw card numbers.
        """

    @abstractmethod
    def checkout(self, items: list[dict[str, Any]]) -> bool:
        """
        Executes the checkout flow up to the final payment confirmation.
        MUST contain a safety stop (demo mode) to prevent actual purchases.
        """
