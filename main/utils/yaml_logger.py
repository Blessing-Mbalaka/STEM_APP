from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, MutableSequence

from django.conf import settings
from django.utils import timezone

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - fallback when PyYAML is unavailable
    yaml = None  # type: ignore

from .privacy import anonymize_user_label
from .roles import get_primary_role


DATA_DIR = Path(settings.BASE_DIR) / "main" / "data"
FORUM_QUESTIONS_FILE = DATA_DIR / "forum_questions.yaml"
CHATBOT_HISTORY_FILE = DATA_DIR / "chatbot_history.yaml"
RESOURCE_LINKS_FILE = DATA_DIR / "resource_links.yaml"
STUDENT_SEARCHES_FILE = DATA_DIR / "student_searches.yaml"


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_yaml_records(path: Path) -> List[Any]:
    """
    Load records from a YAML file, falling back to JSON if PyYAML is unavailable.
    Returns an empty list when the file is missing or malformed.
    """
    if not path.exists():
        return []

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return []

    if not raw.strip():
        return []

    if yaml is not None:
        try:
            data = yaml.safe_load(raw)  # type: ignore[arg-type]
            if isinstance(data, list):
                return data
        except Exception:
            # Fallback to JSON parsing below
            pass

    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass

    return []


def _write_yaml(path: Path, data: MutableSequence[Any]) -> None:
    """
    Persist data to a YAML file, using JSON as a valid YAML subset when PyYAML
    is not installed.
    """
    _ensure_dir()
    if yaml is not None:
        dumped = yaml.safe_dump(  # type: ignore[func-returns-value]
            data,
            sort_keys=False,
            allow_unicode=False,
        )
        path.write_text(dumped, encoding="utf-8")
    else:  # pragma: no cover - exercised only when PyYAML missing
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def append_yaml_record(path: Path, record: Any, *, max_entries: int | None = None) -> List[Any]:
    """
    Append a record to the YAML file and optionally trim the collection to the
    latest `max_entries`. Returns the updated list of records.
    """
    records = load_yaml_records(path)
    records.append(record)
    if max_entries is not None:
        records = records[-max_entries:]
    _write_yaml(path, records)
    return records


def write_yaml_records(path: Path, records: MutableSequence[Any]) -> None:
    """
    Replace the YAML file with the supplied records.
    """
    _write_yaml(path, records)


def _infer_user_role(user: Any) -> str:
    return get_primary_role(user)


def _sanitize_metadata(metadata: Dict[str, Any] | None) -> Dict[str, Any]:
    if not metadata:
        return {}
    result: Dict[str, Any] = {}
    for key, value in metadata.items():
        if key == "local_resources" and isinstance(value, list):
            trimmed = []
            for item in value[:5]:
                if isinstance(item, dict):
                    trimmed.append(
                        {
                            "title": item.get("title"),
                            "url": item.get("url"),
                        }
                    )
            result[key] = trimmed
        else:
            result[key] = value
    return result


def log_student_search(
    query: str,
    *,
    user: Any = None,
    source: str = "",
    metadata: Dict[str, Any] | None = None,
) -> None:
    """
    Persist an anonymised record of a learner search event for analytics.
    """
    cleaned = (query or "").strip()
    if not cleaned:
        return

    record: Dict[str, Any] = {
        "query": cleaned[:300],
        "timestamp": timezone.now().isoformat(),
        "source": source or "unspecified",
        "actor": {
            "label": anonymize_user_label(user),
            "role": _infer_user_role(user),
        },
    }

    meta = _sanitize_metadata(metadata)
    if meta:
        record["metadata"] = meta

    append_yaml_record(STUDENT_SEARCHES_FILE, record, max_entries=2000)
