"""Page object for the resume search results."""
from __future__ import annotations

from typing import Iterable, List, Optional

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from helpers.selenium_helpers import (
    find_all,
    highlight,
    logger,
    wait_clickable,
    wait_present,
)
from pages.base_page import BasePage


class ResumeSearchPage(BasePage):
    """Represents the resume search SERP on hh.ru."""

    SEARCH_INPUT = (By.XPATH, '//input[@id="a11y-search-input"]')
    SEARCH_BUTTON = (By.XPATH, '//button[@data-qa="search-button"]')
    RESUME_CARDS = (
        By.XPATH,
        '//div[contains(@data-qa, "resume-serp__resume") and @data-resume-id]'
    )
    RESUME_TITLE = (By.XPATH, './/a[@data-qa="serp-item__title"]')
    NEXT_BUTTON = (By.XPATH, '//a[@data-qa="pager-next"]')

    def wait_until_ready(self) -> "ResumeSearchPage":
        wait_clickable(self.driver, self.SEARCH_INPUT, label="Resume search input", timeout=self.timeout)
        return self

    def prepare_search(self, query: str) -> "ResumeSearchPage":
        self.wait_until_ready()
        normalized = (query or "").strip()
        self.type(self.SEARCH_INPUT, normalized, label="Resume search input")
        self.submit_search()
        return self

    def submit_search(self) -> None:
        self.click(self.SEARCH_BUTTON, label="Search button")
        self.wait_for_results()

    def wait_for_results(self) -> None:
        wait_present(self.driver, self.RESUME_CARDS, label="Resume search results", timeout=self.timeout)

    def get_resume_cards(self, *, require: bool = True) -> List[WebElement]:
        cards = find_all(
            self.driver,
            self.RESUME_CARDS,
            label="Resume cards",
            timeout=self.timeout,
            require=require,
        )
        highlight(cards)
        return cards

    def extract_resume_links(self, cards: Optional[Iterable[WebElement]] = None) -> List[str]:
        cards = list(cards or self.get_resume_cards())
        links: List[str] = []

        for card in cards:
            try:
                link_element = card.find_element(*self.RESUME_TITLE)
            except NoSuchElementException:
                logger.info("Card without a title link was skipped")
                continue

            highlight(link_element)
            href = link_element.get_attribute("href")
            if href:
                links.append(href)

        return links

    def go_to_next_page(self) -> bool:
        try:
            next_button = wait_clickable(
                self.driver,
                self.NEXT_BUTTON,
                label="Next page button",
                timeout=self.timeout,
            )
        except TimeoutException:
            logger.info("Next page button not available; stopping pagination")
            return False

        classes = (next_button.get_attribute("class") or "").lower()
        if "disabled" in classes:
            logger.info("Reached the final page of search results")
            return False

        current_url = self.current_url
        logger.info("Navigating to the next page of resumes")
        next_button.click()

        if not self.wait_for_url_change(current_url, timeout=self.timeout):
            if self.current_url == current_url:
                logger.info("Pagination did not change the page URL; stopping")
                return False

        self.wait_for_results()
        return True
