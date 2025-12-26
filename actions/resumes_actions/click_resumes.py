from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, MutableSet

from actions.resumes_actions.dataframe import (
    append_record,
    count_records,
    load_existing_ids,
    query_output_path,
)
from actions.resumes_actions.find_resumes import find_resumes
from actions.resumes_actions.parse_resume import parse_resume
from actions.resumes_actions.setup_search import setup_search
from configs.config import config
from helpers.selenium_helpers import logger


def _ensure_queries() -> List[str]:
    if getattr(config, "search_queries", None):
        return list(config.search_queries)

    if config.search_query:
        return [config.search_query]

    raise ValueError("SEARCH_QUERY environment variable is required")


def _collect_for_query(query: str, known_general_ids: MutableSet[str]) -> int:
    logger.info("Начинаем сбор резюме по запросу: %s", query)
    search_page = setup_search(query)
    resume_limit = getattr(config, "resume_limit", 0)
    saved_for_query = 0

    per_query_path = query_output_path(config.output_path, query)
    per_query_path_str = str(per_query_path)
    per_query_ids = load_existing_ids(per_query_path_str)

    existing_records = count_records(per_query_path_str)
    threshold = getattr(config, "existing_record_threshold", 1500)
    if existing_records >= threshold:
        logger.info(
            "Пропускаем запрос '%s' — найдено %s записей (порог %s)",
            query,
            existing_records,
            threshold,
        )
        return 0

    while not resume_limit or saved_for_query < resume_limit:
        resumes_list = list(find_resumes(search_page))
        if not resumes_list:
            logger.info("Подходящих резюме не найдено для запроса '%s'", query)
            break

        resume_links = search_page.extract_resume_links(resumes_list)
        if not resume_links:
            logger.info("На странице не найдено ссылок на резюме")
            break

        for link in resume_links:
            if resume_limit and saved_for_query >= resume_limit:
                logger.info("Достигнут лимит сбора резюме: %s", resume_limit)
                break

            logger.info("Открываем резюме в новой вкладке: %s", link)
            config.driver.execute_script("window.open(arguments[0], '_blank');", link)
            config.driver.switch_to.window(config.driver.window_handles[-1])

            try:
                resume_data = parse_resume()
            except Exception as error:  # pragma: no cover - depends on remote site
                logger.exception("Не удалось распарсить резюме: %s", error)
            else:
                append_record(resume_data, path=per_query_path_str, known_ids=per_query_ids)
                was_added = append_record(
                    resume_data,
                    path=config.output_path,
                    known_ids=known_general_ids,
                )
                if was_added:
                    saved_for_query += 1
                    logger.info(
                        "Добавлено резюме (%s) в общий файл", resume_data.get("full_name", "Неизвестно")
                    )
                else:
                    logger.info(
                        "Резюме уже было сохранено ранее: %s",
                        resume_data.get("resume_id") or resume_data.get("url"),
                    )
            finally:
                config.driver.close()
                config.driver.switch_to.window(config.driver.window_handles[0])
        if resume_limit and saved_for_query >= resume_limit:
            logger.info("Достигнут лимит резюме для запроса '%s'", query)
            break

        if not search_page.go_to_next_page():
            break

    logger.info("Итого новых резюме по '%s': %s", query, saved_for_query)
    return saved_for_query


def click_resumes():
    queries = _ensure_queries()
    known_general_ids = load_existing_ids(config.output_path)
    saved_summary: Dict[str, int] = defaultdict(int)

    for query in queries:
        try:
            saved_summary[query] = _collect_for_query(query, known_general_ids)
        except Exception as error:
            logger.exception("Ошибка при обработке запроса '%s': %s", query, error)

    total_new = sum(saved_summary.values())
    print("Результат сбора по запросам:")
    for query, count in saved_summary.items():
        print(f"  - {query}: {count} новых резюме")
    print(f"Итого новых резюме добавлено: {total_new}")
    print(f"Общий файл с результатами: {config.output_path}")
