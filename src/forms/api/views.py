# src/forms/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from src.forms.models import FormSubmission

# Lista de campos que serão incluídos nas respostas GET e na atualização PATCH.
# Deve corresponder exatamente aos campos do seu FormSubmission model.
FORM_SUBMISSION_FIELDS = (
    "id",
    "formType",
    "first_name",
    "last_name",
    "email",
    "phone",
    "zipCode",
    "coverageType",
    "insuranceCoverage",
    "householdIncome",
    "dob",
    "address",
    "city",
    "state",
    "referrerFirstName",
    "referrerEmail",
    "created_at",
    "company_id",
    "profile_id",
)


class FormSubmissionAPIView(APIView):
    """
    Lida com a listagem (GET) e criação (POST) de FormSubmission.
    """

    def get(self, request):
        """Lista os 200 submissions mais recentes."""
        forms = (
            FormSubmission.objects
            .all()
            .order_by("-id")
            .values(*FORM_SUBMISSION_FIELDS)  # Usa a lista de campos definida
            [:200]
        )
        return Response(list(forms))

    def post(self, request):
        """Cria um novo FormSubmission com todos os dados de formulário."""
        data = request.data

        # O .create() recebe diretamente os dados do request.data
        FormSubmission.objects.create(
            formType=data.get("formType"),
            company_id=data.get("company_id"),

            # Dados do Cliente/Referido
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            email=data.get("email"),
            phone=data.get("phone"),

            # Dados de Cobertura e Renda
            zipCode=data.get("zipCode"),
            coverageType=data.get("coverageType"),
            insuranceCoverage=data.get("insuranceCoverage"),
            householdIncome=data.get("householdIncome"),

            # Dados Pessoais e Endereço
            dob=data.get("dob"),
            address=data.get("address"),
            city=data.get("city"),
            state=data.get("state"),

            # Dados do Indicador (Referrer)
            referrerFirstName=data.get("referrerFirstName"),
            referrerEmail=data.get("referrerEmail"),

            # O profile_id não é recebido no POST de frontend, mas mantido para integridade
            # profile_id=data.get("profile_id"),
        )
        return Response(status=201)  # Retorna 201 Created para sucesso


class FormSubmissionDetailAPIView(APIView):
    """
    Lida com detalhe (GET), atualização (PATCH) e exclusão (DELETE) de FormSubmission.
    """

    def get(self, request, pk):
        """Retorna os detalhes de um único FormSubmission."""
        f = get_object_or_404(FormSubmission, pk=pk)

        # Converte o objeto do modelo para um dicionário usando os campos definidos
        data = {field: getattr(f, field) for field in FORM_SUBMISSION_FIELDS}
        return Response(data)

    def patch(self, request, pk):
        """Atualiza campos específicos de um FormSubmission."""

        # Campos que podem ser atualizados (todos os campos de dados)
        updatable_fields = list(FORM_SUBMISSION_FIELDS)
        updatable_fields.remove("id")
        updatable_fields.remove("created_at")

        payload = {k: request.data[k] for k in updatable_fields if k in request.data}

        # Garante que 'company_id' possa ser atualizado (se vier no request)
        if "company_id" in request.data:
            payload["company_id"] = request.data["company_id"]

        # Atualiza o registro no banco de dados
        FormSubmission.objects.filter(pk=pk).update(**payload)
        return Response()

    def delete(self, request, pk):
        """Exclui um FormSubmission."""
        get_object_or_404(FormSubmission, pk=pk).delete()
        return Response(status=204)  # Retorna 204 No Content para exclusão bem-sucedida