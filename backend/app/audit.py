import json
from typing import Any, Optional

from app import models


def record(
    db,
    admin: Optional[models.User],
    action: str,
    summary: str,
    target_type: Optional[str] = None,
    target_id: Any = None,
    details: Optional[dict] = None,
) -> models.AdminAuditLog:
    """Adds an audit entry to the current transaction (the caller commits).

    `admin=None` marks an automatic system action, e.g. the 50-upvote dataset rule.
    """
    entry = models.AdminAuditLog(
        admin_id=admin.id if admin else None,
        admin_name=(admin.name or admin.email) if admin else "System",
        action=action,
        target_type=target_type,
        target_id=None if target_id is None else str(target_id),
        summary=summary,
        details_json=json.dumps(details, default=str) if details else None,
    )
    db.add(entry)
    return entry
