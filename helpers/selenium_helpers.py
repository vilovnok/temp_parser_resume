"""Centralized Selenium helper utilities with logging and highlighting."""
from __future__ import annotations

import logging
import os
from typing import Iterable, List, Optional, Sequence, Tuple

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

Locator = Tuple[str, str]

_LOGGER_NAME = "hh_scraper.selenium"
logger = logging.getLogger(_LOGGER_NAME)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    force=True,
)

logger.setLevel(logging.INFO)

DEFAULT_TIMEOUT: float = float(os.getenv("WAIT_TIMEOUT", "10"))
_DEBUG_UI = os.getenv("DEBUG_UI", "0").lower() in {"1", "true", "yes", "on"}


def describe_locator(locator: Locator) -> str:
    by, value = locator
    return f"{by} -> {value}"


def _resolve_timeout(timeout: Optional[float]) -> float:
    return DEFAULT_TIMEOUT if timeout is None else float(timeout)


def _highlight(element: WebElement) -> WebElement:
    if not _DEBUG_UI or element is None:
        return element

    try:
        element._parent.execute_script(  # type: ignore[attr-defined]
            "arguments[0].style.outline='2px solid #ff00ff';"
            "arguments[0].style.boxShadow='0 0 6px rgba(255,0,255,0.6)';",
            element,
        )
    except Exception as exc:  # pragma: no cover - best effort only
        logger.debug("Failed to highlight element: %s", exc)

    return element


def highlight(elements: Optional[Sequence[WebElement] | WebElement]) -> None:
    if isinstance(elements, WebElement):
        _highlight(elements)
    elif elements:
        for element in elements:
            _highlight(element)


def create_wait(driver: WebDriver, timeout: Optional[float] = None) -> WebDriverWait:
    return WebDriverWait(driver, _resolve_timeout(timeout))


def wait_present(
    driver: WebDriver,
    locator: Locator,
    *,
    label: Optional[str] = None,
    timeout: Optional[float] = None,
) -> WebElement:
    description = label or describe_locator(locator)
    logger.info("Waiting for presence of %s", description)
    element = create_wait(driver, timeout).until(EC.presence_of_element_located(locator))
    return _highlight(element)


def wait_visible(
    driver: WebDriver,
    locator: Locator,
    *,
    label: Optional[str] = None,
    timeout: Optional[float] = None,
) -> WebElement:
    description = label or describe_locator(locator)
    logger.info("Waiting for visibility of %s", description)
    element = create_wait(driver, timeout).until(EC.visibility_of_element_located(locator))
    return _highlight(element)


def wait_clickable(
    driver: WebDriver,
    locator: Locator,
    *,
    label: Optional[str] = None,
    timeout: Optional[float] = None,
) -> WebElement:
    description = label or describe_locator(locator)
    logger.info("Waiting for clickable %s", description)
    element = create_wait(driver, timeout).until(EC.element_to_be_clickable(locator))
    return _highlight(element)


def wait_gone(
    driver: WebDriver,
    locator: Locator,
    *,
    label: Optional[str] = None,
    timeout: Optional[float] = None,
) -> bool:
    description = label or describe_locator(locator)
    logger.info("Waiting for %s to disappear", description)
    return create_wait(driver, timeout).until(EC.invisibility_of_element_located(locator))


def find_one(
    driver: WebDriver,
    locator: Locator,
    *,
    label: Optional[str] = None,
    timeout: Optional[float] = None,
) -> WebElement:
    return wait_present(driver, locator, label=label, timeout=timeout)


def find_all(
    driver: WebDriver,
    locator: Locator,
    *,
    label: Optional[str] = None,
    timeout: Optional[float] = None,
    require: bool = False,
) -> List[WebElement]:
    description = label or describe_locator(locator)
    logger.info("Finding all elements for %s", description)
    wait = create_wait(driver, timeout)

    def _locate(drv: WebDriver) -> List[WebElement] | bool:
        elements = drv.find_elements(*locator)
        if not elements and require:
            return False
        return elements

    try:
        result = wait.until(_locate)
    except TimeoutException:
        if require:
            raise
        logger.info("No elements located for %s", description)
        return []

    elements_list: Iterable[WebElement]
    if isinstance(result, list):
        elements_list = result
    else:  # EC may return bool False when require=True fails earlier
        elements_list = []

    highlighted: List[WebElement] = []
    for element in elements_list:
        highlighted.append(_highlight(element))
    return highlighted


__all__ = [
    "DEFAULT_TIMEOUT",
    "create_wait",
    "describe_locator",
    "find_all",
    "find_one",
    "highlight",
    "logger",
    "wait_clickable",
    "wait_gone",
    "wait_present",
    "wait_visible",
]
