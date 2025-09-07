# src/products/api/views.py
from typing import Dict, Any

from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from src.products.models import Product, PLAN_CHOICES, TYPE_CHOICES
from src.company.models import Company
from src.users.models import Profile


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _is_admin(request) -> bool:
    """
    Mesma lógica usada no app users: libera admin/owner/superadmin/administrator
    """
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


def serialize_product(p: Product) -> Dict[str, Any]:
    """
    Serializer minimalista com model_to_dict + campos derivados
    """
    data = model_to_dict(
        p,
        fields=["id", "name", "coverageType", "insuranceCoverage", "is_active"],
    )
    data["company_id"] = p.company_id
    data["company_name"] = getattr(p.company, "name", None)
    data["coverageTypeLabel"] = dict(PLAN_CHOICES).get(p.coverageType, p.coverageType)
    data["insuranceCoverageLabel"] = dict(TYPE_CHOICES).get(p.insuranceCoverage, p.insuranceCoverage)
    return data


# ---------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def products_list_create_api(request):
    """
    GET: lista produtos (filtros opcionais)
    POST: cria produto (apenas admin)
    """
    if request.method == "GET":
        qs = Product.objects.select_related("company").all()

        # filtros opcionais
        company = request.query_params.get("company")
        if company:
            if company.isdigit():
                qs = qs.filter(company_id=int(company))
            else:
                qs = qs.filter(company__name__iexact=company)

        coverage = request.query_params.get("coverageType")
        if coverage:
            qs = qs.filter(coverageType=coverage)

        insurance = request.query_params.get("insuranceCoverage")
        if insurance:
            qs = qs.filter(insuranceCoverage=insurance)

        q = request.query_params.get("q")
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(company__name__icontains=q))

        include_inactive = request.query_params.get("include_inactive")
        if not (str(include_inactive).strip().lower() in {"1", "true", "yes"}):
            qs = qs.filter(is_active=True)

        items = [serialize_product(p) for p in qs.order_by("company__name", "name", "id")]
        return Response(items)

    # POST
    if not _is_admin(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    data = request.data or {}
    name = (data.get("name") or "").strip()
    if not name:
        return Response({"detail": "name is required"}, status=status.HTTP_400_BAD_REQUEST)

    coverageType = data.get("coverageType")
    insuranceCoverage = data.get("insuranceCoverage")

    valid_cov = {c[0] for c in PLAN_CHOICES}
    valid_ins = {t[0] for t in TYPE_CHOICES}
    if coverageType not in valid_cov:
        return Response({"detail": f"coverageType must be one of {sorted(valid_cov)}"},
                        status=status.HTTP_400_BAD_REQUEST)
    if insuranceCoverage not in valid_ins:
        return Response({"detail": f"insuranceCoverage must be one of {sorted(valid_ins)}"},
                        status=status.HTTP_400_BAD_REQUEST)

    company_id = _safe_int(data.get("company_id"))
    company = get_object_or_404(Company, id=company_id) if company_id else None

    product = Product.objects.create(
        name=name,
        coverageType=coverageType,
        insuranceCoverage=insuranceCoverage,
        company=company,
        is_active=bool(data.get("is_active", True)),
    )
    return Response(serialize_product(product), status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def product_detail_api(request, pk: int):
    """
    GET: detalhe
    PATCH: atualizar (apenas admin)
    DELETE: deletar (apenas admin) — hard delete
    """
    product = get_object_or_404(Product.objects.select_related("company"), pk=pk)

    if request.method == "GET":
        return Response(serialize_product(product))

    if request.method == "PATCH":
        if not _is_admin(request):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        data = request.data or {}

        if "name" in data:
            name = (data.get("name") or "").strip()
            if not name:
                return Response({"detail": "name cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)
            product.name = name

        if "coverageType" in data:
            valid_cov = {c[0] for c in PLAN_CHOICES}
            if data["coverageType"] not in valid_cov:
                return Response({"detail": f"coverageType must be one of {sorted(valid_cov)}"},
                                status=status.HTTP_400_BAD_REQUEST)
            product.coverageType = data["coverageType"]

        if "insuranceCoverage" in data:
            valid_ins = {t[0] for t in TYPE_CHOICES}
            if data["insuranceCoverage"] not in valid_ins:
                return Response({"detail": f"insuranceCoverage must be one of {sorted(valid_ins)}"},
                                status=status.HTTP_400_BAD_REQUEST)
            product.insuranceCoverage = data["insuranceCoverage"]

        if "company_id" in data:
            cid = _safe_int(data.get("company_id"))
            product.company = get_object_or_404(Company, id=cid) if cid else None

        if "is_active" in data:
            v = str(data["is_active"]).strip().lower()
            product.is_active = v in {"1", "true", "yes", "y", "on"}

        product.save()
        return Response(serialize_product(product))

    # DELETE
    if not _is_admin(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    product.delete()
    return Response({"ok": True, "deleted": True}, status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def product_choices_api(request):
    """
    GET: retorna as choices do Product para popular selects no front
    """
    cov = [{"value": v, "label": lbl} for (v, lbl) in PLAN_CHOICES]
    ins = [{"value": v, "label": lbl} for (v, lbl) in TYPE_CHOICES]
    return Response({"coverageType": cov, "insuranceCoverage": ins})
