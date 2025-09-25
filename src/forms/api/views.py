# forms/api/views.py
from typing import Optional
import re
from django.forms.models import model_to_dict
from django.utils.text import slugify
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from src.forms.models import FormSubmission, FORM_TYPE_CHOICES
from src.company.models import Company
from src.users.models import Profile, UserType  # << precisamos do Profile e UserType

# ---------------------------
# Helpers
# ---------------------------

FORM_TYPES_SET = {v for v, _ in FORM_TYPE_CHOICES}

def serialize_form(f: FormSubmission) -> dict:
    base = model_to_dict(
        f,
        fields=[
            "id","formType","first_name","last_name","email","phone",
            "coverageType","insuranceCoverage","extra","created_at",
        ],
    )
    base["company"]    = f.company.name if f.company else None
    base["company_id"] = f.company_id
    base["profile_id"] = f.profile_id
    base["user_id"]    = getattr(getattr(f, "profile", None), "user_id", None)
    return base

def _clean_str(v: Optional[str]) -> str:
    return (v or "").strip()

def _normalize_phone(v: Optional[str]) -> str:
    return re.sub(r"\D", "", v or "")

def _get_or_create_customer_usertype() -> UserType:
    ut = UserType.objects.filter(user_type__iexact="Customer").first()
    if not ut:
        ut = UserType.objects.create(user_type="Customer")
    return ut

def _unique_username(base: str) -> str:
    """
    Gera username único baseado no 'base'.
    """
    base = re.sub(r"[^a-z0-9._-]+", "", slugify(base, allow_unicode=False))
    base = base or "user"
    if not User.objects.filter(username=base).exists():
        return base
    i = 2
    while True:
        cand = f"{base}{i}"
        if not User.objects.filter(username=cand).exists():
            return cand
        i += 1

def _derive_username(email: str, first_name: str, last_name: str, phone: str) -> str:
    if email and "@" in email:
        return _unique_username(email.split("@", 1)[0])
    if first_name or last_name:
        return _unique_username(f"{first_name}.{last_name}".replace("..","."))
    if phone:
        return _unique_username(f"user{phone[-6:]}")
    return _unique_username("user")

def _find_profile_by_contact(email: str, phone_norm: str) -> Optional[Profile]:
    if email:
        prof = Profile.objects.filter(email__iexact=email).select_related("user").first()
        if prof:
            return prof
        # também tenta via User.email (nem sempre é igual ao Profile.email)
        user = User.objects.filter(email__iexact=email).first()
        if user:
            prof = getattr(user, "profile", None)
            if prof:
                return prof
    if phone_norm:
        prof = Profile.objects.filter(phone_number=phone_norm).select_related("user").first()
        if prof:
            return prof
    return None

def _upsert_user_and_profile_from_form(
    *,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    company: Optional[Company],
    coverageType: Optional[str],
    insuranceCoverage: Optional[str],
    formType: str,
) -> Profile:
    """
    Procura Profile por email/telefone; se não tem, cria User (senha inutilizável) + Profile.
    Sempre garante user_type='Customer' e preenche company/coverage/insurance/formType.
    """
    phone_norm = _normalize_phone(phone)
    email = email.lower()

    prof = _find_profile_by_contact(email, phone_norm)

    if not prof:
        # Criar novo User
        username = _derive_username(email, first_name, last_name, phone_norm)
        user = User.objects.create_user(username=username, email=email or None, password=None)
        user.set_unusable_password()
        if first_name and not user.first_name:
            user.first_name = first_name
        if last_name and not user.last_name:
            user.last_name = last_name
        user.save()

        # Via sinal, Profile já deve existir; garantimos
        prof = getattr(user, "profile", None) or Profile.objects.create(user=user)
    else:
        user = prof.user
        # Atualiza o User com dados básicos sem sobrescrever o que já existe
        if user:
            if email and not user.email:
                user.email = email
            if first_name and not user.first_name:
                user.first_name = first_name
            if last_name and not user.last_name:
                user.last_name = last_name
            user.save()

    # Garante user_type "Customer"
    customer_ut = _get_or_create_customer_usertype()
    if not prof.user_type_id or prof.user_type_id != customer_ut.id:
        prof.user_type = customer_ut

    # Preenche campos do Profile (sem apagar o que já existe)
    if first_name and not prof.first_name:
        prof.first_name = first_name
    if last_name and not prof.last_name:
        prof.last_name = last_name
    if email and not prof.email:
        prof.email = email
    if phone_norm and not prof.phone_number:
        prof.phone_number = phone_norm
    if company and not prof.company_id:
        prof.company = company

    # Estes podem ser atualizados a cada submissão (faz sentido refletir o último interesse)
    if coverageType:
        prof.coverageType = coverageType
    if insuranceCoverage:
        prof.insuranceCoverage = insuranceCoverage
    if formType:
        prof.formType = formType

    prof.save()
    return prof

