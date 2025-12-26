import os

from actions.resumes_actions.click_resumes import click_resumes
from configs.config import config
from helpers.check_bat import is_running_from_batch


def main() -> None:
    """Entry point for collecting resumes."""
    click_resumes()


if __name__ == "__main__":
    if is_running_from_batch():
        os.system("cls")

    try:
        main()
    finally:
        try:
            config.driver.quit()
        except Exception:
            pass
