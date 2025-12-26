from typing import Iterable

from selenium.webdriver.remote.webelement import WebElement

from configs.config import config
from pages.resumes.search_page import ResumeSearchPage


def find_resumes(search_page: ResumeSearchPage | None = None) -> Iterable[WebElement]:
    page = search_page or ResumeSearchPage(config.driver)
    return page.get_resume_cards()
