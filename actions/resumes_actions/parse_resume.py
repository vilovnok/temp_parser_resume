from configs.config import config
from pages.resumes.detail_page import ResumeDetailPage


def parse_resume():
    page = ResumeDetailPage(config.driver)
    return page.collect()