# ---------------------------
# Views
# ---------------------------

@api_view(["GET", "POST"])
def form_list_create_api(request):
    if request.method == "GET":
        # Protegido por autenticação para dashboard
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        qs = FormSubmission.objects.select_related("company", "profile").order_by("-created_at")

        company = request.query_params.get("company")
        if company:
            qs = qs.filter(company__id=company)

        formType = request.query_params.get("formType")
        if formType:
            qs = qs.filter(formType__iexact=formType)

        out = [serialize_form(f) for f in qs[:200]]
        return Response(out)

    # POST (público – vindo dos sites)
    data = request.data or {}
    formType = _clean_str(data.get("formType"))
    if not formType or formType not in FORM_TYPES_SET:
        return Response({"detail": f"Invalid formType. Allowed: {sorted(FORM_TYPES_SET)}"}, status=status.HTTP_400_BAD_REQUEST)

    email = _clean_str(data.get("email"))
    phone = _clean_str(data.get("phone"))

    if not email and not phone:
        return Response({"detail": "At least one of email or phone is required."}, status=status.HTTP_400_BAD_REQUEST)

    first_name = _clean_str(data.get("first_name"))
    last_name  = _clean_str(data.get("last_name"))

    company = Company.objects.filter(id=data.get("company_id")).first() if data.get("company_id") else None

    coverageType      = _clean_str(data.get("coverageType")) or None
    insuranceCoverage = _clean_str(data.get("insuranceCoverage")) or None
    extra             = data.get("extra") or {}

    # 1) Salva o FormSubmission
    f = FormSubmission.objects.create(
        formType=formType,
        email=email or None,
        first_name=first_name or None,
        last_name=last_name or None,
        phone=phone or None,
        company=company,
        coverageType=coverageType,
        insuranceCoverage=insuranceCoverage,
        extra=extra,
    )

    # 2) Cria/Atualiza User + Profile (Customer) e vincula ao Form
    prof = _upsert_user_and_profile_from_form(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        company=company,
        coverageType=coverageType,
        insuranceCoverage=insuranceCoverage,
        formType=formType,
    )

    if prof and not f.profile_id:
        f.profile = prof
        f.save(update_fields=["profile"])

    return Response(serialize_form(f), status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
def form_detail_api(request, pk):
    # Protegido por autenticação
    if not request.user.is_authenticated:
        return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    f = get_object_or_404(FormSubmission, pk=pk)

    if request.method == "GET":
        return Response(serialize_form(f))

    if request.method == "PATCH":
        data = request.data or {}
        for field in ["formType", "email", "first_name", "last_name", "phone", "extra", "coverageType", "insuranceCoverage"]:
            if field in data:
                setattr(f, field, data[field])
        if "company_id" in data:
            f.company = Company.objects.filter(id=data["company_id"]).first()
        f.save()
        return Response(serialize_form(f))

    f.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
