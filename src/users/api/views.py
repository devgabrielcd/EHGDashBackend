# src/users/api/views.py
from typing import Dict, Any
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q, Count

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from src.users.models import Profile, UserRole, UserType
from src.company.models import Company

User = get_user_model()

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _build_image_url(image_field, request=None):
    if not image_field:
        return None
    try:
        url = image_field.url
    except Exception:
        return None
    return request.build_absolute_uri(url) if request else url


def _is_admin(request) -> bool:
    prof = getattr(request.user, "profile", None)
    if not prof and request.user.is_authenticated:
        try:
            prof = Profile.objects.select_related("user_role").get(user=request.user)
        except Profile.DoesNotExist:
            prof = None
    role_name = getattr(getattr(prof, "user_role", None), "user_role", "") or ""
    return role_name.lower() in {"admin", "administrator", "owner", "superadmin"}


def _parse_bool(val, default=False):
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}


def _safe_int(val, default=None):
    try:
        return int(val)
    except Exception:
        return default


def serialize_user_for_sheets(user: User, request=None) -> Dict[str, Any]:
    """
    Serialização flat no formato consumido pelo frontend (TopEntities/SystemHealth/UserAccounts).
    Lê coverageType e insuranceCoverage do Profile.
    Inclui também user_role e user_type (nomes) para exibição na tabela.
    """
    profile = getattr(user, "profile", None)

    insurance_coverage = getattr(profile, "insuranceCoverage", None)
    coverage_type = getattr(profile, "coverageType", None)

    # Fallback temporário (remova quando todos estiverem migrados)
    if not insurance_coverage:
        insurance_coverage = getattr(getattr(profile, "user_role", None), "user_role", None)
    if not coverage_type:
        coverage_type = getattr(getattr(profile, "user_type", None), "user_type", None)

    data = {
        "id": user.id,
        "username": getattr(user, "username", None),
        "is_active": bool(getattr(user, "is_active", False)),

        "firstName": getattr(profile, "first_name", None) or getattr(user, "first_name", None),
        "lastName":  getattr(profile, "last_name",  None) or getattr(user, "last_name",  None),
        "email":     getattr(profile, "email",      None) or getattr(user, "email",      None),
        "phone":     getattr(profile, "phone_number", None),

        # Planos usados no SystemHealth
        "insuranceCoverage": insurance_coverage,   # Medicare / Dental / Life / Health / Vision
        "coverageType":      coverage_type,        # individual / family

        # Também expõe role/type (nomes)
        "user_role": getattr(getattr(profile, "user_role", None), "user_role", None),
        "user_type": getattr(getattr(profile, "user_type", None), "user_type", None),

        "company_name": getattr(getattr(profile, "company", None), "name", None),
        "datetime": user.date_joined.isoformat() if user.date_joined else None,

        # compat com antigo sheets (não é usado em /api/users)
        "formType": None,
    }
    return data


def serialize_user_with_profile(user: User, request=None) -> Dict[str, Any]:
    """
    Usado em /api/users/<id>/ para retornar {user, profile}.
    Inclui user_role e user_type também no objeto user para compatibilidade com o auth/session.
    """
    profile = getattr(user, "profile", None)
    user_data = model_to_dict(
        user,
        fields=[
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "date_joined",
            "last_login",
        ],
    )
    from datetime import date, datetime
    for k in ("date_joined", "last_login"):
        if isinstance(user_data.get(k), (date, datetime)):
            user_data[k] = user_data[k].isoformat()

    # Adiciona role/type direto no "user"
    if profile:
        user_data["user_role"] = getattr(getattr(profile, "user_role", None), "user_role", None)
        user_data["user_type"] = getattr(getattr(profile, "user_type", None), "user_type", None)

    profile_data = {}
    if profile:
        profile_data = model_to_dict(profile, exclude=["user"])
        profile_data["image"] = _build_image_url(profile.image, request)
        profile_data["user_type"] = getattr(profile.user_type, "user_type", None)
        profile_data["user_type_id"] = getattr(profile.user_type, "id", None)
        profile_data["user_role"] = getattr(profile.user_role, "user_role", None)
        profile_data["user_role_id"] = getattr(profile.user_role, "id", None)
        for k in ("date_of_birth", "signed_date"):
            v = profile_data.get(k)
            if isinstance(v, (date, datetime)):
                profile_data[k] = v.isoformat()
    return {"user": user_data, "profile": profile_data}

