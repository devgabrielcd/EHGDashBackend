# forms/api/views.py
from django.forms.models import model_to_dict
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from src.forms.models import FormSubmission
from src.company.models import Company


def serialize_form(f: FormSubmission) -> dict:
    """Serializer simples para FormSubmission usando model_to_dict"""
    base = model_to_dict(
        f,
        fields=["id", "formType", "first_name", "last_name", "email", "phone", "created_at"],
    )
    base["company"] = f.company.name if f.company else None
    base["company_id"] = f.company_id
    base["user_id"] = f.user_id
    return base


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def form_list_create_api(request):
    if request.method == "GET":
        qs = FormSubmission.objects.select_related("company").order_by("-created_at")

        company = request.query_params.get("company")
        if company:
            qs = qs.filter(company__id=company)

        formType = request.query_params.get("formType")
        if formType:
            qs = qs.filter(formType__iexact=formType)

        out = [serialize_form(f) for f in qs[:200]]
        return Response(out)

    # POST
    data = request.data or {}
    f = FormSubmission(
        formType=data.get("formType"),
        email=data.get("email"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        phone=data.get("phone"),
        user_id=data.get("user_id"),
        company=Company.objects.filter(id=data.get("company_id")).first()
        if data.get("company_id")
        else None,
    )
    f.save()
    return Response(serialize_form(f), status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def form_detail_api(request, pk):
    f = get_object_or_404(FormSubmission, pk=pk)

    if request.method == "GET":
        return Response(serialize_form(f))

    if request.method == "PATCH":
        data = request.data or {}
        for field in ["formType", "email", "first_name", "last_name", "phone", "extra"]:
            if field in data:
                setattr(f, field, data[field])
        if "company_id" in data:
            f.company_id = data["company_id"]
        if "user_id" in data:
            f.user_id = data["user_id"]

        f.save()
        return Response(serialize_form(f))

    f.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
