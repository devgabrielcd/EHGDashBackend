# src/reports/api/views.py
from typing import Dict, Any, List
from datetime import datetime
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.utils.dateparse import parse_date

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from src.reports.models import Report

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _is_admin(request) -> bool:
    """
    Admin conforme sua regra atual (via profile.user_role) com fallback para superuser/staff.
    """
    try:
        prof = getattr(request.user, "profile", None)
        role_name = getattr(getattr(prof, "user_role", None), "user_role", "") or ""
        return (
            role_name.lower() in {"admin", "administrator", "owner", "superadmin"}
            or request.user.is_superuser
            or request.user.is_staff
        )
    except Exception:
        return bool(getattr(request.user, "is_staff", False))

def _safe_int(val, default=None):
    try:
        return int(val)
    except Exception:
        return default

def _fmt_date(d: datetime) -> str:
    if not d:
        return None
    try:
        return d.isoformat()
    except Exception:
        return None

def serialize_report(r: Report) -> Dict[str, Any]:
    """
    Serializer enxuto para listagens.
    (Sem 'config' por padrão; pode ser incluído com ?include=config)
    """
    return {
        "id": str(r.id),
        "name": r.name,
        "type": r.type,
        "status": r.status,
        "owner": getattr(r.owner, "username", None) or getattr(r.owner, "email", None),
        "updated_at": _fmt_date(r.updated_at) or _fmt_date(r.created_at),
        "created_at": _fmt_date(r.created_at),
    }

def serialize_report_detail(r: Report) -> Dict[str, Any]:
    """
    Serializer completo para GET/PATCH de um único relatório.
    Inclui 'config' (necessário para o viewer/builder no front).
    """
    return {
        "id": str(r.id),
        "name": r.name,
        "type": r.type,
        "status": r.status,
        "owner": {
            "id": getattr(r.owner, "id", None),
            "username": getattr(r.owner, "username", None),
            "email": getattr(r.owner, "email", None),
        },
        "config": r.config or {},
        "updated_at": _fmt_date(r.updated_at) or _fmt_date(r.created_at),
        "created_at": _fmt_date(r.created_at),
    }

def _apply_filters(qs, request):
    """
    Filtros para listagens/stats:
      - ?q=<texto> (name/type)
      - ?type=<tipo>
      - ?from=YYYY-MM-DD
      - ?to=YYYY-MM-DD
    """
    q = (request.query_params.get("q") or "").strip()
    rtype = (request.query_params.get("type") or "").strip()
    date_from = request.query_params.get("from")
    date_to = request.query_params.get("to")

    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(type__icontains=q))
    if rtype:
        qs = qs.filter(type__iexact=rtype)

    # por updated_at (pode trocar para created_at se preferir)
    if date_from:
        dfrom = parse_date(date_from)
        if dfrom:
            qs = qs.filter(updated_at__date__gte=dfrom)
    if date_to:
        dto = parse_date(date_to)
        if dto:
            qs = qs.filter(updated_at__date__lte=dto)

    return qs

def _paginate(request, qs):
    page = _safe_int(request.query_params.get("page"), 1) or 1
    page_size = _safe_int(request.query_params.get("page_size"), 10) or 10
    total = qs.count()
    start = (page - 1) * page_size
    end = start + page_size
    return page, page_size, total, qs[start:end]

# ---------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def reports_list_create_api(request):
    """
    GET: lista relatórios (autenticado). Suporta filtros e paginação.
         Use '?include=config' para trazer 'config' na listagem.
    POST: cria relatório (somente admin).
    """
    if request.method == "GET":
        qs = Report.objects.select_related("owner").all().order_by("-updated_at")
        qs = _apply_filters(qs, request)
        page, page_size, total, page_qs = _paginate(request, qs)

        data = [serialize_report(r) for r in page_qs]

        # incluir config se solicitado explicitamente (evita payloads grandes por padrão)
        if (request.query_params.get("include") or "").lower() == "config":
            for i, r in enumerate(page_qs):
                data[i]["config"] = r.config or {}

        return Response({
            "results": data,
            "count": total,
            "page": page,
            "page_size": page_size,
        })

    # POST
    if not _is_admin(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    payload = request.data or {}
    name = (payload.get("name") or "").strip()
    rtype = (payload.get("type") or "").strip() or "General"
    status_val = (payload.get("status") or Report.Status.READY)

    if not name:
        return Response({"detail": "name is required"}, status=status.HTTP_400_BAD_REQUEST)

    r = Report.objects.create(
        name=name,
        type=rtype,
        status=status_val if status_val in Report.Status.values else Report.Status.READY,
        owner=request.user,                 # se quiser permitir outro owner, aceite owner_id no payload
        config=payload.get("config") or {}, # guarda configuração do builder
    )
    return Response(serialize_report_detail(r), status=status.HTTP_201_CREATED)

@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def report_detail_api(request, pk):
    r = get_object_or_404(Report.objects.select_related("owner"), pk=pk)

    if request.method == "GET":
        return Response(serialize_report_detail(r))

    if not _is_admin(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "PATCH":
        payload = request.data or {}
        name = payload.get("name")
        rtype = payload.get("type")
        status_val = payload.get("status")
        config = payload.get("config")

        if name is not None:
            r.name = name.strip() or r.name
        if rtype is not None:
            r.type = rtype.strip() or r.type
        if status_val is not None and status_val in Report.Status.values:
            r.status = status_val
        if config is not None:
            r.config = config

        # opcional: permitir trocar owner (admin only)
        owner_id = payload.get("owner_id")
        if owner_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                r.owner = User.objects.get(pk=int(owner_id))
            except Exception:
                pass

        r.save()
        return Response(serialize_report_detail(r))

    # DELETE
    r.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def report_types_list_api(request):
    """
    Lista tipos distintos para popular filtros do front.
    """
    # ordenar antes do values_list/distinct para evitar edge cases
    types = (
        Report.objects.order_by("type")
        .values_list("type", flat=True)
        .distinct()
    )
    out = [{"label": t, "value": t} for t in types if t]
    return Response(out)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def reports_stats_api(request):
    """
    Contagens para cartões do topo.
    """
    qs = Report.objects.all()
    qs = _apply_filters(qs, request)

    total = qs.count()
    agg = qs.values("status").annotate(c=Count("id"))
    by = {row["status"]: row["c"] for row in agg}

    out = {
        "total": total,
        "ready": by.get("Ready", 0) + by.get("Active", 0),
        "processing": by.get("Processing", 0) + by.get("Scheduled", 0),
        "failed": by.get("Failed", 0),
    }
    return Response(out)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def report_export_api(request, pk):
    """
    Exporta CSV (placeholder). Em produção, gere dataset conforme r.config.
    """
    r = get_object_or_404(Report, pk=pk)

    fmt = (request.query_params.get("format") or "csv").lower()
    if fmt != "csv":
        return Response({"detail": "Only CSV is supported right now."}, status=status.HTTP_400_BAD_REQUEST)

    # Exemplo simplificado
    rows: List[Dict[str, Any]] = [
        {"metric": "revenue", "value": 12345, "date": "2025-08-01"},
        {"metric": "orders", "value": 678, "date": "2025-08-01"},
    ]

    import csv
    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = f'attachment; filename="{(r.name or "report").replace(" ", "_")}.csv"'
    writer = csv.DictWriter(resp, fieldnames=["metric", "value", "date"])
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return resp
 