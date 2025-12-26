"""Base class for all page objects."""
from __future__ import annotations

import os
from typing import Optional
from urllib.parse import urljoin, urlparse

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

from helpers.selenium_helpers import (
    DEFAULT_TIMEOUT,
    describe_locator,
    logger,
    wait_clickable,
    wait_visible,
)


class BasePage:
    """Shared Selenium page object helpers."""

    base_url: str = os.getenv("BASE_URL", "").rstrip("/")

    def __init__(self, driver: WebDriver, *, timeout: Optional[float] = None) -> None:
        self.driver = driver
        self.timeout = timeout or DEFAULT_TIMEOUT

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------
    def open(self, path: Optional[str] = None) -> "BasePage":
        target = self._resolve_url(path)
        if target:
            logger.info("Opening URL: %s", target)
            self.driver.get(target)
        return self

    @property
    def current_url(self) -> str:
        return self.driver.current_url

    def wait(self, timeout: Optional[float] = None):
        from helpers.selenium_helpers import create_wait

        return create_wait(self.driver, timeout or self.timeout)

    def wait_for_url_change(self, current_url: str, *, timeout: Optional[float] = None) -> bool:
        logger.info("Waiting for URL to change from %s", current_url)
        try:
            self.wait(timeout).until(EC.url_changes(current_url))
            return True
        except TimeoutException:
            return False

    # ------------------------------------------------------------------
    # Element interactions
    # ------------------------------------------------------------------
    def click(self, locator, *, label: Optional[str] = None, timeout: Optional[float] = None):
        description = label or describe_locator(locator)
        element = wait_clickable(self.driver, locator, label=description, timeout=timeout or self.timeout)
        logger.info("Clicking %s", description)
        element.click()
        return element

    def type(
        self,
        locator,
        text: str,
        *,
        label: Optional[str] = None,
        clear: bool = True,
        timeout: Optional[float] = None,
    ):
        description = label or describe_locator(locator)
        element = wait_visible(self.driver, locator, label=description, timeout=timeout or self.timeout)
        logger.info("Typing '%s' into %s", text, description)
        if clear:
            element.clear()
        element.send_keys(text)
        return element

    def get_text(self, locator, *, label: Optional[str] = None, timeout: Optional[float] = None) -> str:
        description = label or describe_locator(locator)
        element = wait_visible(self.driver, locator, label=description, timeout=timeout or self.timeout)
        logger.info("Reading text from %s", description)
        return element.text.strip()

    def get_optional_text(
        self,
        locator,
        *,
        label: Optional[str] = None,
        timeout: Optional[float] = None,
        default: str = "",
    ) -> str:
        try:
            effective_timeout = timeout if timeout is not None else min(self.timeout, 2)
            return self.get_text(locator, label=label, timeout=effective_timeout)
        except TimeoutException:
            logger.info("Optional element %s not found; returning default", label or describe_locator(locator))
            return default

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _resolve_url(self, path: Optional[str]) -> str:
        if not path:
            return self.base_url

        parsed = urlparse(path)
        if parsed.scheme:
            return path

        if not self.base_url:
            return path

        return urljoin(f"{self.base_url}/", path.lstrip("/"))
