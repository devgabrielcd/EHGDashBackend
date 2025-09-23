# src/analytics/api/views.py
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone, date as _date
from calendar import month_abbr

from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from src.users.models import Profile
from src.forms.models import FormSubmission  # ⬅️ novo
from .filters import ProfileFilterSet, UserFilterSet, FormSubmissionFilterSet

# importa helpers do app users
from src.users.api.views import (
    _is_admin,
    _safe_int,
    _coerce_to_date,
    _parse_bool,  # não usado aqui, mas ok manter
    serialize_user_for_sheets,       # não usamos neste arquivo, mas ok
    serialize_user_with_profile,     # idem
)

User = get_user_model()

# ------------------------
# Helpers específicos do analytics
# ------------------------

def _month_key(d: _date) -> str:
    return f"{d.year}-{str(d.month).zfill(2)}"

def _month_label(d: _date) -> Tuple[str, int]:
    return month_abbr[d.month], d.year

def _build_last_n_months(n: int, anchor: Optional[_date] = None) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc).date()
    start = _date((anchor or now).year, (anchor or now).month, 1)
    out: List[Dict[str, Any]] = []
    for i in range(n - 1, -1, -1):
        year = start.year
        month = start.month - i
        while month <= 0:
            month += 12
            year -= 1
        d = _date(year, month, 1)
        lbl, y = _month_label(d)
        out.append({"key": _month_key(d), "label": lbl, "year": y, "count": 0})
    return out

def _build_ytd_months(anchor: Optional[_date] = None) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc).date()
    y = (anchor or now).year
    last_month = (anchor or now).month
    out: List[Dict[str, Any]] = []
    for m in range(1, last_month + 1):
        d = _date(y, m, 1)
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


# ------------------ Endpoints ------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def users_product_mix(request):
    """
    Agregações para o "System Health".

    Filtros aceitos:
      - company=<id>
      - insuranceCoverage=<str> | insuranceCoverage__in=A,B,C
      - coverageType=<str>
      - include_unknown=1|0     (aplica nos campos do Profile)
      - formType=<str> | formType__in=A,B,C  (aplica em FormSubmission)
      - order=asc|desc          (padrão: desc)
      - limit=<int>
      - view=insurance|planTypes|formTypes|all

    Resposta:
      {
        "by_insurance": [{"insuranceCoverage": "...", "total": N}, ...],
        "by_plan": [{"coverageType": "...", "total": N}, ...],
        "by_form": [{"formType": "...", "total": N}, ...]
      }
    """
    if not _is_admin(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    view  = (request.query_params.get("view")  or "all").strip().lower()
    order = (request.query_params.get("order") or "desc").strip().lower()
    limit = _safe_int(request.query_params.get("limit"))

    # ------- Profiles (insurance/plan) -------
    base_profiles = Profile.objects.select_related("company")
    pf = ProfileFilterSet(request.GET, queryset=base_profiles)
    qsp = pf.qs

    by_insurance_list, by_plan_list, by_form_list = [], [], []

    if view in ("insurance", "all"):
        q = qsp.values("insuranceCoverage").annotate(total=Count("id")).order_by("total" if order == "asc" else "-total")
        if limit: q = q[:limit]
        by_insurance_list = list(q)

    if view in ("plantypes", "all"):
        q = qsp.values("coverageType").annotate(total=Count("id")).order_by("total" if order == "asc" else "-total")
        if limit: q = q[:limit]
        by_plan_list = list(q)

    # ------- Form Submissions (formTypes) -------
    if view in ("formtypes", "all"):
        base_forms = FormSubmission.objects.select_related("company")
        ff = FormSubmissionFilterSet(request.GET, queryset=base_forms)
        qsf = ff.qs.exclude(formType__isnull=True).exclude(formType__exact="")
        q = qsf.values("formType").annotate(total=Count("id")).order_by("total" if order == "asc" else "-total")
        if limit: q = q[:limit]
        by_form_list = list(q)

    return Response({
        "by_insurance": by_insurance_list if view in ("insurance", "all") else [],
        "by_plan":      by_plan_list      if view in ("plantypes", "all") else [],
        "by_form":      by_form_list      if view in ("formtypes", "all") else [],
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def revenue_series(request):
    """
    Filtros via django-filter (UserFilterSet):
      - company=<id>
      - q=<search>
      - date_joined_after=YYYY-MM-DD
      - date_joined_before=YYYY-MM-DD
    Além de 'period=3|6|12|24|ytd'
    """
    if not _is_admin(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    period_kind, n_months = _parse_period(request.query_params)

    base = (
        User.objects.all()
        .select_related("profile", "profile__company")
        .order_by("-date_joined")
    )
    f = UserFilterSet(request.GET, queryset=base)
    qs = f.qs

    months = _build_ytd_months() if period_kind == "ytd" else _build_last_n_months(n_months or 12)
    idx_by_key = {m["key"]: i for i, m in enumerate(months)}

    for u in qs:
        d = _coerce_to_date(u.date_joined)
        if not d:
            continue
        key = _month_key(_date(d.year, d.month, 1))
        i = idx_by_key.get(key)
        if i is not None:
            months[i]["count"] += 1

    series = []
    for i, m in enumerate(months):
        show_year = i == 0 or months[i - 1]["year"] != m["year"]
        name = f"{m['label']} {m['year']}" if show_year else m["label"]
        series.append({"name": name, "count": m["count"]})

    return Response(series)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def top_entities(request):
    """
    Lista flat com suporte a filtros do UserFilterSet:
      - company=<id>
      - q=<search>
      - date_joined_after/before=YYYY-MM-DD
      - limit=1..200
    """
    if not _is_admin(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    limit = _safe_int(request.query_params.get("limit"), 20)
    limit = max(1, min(limit, 200))

    base = (
        User.objects.all()
        .select_related(
            "profile",
            "profile__user_role",
            "profile__user_type",
            "profile__company",
        )
        .order_by("-date_joined")
    )
    f = UserFilterSet(request.GET, queryset=base)
    qs = f.qs

    users = [
        {
            "id": u.id,
            "username": u.username,
            "firstName": getattr(u.profile, "first_name", u.first_name),
            "lastName": getattr(u.profile, "last_name", u.last_name),
            "email": u.email,
            "company_name": getattr(u.profile.company, "name", None),
            "insuranceCoverage": getattr(u.profile, "insuranceCoverage", None),
            "coverageType": getattr(u.profile, "coverageType", None),
            "datetime": u.date_joined.isoformat() if u.date_joined else None,
        }
        for u in qs[:limit]
    ]
    return Response(users)
