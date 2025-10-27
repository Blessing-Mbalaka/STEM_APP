from __future__ import annotations

import hashlib
from typing import Any


def anonymize_user_label(user: Any, prefix: str = "Learner") -> str:
    """
    Generate a stable anonymised label for a user without exposing PII.
    The label is derived from the user's primary key, username and email,
    hashed with SHA-256 and truncated for readability.
    """
    if not getattr(user, "is_authenticated", False):
        return f"{prefix}-Guest"

    raw = f"{getattr(user, 'pk', '')}:{getattr(user, 'username', '')}:{getattr(user, 'email', '')}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8].upper()
    return f"{prefix}-{digest}"
