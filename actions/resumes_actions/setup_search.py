from configs.config import config
from pages.resumes.search_page import ResumeSearchPage


def setup_search(query: str) -> ResumeSearchPage:
    page = ResumeSearchPage(config.driver)
    page.open(config.resume_search_url)
    page.prepare_search(query)
    return page
