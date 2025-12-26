"""Page object for the resume detail view."""
from __future__ import annotations

import json
import re
from typing import Dict, List
from urllib.parse import urlparse

from selenium.webdriver.common.by import By

from helpers.selenium_helpers import find_all, logger
from pages.base_page import BasePage


class ResumeDetailPage(BasePage):
    """Encapsulates selectors and helpers for resume details."""

    FULL_NAME = (By.XPATH, '//h1[@data-qa="resume-personal-name"]')
    DESIRED_POSITION = (By.XPATH, '//span[@data-qa="resume-block-title-position"]')
    SALARY = (By.XPATH, '//span[@data-qa="resume-block-salary"]')
    AGE = (By.XPATH, '//span[@data-qa="resume-personal-age"]')
    GENDER = (By.XPATH, '//span[@data-qa="resume-personal-gender"]')
    LOCATION = (By.XPATH, '//span[@data-qa="resume-personal-address"]')
    WORK_EXPERIENCE = (By.XPATH, '//div[@data-qa="resume-block-experience"]')
    EDUCATION = (By.XPATH, '//div[@data-qa="resume-block-education"]')
    LANGUAGE_ITEMS = (
        By.XPATH,
        '//li[@data-qa="resume-block-language-item"] | '
        '//span[@data-qa="resume-block-language-item"]',
    )
    KEY_SKILLS = (By.XPATH, '//span[@data-qa="bloko-tag__text"]')
    SKILL_KEYWORDS = (By.XPATH, '//span[@data-qa="skills-table-item"]')
    SELF_DESCRIPTION = (By.XPATH, '//div[@data-qa="resume-block-skills-content"]')
    CITIZENSHIP = (By.XPATH, '//span[@data-qa="resume-personal-citizenship"]')
    READY_TO_RELOCATE = (By.XPATH, '//p[@data-qa="resume-personal-relocation"]')
    TRAVEL_TIME = (By.XPATH, '//span[@data-qa="resume-personal-metro"]')
    UPDATED_AT = (By.XPATH, '//span[@data-qa="resume-updatedAt"]')
    DRIVER_LICENSES = (
        By.XPATH,
        (
            "//*[@data-qa and "
            "contains(translate(@data-qa, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'driver') "
            "and contains(translate(@data-qa, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'licen')]"
        ),
    )
    PERSONAL_DETAILS = (
        By.XPATH,
        '//div[@data-qa="resume-block-personal"]//*[@data-qa]',
    )

    def collect(self) -> dict:
        logger.info("Collecting resume details from %s", self.current_url)
        personal_details = self._collect_personal_details()
        languages = self._collect_languages()
        key_skills = self._collect_key_skills()
        driver_licenses = self._collect_driver_license()

        formatted_languages = [
            formatted
            for formatted in (self._format_language(entry) for entry in languages)
            if formatted
        ]

        return {
            "resume_id": self._extract_resume_id(self.current_url),
            "url": self.current_url,
            "full_name": self.get_optional_text(self.FULL_NAME, label="Full name"),
            "desired_position": self.get_optional_text(
                self.DESIRED_POSITION, label="Desired position"
            ),
            "salary": self.get_optional_text(self.SALARY, label="Salary"),
            "age": self.get_optional_text(self.AGE, label="Age"),
            "gender": self.get_optional_text(self.GENDER, label="Gender"),
            "location": self.get_optional_text(self.LOCATION, label="Location"),
            "work_experience": self.get_optional_text(
                self.WORK_EXPERIENCE, label="Work experience"
            ),
            "education": self.get_optional_text(self.EDUCATION, label="Education"),
            "languages": "; ".join(formatted_languages),
            "languages_detailed": json.dumps(languages, ensure_ascii=False),
            "self_description": self.get_optional_text(
                self.SELF_DESCRIPTION,
                label="Self description",
                timeout=1,
            ),
            "key_skills": "; ".join(key_skills),
            "key_skills_raw": json.dumps(key_skills, ensure_ascii=False),
            "skill_keywords": self._join_texts(self.SKILL_KEYWORDS, label="Skill keywords"),
            "citizenship": self._join_texts(self.CITIZENSHIP, label="Citizenship"),
            "ready_to_relocate": self.get_optional_text(
                self.READY_TO_RELOCATE, label="Relocation readiness"
            ),
            "travel_time": self.get_optional_text(self.TRAVEL_TIME, label="Travel time"),
            "driver_license": "; ".join(driver_licenses),
            "driver_license_raw": json.dumps(driver_licenses, ensure_ascii=False),
            "personal_details": json.dumps(personal_details, ensure_ascii=False),
            "updated_at": self.get_optional_text(self.UPDATED_AT, label="Updated at"),
        }

    def _collect_key_skills(self) -> List[str]:
        elements = find_all(
            self.driver, self.KEY_SKILLS, label="Key skills", timeout=1, require=False
        )
        return self._unique_preserve_order(
            [element.text.strip() for element in elements if element.text.strip()]
        )

    def _collect_languages(self) -> List[Dict[str, str]]:
        elements = find_all(
            self.driver,
            self.LANGUAGE_ITEMS,
            label="Languages",
            timeout=1,
            require=False,
        )
        languages: List[Dict[str, str]] = []

        for element in elements:
            text = element.text.strip()
            if not text:
                continue
            name, level = self._split_language(text)
            if not name:
                continue
            languages.append({"name": name, "level": level})

        return languages

    def _collect_driver_license(self) -> List[str]:
        elements = find_all(
            self.driver,
            self.DRIVER_LICENSES,
            label="Driver license",
            timeout=1,
            require=False,
        )
        return self._unique_preserve_order(
            [element.text.strip() for element in elements if element.text.strip()]
        )

    def _collect_personal_details(self) -> Dict[str, str]:
        elements = find_all(
            self.driver,
            self.PERSONAL_DETAILS,
            label="Personal details",
            timeout=1,
            require=False,
        )
        details: Dict[str, str] = {}

        for element in elements:
            data_qa = (element.get_attribute("data-qa") or "").strip()
            value = element.text.strip()
            if not data_qa or not value:
                continue
            details[data_qa] = value

        return details

    def _join_texts(self, locator, *, label: str, separator: str = ", ") -> str:
        elements = find_all(self.driver, locator, label=label, timeout=1, require=False)
        values = [element.text.strip() for element in elements if element.text.strip()]
        return separator.join(values)

    @staticmethod
    def _extract_resume_id(url: str) -> str:
        parsed = urlparse(url)
        return parsed.path.rstrip("/").split("/")[-1]

    @staticmethod
    def _split_language(value: str) -> tuple[str, str]:
        parts = re.split(r"\s+[—\-–]\s+", value, maxsplit=1)
        name = parts[0].strip()
        level = parts[1].strip() if len(parts) > 1 else ""
        return name, level

    @staticmethod
    def _format_language(entry: Dict[str, str]) -> str:
        name = entry.get("name", "").strip()
        level = entry.get("level", "").strip()
        return f"{name} ({level})" if name and level else name

    @staticmethod
    def _unique_preserve_order(values: List[str]) -> List[str]:
        seen = set()
        ordered: List[str] = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            ordered.append(value)
        return ordered
