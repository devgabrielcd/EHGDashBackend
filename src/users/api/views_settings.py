from typing import Dict, Any
from datetime import datetime, timezone, date  # 👈 necessário p/ _coerce_to_date
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.db import transaction
from django.db.models import Q, Count
from django.contrib.sessions.models import Session
from django.utils import timezone as dj_tz

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from src.users.models import Profile, UserRole, UserType
from src.company.models import Company

from django.db.models.functions import Coalesce
from src.forms.models import FormSubmission

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


def _coerce_to_date(value):
    """
    Converte datetime/date/string ISO para date (UTC). Compatível com Python 3.9+.
    Usado por endpoints de analytics.
    """
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


def serialize_user_for_sheets(user: User, request=None) -> Dict[str, Any]:
    """
    Serialização flat no formato consumido pelo frontend (TopEntities/SystemHealth/UserAccounts).
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
    Inclui user_role e user_type também no objeto user.
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
    # normaliza datas em ISO
    for k in ("date_joined", "last_login"):
        v = user_data.get(k)
        if isinstance(v, (date, datetime)):
            user_data[k] = v.isoformat()

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
# ENDPOINTS DE USUÁRIOS (limpos: sem analytics)
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
    GET: admin OU o próprio usuário (self).
    PATCH: admin OU o próprio usuário (self) em campos 'seguros' (perfil básico).
    DELETE: admin OU o próprio usuário (self) — self faz hard delete.
    """
    user = get_object_or_404(
        User.objects.select_related("profile", "profile__user_role", "profile__user_type", "profile__company"),
        pk=pk
    )
    is_self = request.user.is_authenticated and request.user.id == user.id
    is_admin = _is_admin(request)

    # ---------- GET ----------
    if request.method == "GET":
        if not (is_admin or is_self):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        data = serialize_user_with_profile(user, request=request)
        return Response({"user": data["user"], "profile": data["profile"]})

    # ---------- PATCH ----------
    if request.method == "PATCH":
        data = request.data or {}
        profile = user.profile

        if is_admin:
            # fluxo atual de admin (completo)
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

        elif is_self:
            # fluxo 'seguro' para o próprio usuário (sem username/is_active/password/role/type/company)
            for field in ["first_name", "last_name", "email"]:
                if field in data and data[field] is not None:
                    if field == "email":
                        user.email = data[field].strip().lower()
                    else:
                        setattr(user, field, data[field])
            user.save()

            for field in ["first_name", "middle_name", "last_name", "phone_number", "email"]:
                if field in data and data[field] is not None:
                    setattr(profile, field, data[field])

            if "coverageType" in data:
                profile.coverageType = data["coverageType"]
            if "insuranceCoverage" in data:
                profile.insuranceCoverage = data["insuranceCoverage"]

            profile.save()
        else:
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        out = serialize_user_with_profile(user, request=request)
        return Response({"user": out["user"], "profile": out["profile"]})

    # ---------- DELETE ----------
    if not (is_admin or is_self):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    if is_self:
        try:
            request.session.flush()  # derruba a sessão atual
        except Exception:
            pass
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    user.delete()  # admin
    return Response(status=status.HTTP_204_NO_CONTENT)

# ---------------------------------------------------------------------
# Auxiliares (listas)
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
# KPIs para Dashboard
# ---------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_stats_api(request):
    """
    KPIs simples para o dashboard.
    """
    qs = User.objects.all().select_related("profile", "profile__company")

    # ----- filtros por empresa -----
    companies_csv = (request.query_params.get("companies") or "").strip()
    company_param = (request.query_params.get("company") or "all").strip()

    if companies_csv:
        try:
            ids = [int(x) for x in companies_csv.split(",") if x.strip().isdigit()]
        except Exception:
            ids = []
        if ids:
            qs = qs.filter(profile__company__id__in=ids)
    elif company_param and company_param != "all":
        try:
            cid = int(company_param)
            qs = qs.filter(profile__company__id=cid)
        except Exception:
            pass

    total_users = qs.count()

    # contagem por empresa
    by_company_qs = (
        qs.values("profile__company__id", "profile__company__name")
          .annotate(total=Count("id"))
          .order_by("-total", "profile__company__name")
    )
    by_company = [
        {
            "company_id": row["profile__company__id"],
            "company_name": row["profile__company__name"],
            "total": row["total"],
        }
        for row in by_company_qs
    ]

    # KPIs específicos
    h4h_users = qs.filter(profile__company__name__icontains="h4h").count()
    qol_users = qs.filter(
        Q(profile__company__name__icontains="qol") |
        Q(profile__company__name__icontains="quality of life")
    ).count()

    if h4h_users == 0 or qol_users == 0:
        h4h_total = 0
        qol_total = 0
        for row in by_company_qs:
            name = (row["profile__company__name"] or "").lower()
            if "h4h" in name:
                h4h_total += row["total"]
            if "qol" in name or "quality of life" in name:
                qol_total += row["total"]
        if h4h_users == 0:
            h4h_users = h4h_total
        if qol_users == 0:
            qol_users = qol_total

    data = {
        "total_users": total_users,
        "h4h_users": h4h_users,
        "qol_users": qol_users,
        "by_company": by_company,
    }
    return Response(data)