# ---------------------------------------------------------------------
# ENDPOINTS DE USUÁRIOS
# ---------------------------------------------------------------------

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def users_list_create_api(request):
    # Somente admins podem listar/criar usuários
    if not _is_admin(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        qs = (
            User.objects.all()
            .select_related("profile", "profile__user_role", "profile__user_type", "profile__company")
            .order_by("-date_joined")
        )

        company_id = request.query_params.get("company")
        if company_id:
            qs = qs.filter(profile__company__id=company_id)

        q = request.query_params.get("q")
        if q:
            qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q))

        users = [serialize_user_for_sheets(u, request=request) for u in qs]
        return Response(users)

    # POST (criação)
    data = request.data or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")

    if not email or not password:
        return Response({"detail": "email and password are required"}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(email=email).exists():
        return Response({"detail": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)

    username = (data.get("username") or email).strip().lower()

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=data.get("first_name", ""),
        last_name=data.get("last_name", ""),
        is_active=_parse_bool(data.get("is_active"), True),
    )

    profile, _ = Profile.objects.get_or_create(user=user)

    # campos simples
    for field in ["first_name", "middle_name", "last_name", "phone_number", "email"]:
        if field in data:
            setattr(profile, field, data.get(field))

    # Campos de planos (opcionais)
    if "coverageType" in data:
        profile.coverageType = data.get("coverageType")  # 'individual'|'family'
    if "insuranceCoverage" in data:
        profile.insuranceCoverage = data.get("insuranceCoverage")  # 'Medicare'|'Dental'|...

    # relacionamentos
    user_role_id = _safe_int(data.get("user_role_id"))
    if user_role_id:
        profile.user_role = get_object_or_404(UserRole, id=user_role_id)

    user_type_id = _safe_int(data.get("user_type_id"))
    if user_type_id:
        profile.user_type = get_object_or_404(UserType, id=user_type_id)

    company_id = _safe_int(data.get("company_id"))
    if company_id:
        profile.company = get_object_or_404(Company, id=company_id)

    profile.save()
    return Response(serialize_user_for_sheets(user, request=request), status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def user_detail_api(request, pk):
    """
    GET: permite admin OU o próprio usuário (self).
    PATCH/DELETE: somente admin.
    """
    user = get_object_or_404(
        User.objects.select_related("profile", "profile__user_role", "profile__user_type", "profile__company"),
        pk=pk
    )
    is_self = request.user.is_authenticated and request.user.id == user.id
    is_admin = _is_admin(request)

    if request.method == "GET":
        if not (is_admin or is_self):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        data = serialize_user_with_profile(user, request=request)
        return Response({"user": data["user"], "profile": data["profile"]})

    if not is_admin:
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "PATCH":
        data = request.data or {}
        profile = user.profile

        if "username" in data and data["username"]:
            new_username = data["username"].strip().lower()
            if new_username != user.username and User.objects.filter(username=new_username).exists():
                return Response({"detail": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST)
            user.username = new_username

        if "email" in data and data["email"]:
            user.email = data["email"].strip().lower()

        if "password" in data and data["password"]:
            user.set_password(data["password"])

        if "is_active" in data:
            user.is_active = _parse_bool(data["is_active"], user.is_active)

        user.save()

        for field in ["first_name", "middle_name", "last_name", "phone_number", "email"]:
            if field in data:
                setattr(profile, field, data.get(field))

        # Campos de planos (opcionais)
        if "coverageType" in data:
            profile.coverageType = data.get("coverageType")
        if "insuranceCoverage" in data:
            profile.insuranceCoverage = data.get("insuranceCoverage")

        user_role_id = _safe_int(data.get("user_role_id"))
        if user_role_id:
            profile.user_role = get_object_or_404(UserRole, id=user_role_id)

        user_type_id = _safe_int(data.get("user_type_id"))
        if user_type_id:
            profile.user_type = get_object_or_404(UserType, id=user_type_id)

        company_id = _safe_int(data.get("company_id"))
        if company_id:
            profile.company = get_object_or_404(Company, id=company_id)

        profile.save()

        out = serialize_user_with_profile(user, request=request)
        return Response({"user": out["user"], "profile": out["profile"]})

    # DELETE
    hard = _parse_bool(request.query_params.get("hard"), False)
    if hard:
        user.delete()
        return Response({"ok": True, "deleted": True}, status=status.HTTP_204_NO_CONTENT)
    else:
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response({"ok": True, "deleted": False, "deactivated": True})

# ---------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_roles_list_api(request):
    if not _is_admin(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    roles = UserRole.objects.all().order_by("id").values("id", "user_role")
    return Response([{"id": r["id"], "name": r["user_role"]} for r in roles])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_types_list_api(request):
    if not _is_admin(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    types = UserType.objects.all().order_by("id").values("id", "user_type")
    return Response([{"id": t["id"], "name": t["user_type"]} for t in types])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def detail_user_api(request, pk):
    """
    Endpoint legado usado em alguns pontos: recebe PK de Profile.
    Mantido para compatibilidade.
    """
    profile = get_object_or_404(Profile, id=pk)
    data = serialize_user_with_profile(profile.user, request=request)
    return Response({"user": data["user"], "profile": data["profile"]})

# ---------------------------------------------------------------------
# KPIs / Stats
# ---------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def users_stats_api(request):
    if not _is_admin(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    company_id = request.query_params.get("company")

    base = Profile.objects.select_related("company")
    if company_id:
        base = base.filter(company__id=company_id)

    total_users = base.count()

    # Contagens por companhia (ajuste os nomes conforme seu seed)
    h4h_users = base.filter(
        Q(company__name__iexact="H4hInsurance")
        | Q(company__name__iexact="h4hinsurance")
        | Q(company__name__iexact="H4HInsurance")
    ).count()

    qol_users = base.filter(
        Q(company__name__iexact="qolinsurance")
        | Q(company__name__iexact="QoLInsurance")
        | Q(company__name__iexact="QoL")
    ).count()

    by_insurance = (
        base.values("insuranceCoverage")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    by_coverage_type = (
        base.values("coverageType")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    return Response(
        {
            "total_users": total_users,
            "h4h_users": h4h_users,
            "qol_users": qol_users,
            "by_insurance": list(by_insurance),
            "by_coverage_type": list(by_coverage_type),
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def users_product_mix(request):
    """
    Retorna agregações enxutas para gráficos:
      - by_insurance: [{insuranceCoverage, total}]
      - by_plan:      [{coverageType, total}]
    Filtro opcional por ?company=<id>
    """
    company_id = request.query_params.get("company")
    base = Profile.objects.all()
    if company_id:
        base = base.filter(company__id=company_id)

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
