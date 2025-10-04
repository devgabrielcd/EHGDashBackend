# src/forms/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from src.forms.models import FormSubmission

class FormSubmissionAPIView(APIView):
    # Lista bem simples (até 200) ou cria um registro novo
    def get(self, request):
        forms = (
            FormSubmission.objects
            .all()
            .order_by("-id")
            .values(
                "id","formType","first_name","last_name","email","phone",
                "coverageType","insuranceCoverage","extra","created_at",
                "company_id","profile_id"
            )[:200]
        )
        return Response(list(forms))

    def post(self, request):
        FormSubmission.objects.create(
            formType=request.data.get("formType"),
            first_name=request.data.get("first_name"),
            last_name=request.data.get("last_name"),
            email=request.data.get("email"),
            phone=request.data.get("phone"),
            coverageType=request.data.get("coverageType"),
            insuranceCoverage=request.data.get("insuranceCoverage"),
            extra=request.data.get("extra", {}),
            company_id=request.data.get("company_id"),  # aceita ID direto
        )
        return Response()  # mesmo estilo do exemplo


class FormSubmissionDetailAPIView(APIView):
    # GET/PATCH/DELETE ultra enxutos
    def get(self, request, pk):
        f = get_object_or_404(FormSubmission, pk=pk)
        data = {
            "id": f.id,
            "formType": f.formType,
            "first_name": f.first_name,
            "last_name": f.last_name,
            "email": f.email,
            "phone": f.phone,
            "coverageType": f.coverageType,
            "insuranceCoverage": f.insuranceCoverage,
            "extra": f.extra,
            "created_at": f.created_at,
            "company_id": f.company_id,
            "profile_id": f.profile_id,
        }
        return Response(data)

    def patch(self, request, pk):
        fields = [
            "formType","first_name","last_name","email","phone",
            "coverageType","insuranceCoverage","extra"
        ]
        payload = {k: request.data[k] for k in fields if k in request.data}
        if "company_id" in request.data:
            payload["company_id"] = request.data["company_id"]

        # Atualiza sem carregar tudo em memória
        FormSubmission.objects.filter(pk=pk).update(**payload)
        return Response()

    def delete(self, request, pk):
        get_object_or_404(FormSubmission, pk=pk).delete()
        return Response(status=204)