# ---------------------------------------------------------------------
# SETTINGS: Security, Preferences, Sessions, Integrations
# ---------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def change_password_api(request):
    data = request.data or {}
    current_password = (data.get("current_password") or "").strip()
    new_password = (data.get("new_password") or "").strip()

    if not current_password or not new_password:
        return Response({"detail": "current_password and new_password are required"}, status=400)

    user = request.user
    if not user.check_password(current_password):
        return Response({"detail": "Current password is incorrect"}, status=400)

    user.set_password(new_password)
    user.save()
    update_session_auth_hash(request, user)  # mantém logado
    return Response({"detail": "Password changed successfully"})


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def user_preferences_api(request, pk):
    user = get_object_or_404(User.objects.select_related("profile"), pk=pk)
    is_self = request.user.id == user.id
    is_admin = _is_admin(request)
    if not (is_self or is_admin):
        return Response({"detail": "Forbidden"}, status=403)

    profile = getattr(user, "profile", None)

    def get_prefs():
        theme = getattr(profile, "theme", None)
        email = getattr(profile, "notif_email", None)
        push = getattr(profile, "notif_push", None)
        blob = getattr(profile, "meta", None) or getattr(profile, "integrations", None) or {}
        if theme is None:
            theme = (blob.get("prefs", {}) or {}).get("theme", "system")
        if email is None:
            email = (blob.get("prefs", {}) or {}).get("notifications", {}).get("email", True)
        if push is None:
            push = (blob.get("prefs", {}) or {}).get("notifications", {}).get("push", False)
        return {"theme": (theme or "system"), "notifications": {"email": bool(email), "push": bool(push)}}

    if request.method == "GET":
        return Response(get_prefs())

    data = request.data or {}
    prefs = get_prefs()

    if "theme" in data:
        val = (data["theme"] or "system").lower()
        if val not in {"light", "dark", "system"}:
            return Response({"detail": "invalid theme"}, status=400)
        if hasattr(profile, "theme"):
            profile.theme = val
        else:
            blob = getattr(profile, "meta", None) or getattr(profile, "integrations", None) or {}
            p = blob.get("prefs", {}) or {}
            p["theme"] = val
            blob["prefs"] = p
            if hasattr(profile, "meta"):
                profile.meta = blob
            else:
                profile.integrations = blob

    if "notifications" in data:
        notif = data["notifications"] or {}
        email = bool(notif.get("email", prefs["notifications"]["email"]))
        push = bool(notif.get("push", prefs["notifications"]["push"]))
        if hasattr(profile, "notif_email"):
            profile.notif_email = email
            profile.notif_push = push
        else:
            blob = getattr(profile, "meta", None) or getattr(profile, "integrations", None) or {}
            p = blob.get("prefs", {}) or {}
            p["notifications"] = {"email": email, "push": push}
            blob["prefs"] = p
            if hasattr(profile, "meta"):
                profile.meta = blob
            else:
                profile.integrations = blob

    profile.save()
    return Response(get_prefs())


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_sessions_api(request, pk):
    if not (request.user.id == pk or _is_admin(request)):
        return Response({"detail": "Forbidden"}, status=403)

    sessions = []
    now = dj_tz.now()
    for s in Session.objects.filter(expire_date__gt=now):
        data = s.get_decoded()
        if str(data.get("_auth_user_id")) == str(pk):
            sessions.append({
                "id": s.session_key,
                "device": data.get("ua", "Unknown device"),  # opcional (se você salvar UA)
                "ip": data.get("ip"),
                "created_at": None,  # preencha se você salvar isso no login
                "last_active_at": s.expire_date.isoformat(),
                "current": s.session_key == request.session.session_key,
            })
    return Response(sessions)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def user_session_delete_api(request, pk, key: str):
    if not (request.user.id == pk or _is_admin(request)):
        return Response({"detail": "Forbidden"}, status=403)
    try:
        s = Session.objects.get(session_key=key)
    except Session.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)
    data = s.get_decoded()
    if str(data.get("_auth_user_id")) != str(pk):
        return Response({"detail": "Forbidden"}, status=403)
    s.delete()
    return Response({"ok": True})


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def user_integrations_api(request, pk):
    user = get_object_or_404(User.objects.select_related("profile"), pk=pk)
    if not (request.user.id == user.id or _is_admin(request)):
        return Response({"detail": "Forbidden"}, status=403)

    profile = user.profile

    def read_blob():
        if hasattr(profile, "integrations") and isinstance(profile.integrations, dict):
            return profile.integrations
        if hasattr(profile, "meta") and isinstance(profile.meta, dict):
            return profile.meta.get("integrations", {})
        return {}

    if request.method == "GET":
        return Response(read_blob())

    payload = request.data or {}
    blob = read_blob()
    blob.update({k: bool(v) for (k, v) in payload.items()})

    if hasattr(profile, "integrations"):
        profile.integrations = blob
    elif hasattr(profile, "meta"):
        m = profile.meta or {}
        m["integrations"] = blob
        profile.meta = m
    else:
        # sem campo para persistir: responde OK (stateless) até você criar JSONField
        return Response(blob)

    profile.save()
    return Response(blob)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def auth_session_api(request):
    """
    Retorna o usuário autenticado com base na sessão/JWT atual.
    Útil para o frontend descobrir o userId sem localStorage.
    """
    user = request.user
    prof = getattr(user, "profile", None)
    return Response({
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
        "profile_id": getattr(prof, "id", None),
    })