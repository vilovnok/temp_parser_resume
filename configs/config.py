import os

from dotenv import load_dotenv
from selenium.webdriver import ActionChains
from selenium.webdriver.support.wait import WebDriverWait

from drivers.set_driver import set_driver

load_dotenv()


class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.counter = 0
            cls._instance.wait_time = float(os.getenv("WAIT_TIMEOUT", "10"))
            cls._instance.login_url = "https://hh.ru/account/login"
            cls._instance.base_page = "https://hh.ru"
            cls._instance.driver_type = os.getenv("DRIVER", "chrome").lower()
            cls._instance.driver = set_driver(cls._instance.driver_type)
            cls._instance.action = ActionChains(cls._instance.driver)
            cls._instance.wait = WebDriverWait(cls._instance.driver, cls._instance.wait_time)
            raw_queries = os.getenv("SEARCH_QUERY", "")
            cls._instance.search_queries = [
                query.strip()
                for query in raw_queries.split(",")
                if query.strip()
            ]
            cls._instance.search_query = (
                cls._instance.search_queries[0] if cls._instance.search_queries else ""
            )
            cls._instance.limit = int(os.getenv("LIMIT", "0") or 0)
            cls._instance.resume_limit = int(os.getenv("RESUME_LIMIT", "500") or 500)
            cls._instance.existing_record_threshold = int(
                os.getenv("EXISTING_RECORD_LIMIT", "1500") or 1500
            )
            cls._instance.resume_records = []
            cls._instance.output_path = os.getenv("OUTPUT_PATH", "data/resumes.csv")
            resume_search_url = os.getenv("RESUME_SEARCH_URL")
            if resume_search_url:
                cls._instance.resume_search_url = resume_search_url
            else:
                base = cls._instance.base_page.rstrip("/")
                cls._instance.resume_search_url = f"{base}/search/resume"

        return cls._instance

    def increment_counter(self):
        self.counter += 1


config = Config()
