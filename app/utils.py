import re
from datetime import datetime, timezone


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip('-')


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()