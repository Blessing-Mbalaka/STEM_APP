from __future__ import annotations

from typing import Any, Set

ROLE_ADMIN = "admin"
ROLE_TUTOR = "tutor"
ROLE_STUDENT = "student"
ROLE_SUPERUSER = "superuser"
ROLE_ANONYMOUS = "anonymous"

_ROLE_PRIORITY = (
    ROLE_ADMIN,
    ROLE_TUTOR,
    ROLE_STUDENT,
    ROLE_ANONYMOUS,
)


def _normalize(role: Any) -> str:
    if isinstance(role, str):
        return role.strip().lower()
    return ""


def get_user_roles(user: Any) -> Set[str]:
    """
    Return a set of logical roles for the given user instance.
    """
    roles: Set[str] = set()
    if not user:
        return {ROLE_ANONYMOUS}

    try:
        if getattr(user, "is_superuser", False):
            roles.add(ROLE_SUPERUSER)
            roles.add(ROLE_ADMIN)
        elif getattr(user, "is_staff", False):
            roles.add(ROLE_ADMIN)

        if getattr(user, "is_tutor", False):
            roles.add(ROLE_TUTOR)

        if getattr(user, "is_authenticated", False):
            if not roles:
                roles.add(ROLE_STUDENT)
        else:
            roles.add(ROLE_ANONYMOUS)
    except Exception:
        roles.add(ROLE_ANONYMOUS)

    if not roles:
        roles.add(ROLE_ANONYMOUS)

    return roles


def get_primary_role(user: Any) -> str:
    """
    Return the primary role for a user, using a predictable priority order.
    """
    roles = get_user_roles(user)
    for role in _ROLE_PRIORITY:
        if role in roles:
            return ROLE_ADMIN if role == ROLE_SUPERUSER else role
    return ROLE_ANONYMOUS


def user_has_role(user: Any, *role_names: str) -> bool:
    """
    Return True if the user has any of the requested roles. Role comparisons
    are case-insensitive and accept "any" as a wildcard.
    """
    if not role_names:
        return False

    requested = {_normalize(r) for r in role_names if r}
    if not requested:
        return False

    if "any" in requested:
        return True

    normalized_roles = get_user_roles(user)
    if ROLE_SUPERUSER in normalized_roles:
        normalized_roles.add(ROLE_ADMIN)

    aliases = set()
    for role in requested:
        if role == ROLE_ADMIN:
            aliases.add(ROLE_ADMIN)
            aliases.add(ROLE_SUPERUSER)
        else:
            aliases.add(role)

    return bool(normalized_roles.intersection(aliases))
