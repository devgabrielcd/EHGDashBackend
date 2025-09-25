from typing import Optional, Dict, Any
from django.contrib.auth import get_user_model
from .models import ActivityLog

User = get_user_model()

def log_activity(
    *,
    actor: Optional[User],
    action: str,
    target_user: Optional[User] = None,
    company=None,
    message: str = "",
    meta: Optional[Dict[str, Any]] = None,
):
    try:
        ActivityLog.objects.create(
            actor=actor,
            action=action,
            target_user=target_user,
            company=company,
            message=message or "",
            meta=meta or {},
        )
    except Exception:
        # não quebrar o fluxo se o log falhar
        pass
