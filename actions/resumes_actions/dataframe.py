from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableSet

import pandas as pd


def _read_csv_with_fallback(path: Path, **kwargs: Any) -> pd.DataFrame:
    try:
        return pd.read_csv(path, **kwargs)
    except pd.errors.ParserError:
        return pd.read_csv(path, engine="python", on_bad_lines="skip", **kwargs)


def _normalize_value(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return value


def _normalize_record(record: Mapping[str, Any]) -> dict:
    return {key: _normalize_value(value) for key, value in record.items()}


def build_dataframe(records: Iterable[Mapping[str, Any]] | None) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()

    normalized = [_normalize_record(record) for record in records]
    return pd.DataFrame(normalized)


def save_dataframe(dataframe: pd.DataFrame, output_path: str) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output, index=False)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^\w]+", "_", value.strip().lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "all"


def query_output_path(base_path: str, query: str) -> Path:
    output = Path(base_path)
    slug = _slugify(query)
    return output.with_name(f"{output.stem}_{slug}{output.suffix}")


def load_existing_ids(path: str) -> MutableSet[str]:
    output = Path(path)
    if not output.exists():
        return set()

    try:
        dataframe = _read_csv_with_fallback(output)
    except pd.errors.EmptyDataError:
        return set()

    if "resume_id" not in dataframe.columns:
        return set()

    ids = dataframe["resume_id"].dropna().astype(str)
    return set(ids)


def append_record(
    record: Mapping[str, Any], *, path: str, known_ids: MutableSet[str]
) -> bool:
    resume_id = str(record.get("resume_id", "")).strip()
    if resume_id and resume_id in known_ids:
        return False

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    normalized = _normalize_record(record)

    existing_columns: list[str] = []
    if output.exists():
        try:
            header = _read_csv_with_fallback(output, nrows=0)
        except pd.errors.EmptyDataError:
            header = pd.DataFrame()
        existing_columns = list(header.columns)

    normalized_keys = list(normalized.keys())
    if existing_columns:
        new_columns = [column for column in normalized_keys if column not in existing_columns]
        columns = [*existing_columns, *new_columns]

        if new_columns:
            try:
                existing_dataframe = _read_csv_with_fallback(output)
            except pd.errors.EmptyDataError:
                existing_dataframe = pd.DataFrame(columns=existing_columns)

            existing_dataframe = existing_dataframe.reindex(columns=columns)
            existing_dataframe = existing_dataframe.fillna("")
            existing_dataframe.to_csv(output, index=False)
    else:
        columns = normalized_keys

    dataframe = pd.DataFrame([normalized]).reindex(columns=columns)
    dataframe = dataframe.fillna("")
    write_header = not output.exists() or not existing_columns
    dataframe.to_csv(output, mode="a", header=write_header, index=False)

    if resume_id:
        known_ids.add(resume_id)

    return True


def count_records(path: str) -> int:
    output = Path(path)
    if not output.exists():
        return 0

    try:
        dataframe = _read_csv_with_fallback(output)
    except pd.errors.EmptyDataError:
        return 0

    return len(dataframe.index)
