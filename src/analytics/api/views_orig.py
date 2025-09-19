# src/analytics/api/views.py
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone, date
from calendar import month_abbr

from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from src.users.models import Profile
from src.company.models import Company  # (se usar em outros lugares)

User = get_user_model()

# ------------------------ Helpers ------------------------

def _is_admin(request) -> bool:
    prof = getattr(request.user, "profile", None)
    if not prof and request.user.is_authenticated:
        try:
            prof = Profile.objects.select_related("user_role").get(user=request.user)
        except Profile.DoesNotExist:
            prof = None
    role_name = getattr(getattr(prof, "user_role", None), "user_role", "") or ""
    return role_name.lower() in {"admin", "administrator", "owner", "superadmin"}

def _safe_int(val, default=None):
    try:
        return int(val)
    except Exception:
        return default

def _coerce_to_date(value) -> Optional[date]:
    """Converte datetime/date/string ISO para date (UTC), compatível Python 3.9."""
    if value is None:
        return None
    if isinstance(value, datetime):
        try:
            return value.astimezone(timezone.utc).date()
        except Exception:
            return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            s = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
            return dt.astimezone(timezone.utc).date()
        except Exception:
            return None
    return None

def _month_key(d: date) -> str:
    return f"{d.year}-{str(d.month).zfill(2)}"

def _month_label(d: date) -> Tuple[str, int]:
    return month_abbr[d.month], d.year

def _build_last_n_months(n: int, anchor: Optional[date] = None) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc).date()
    start = date((anchor or now).year, (anchor or now).month, 1)
    out: List[Dict[str, Any]] = []
    for i in range(n - 1, -1, -1):
        year = start.year
        month = start.month - i
        while month <= 0:
            month += 12
            year -= 1
        d = date(year, month, 1)
        lbl, y = _month_label(d)
        out.append({"key": _month_key(d), "label": lbl, "year": y, "count": 0})
    return out

def _build_ytd_months(anchor: Optional[date] = None) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc).date()
    y = (anchor or now).year
    last_month = (anchor or now).month
    out: List[Dict[str, Any]] = []
    for m in range(1, last_month + 1):
        d = date(y, m, 1)
        lbl, yy = _month_label(d)
        out.append({"key": _month_key(d), "label": lbl, "year": yy, "count": 0})
    return out

def _parse_period(query_params) -> Tuple[str, Optional[int]]:
    """
    period=3|6|12|24  -> ("months", N)
    period=ytd        -> ("ytd", None)
    default           -> ("months", 12)
    """
    p = (query_params.get("period") or "").strip().lower()
    if p == "ytd":
        return ("ytd", None)
    try:
        n = int(p)
        if n <= 0:
            n = 12
        return ("months", n)
    except Exception:
        return ("months", 12)

def _serialize_user_flat(u: User) -> Dict[str, Any]:
    prof = getattr(u, "profile", None)

    insurance_coverage = getattr(prof, "insuranceCoverage", None)
    coverage_type = getattr(prof, "coverageType", None)

    if not insurance_coverage:
        insurance_coverage = getattr(getattr(prof, "user_role", None), "user_role", None)
    if not coverage_type:
        coverage_type = getattr(getattr(prof, "user_type", None), "user_type", None)

    return {
        "id": u.id,
        "username": getattr(u, "username", None),
        "is_active": bool(getattr(u, "is_active", False)),

        "firstName": getattr(prof, "first_name", None) or getattr(u, "first_name", None),
        "lastName":  getattr(prof, "last_name",  None) or getattr(u, "last_name",  None),
        "email":     getattr(prof, "email",      None) or getattr(u, "email",      None),
        "phone":     getattr(prof, "phone_number", None),

        "insuranceCoverage": insurance_coverage,
        "coverageType":      coverage_type,

        "user_role": getattr(getattr(prof, "user_role", None), "user_role", None),
        "user_type": getattr(getattr(prof, "user_type", None), "user_type", None),

        "company_name": getattr(getattr(prof, "company", None), "name", None),

        # usa _coerce_to_date pra não quebrar se vier None/str
        "datetime": (_coerce_to_date(u.date_joined).isoformat()
                     if _coerce_to_date(u.date_joined) else None),

        "formType": None,
    }

# ------------------ Endpoints ------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def revenue_series(request):
    """
    GET params:
      - company: <id> | 'all'
      - period:  '3' | '6' | '12' | '24' | 'ytd'
    Retorna: [{ name: 'Jan 2025', count: 4 }, ...]
    """
    if not _is_admin(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    period_kind, n_months = _parse_period(request.query_params)
    company_id = request.query_params.get("company", "all")

    qs = (
        User.objects.all()
        .select_related("profile", "profile__company")
        .order_by("-date_joined")
    )
    if company_id != "all":
        cid = _safe_int(company_id)
        if cid:
            qs = qs.filter(profile__company__id=cid)

    months = _build_ytd_months() if period_kind == "ytd" else _build_last_n_months(n_months or 12)
    idx_by_key = {m["key"]: i for i, m in enumerate(months)}

    for u in qs:
        d = _coerce_to_date(u.date_joined)
        if not d:
            continue
        key = _month_key(date(d.year, d.month, 1))
        i = idx_by_key.get(key)
        if i is not None:
            months[i]["count"] += 1

    series: List[Dict[str, Any]] = []
    for i, m in enumerate(months):
        show_year = i == 0 or months[i - 1]["year"] != m["year"]
        name = f"{m['label']} {m['year']}" if show_year else m["label"]
        series.append({"name": name, "count": m["count"]})

    return Response(series)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def users_product_mix(request):
    """
    GET params:
      - company: <id> | 'all'
    Retorna:
      { "by_insurance": [{"insuranceCoverage": "...", "total": N}, ...],
        "by_plan": [{"coverageType": "...", "total": N}, ...] }
    """
    if not _is_admin(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    company_id = request.query_params.get("company", "all")
    base = Profile.objects.select_related("company")
    if company_id != "all":
        cid = _safe_int(company_id)
        if cid:
            base = base.filter(company__id=cid)

    by_insurance = (
        base.values("insuranceCoverage")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    by_plan = (
        base.values("coverageType")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    return Response({
        "by_insurance": list(by_insurance),
        "by_plan": list(by_plan),
    })

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def top_entities(request):
    """
    GET params:
      - company: <id> | 'all'
      - limit:   1..200 (default 20)
    Retorna: lista flat com os últimos usuários.
    """
    if not _is_admin(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    company_id = request.query_params.get("company", "all")
    limit = _safe_int(request.query_params.get("limit"), 20)
    limit = max(1, min(limit, 200))

    qs = (
        User.objects.all()
        .select_related(
            "profile",
            "profile__user_role",
            "profile__user_type",
            "profile__company",
        )
        .order_by("-date_joined")
    )
    if company_id != "all":
        cid = _safe_int(company_id)
        if cid:
            qs = qs.filter(profile__company__id=cid)

    users = [_serialize_user_flat(u) for u in qs[:limit]]
    return Response(users)
