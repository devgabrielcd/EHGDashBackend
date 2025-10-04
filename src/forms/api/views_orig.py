from typing import Optional
import re
from django.forms.models import model_to_dict
from django.utils.text import slugify
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.views import APIView

from src.forms.models import FormSubmission, FORM_TYPE_CHOICES
from src.company.models import Company
from src.users.models import Profile
from src.users.services import create_or_update_user_profile_from_form  # <- usamos o service

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

def _clean(v: Optional[str]) -> str:
    return (v or "").strip()

def _resolve_company(data) -> Optional[Company]:
    raw = data.get("company_id") or data.get("company") or data.get("companySlug") or data.get("companyName")
    if not raw:
        return None
    # id?
    if str(raw).isdigit():
         return Company.objects.filter(id=int(raw)).first()
    # nome exato
    c = Company.objects.filter(name__iexact=str(raw).strip()).first()
    if c: return c
    # slug
    c = Company.objects.filter(slug__iexact=slugify(str(raw))).first()
    if c: return c
    # contains
    return Company.objects.filter(name__icontains=str(raw).strip()).first()

@api_view(["GET", "POST"])
def form_list_create_api(request):
    if request.method == "GET":
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        qs = FormSubmission.objects.select_related("company", "profile").order_by("-created_at")

        company = request.query_params.get("company")
        if company:
            if str(company).isdigit():
                qs = qs.filter(company__id=int(company))
            else:
                qs = qs.filter(company__name__iexact=str(company))

        formType = request.query_params.get("formType")
        if formType:
            qs = qs.filter(formType__iexact=formType)

        out = [serialize_form(f) for f in qs[:200]]
        return Response(out)

    # POST (público — websites)
    data = request.data or {}

    # aceita camelCase e snake_case
    formType = _clean(data.get("formType") or data.get("form_type") or "homepage")
    first_name = _clean(data.get("first_name") or data.get("firstName"))
    last_name  = _clean(data.get("last_name") or data.get("lastName"))
    email      = _clean(data.get("email"))
    phone      = _clean(data.get("phone"))
    coverageType      = _clean(data.get("coverageType") or data.get("coverage_type")) or None
    insuranceCoverage = _clean(data.get("insuranceCoverage") or data.get("insurance_coverage")) or None
    extra             = data.get("extra") or {}
    company           = _resolve_company(data)

    if not email and not phone:
        return Response({"detail": "At least one of email or phone is required."}, status=status.HTTP_400_BAD_REQUEST)

    # normaliza alguns aliases de formType
    if formType not in FORM_TYPES_SET:
        aliases = {"refer": "referral", "referral-friend": "referral", "refer-a-friend": "referral"}
        formType = aliases.get(formType, formType)
        if formType not in FORM_TYPES_SET:
            return Response({"detail": f"Invalid formType. Allowed: {sorted(FORM_TYPES_SET)}"}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        f = FormSubmission.objects.create(
            formType=formType,
            first_name=first_name or None,
            last_name=last_name or None,
            email=email or None,
            phone=phone or None,
            company=company,
            coverageType=coverageType,
            insuranceCoverage=insuranceCoverage,
            extra=extra,
        )

        # Aqui garantimos User + Profile (sem signals)
        user, prof = create_or_update_user_profile_from_form(
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
        # company pode vir por qualquer chave aceita
        maybe_company = _resolve_company(data)
        if maybe_company is not None:
            f.company = maybe_company
        f.save()
        return Response(serialize_form(f))

    f.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

class ProfileFormsAPIView(APIView):
    def post(self,request):
        create_form = Profile.objects.create(
            first_name=request.data['first_name'],
            last_name=request.data['last_name'],
            user_type_id=1

        )
        return Response()
