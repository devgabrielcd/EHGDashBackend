from django.db.models import F
from django.forms import model_to_dict
from rest_framework.response import Response
from rest_framework.views import APIView

from src.company.models import Company
from src.sheets.models import SheetData


class SheetDataListAPIView(APIView):
    def get(self, request):
        company_param = request.query_params.get('company')

        if company_param:
            try:
                if company_param.isdigit():
                    company_obj = Company.objects.get(id=int(company_param))
                else:
                    company_obj = Company.objects.get(name__iexact=company_param)

                sheetsdata = SheetData.objects.filter(company=company_obj.id)
            except Company.DoesNotExist:
                return Response({'error': 'Empresa não encontrada.'}, status=404)
        else:
            sheetsdata = SheetData.objects.all()

        data = sheetsdata.values(
            'id', 'zipCode', 'coverageType', 'insuranceCoverage',
            'householdIncome', 'firstName', 'lastName', 'dob', 'address',
            'datetime', 'city', 'state', 'email', 'phone', 'company',
            'formType', 'referrerFirstName', 'referrerEmail',
            company_name=F('company__name')
        )
        return Response(data)

    def post(self, request):
        form_type = request.data.get('formType', 'homepage')
        sheet_data = SheetData.objects.create(
            zipCode=request.data.get('zipCode'),
            coverageType=request.data.get('coverageType'),
            insuranceCoverage=request.data.get('insuranceCoverage'),
            householdIncome=request.data.get('householdIncome'),
            firstName=request.data.get('firstName'),
            lastName=request.data.get('lastName'),
            dob=request.data.get('dob'),
            address=request.data.get('address'),
            datetime=request.data.get('datetime'),
            city=request.data.get('city'),
            state=request.data.get('state'),
            email=request.data.get('email'),
            phone=request.data.get('phone'),
            company_id=request.data.get('company'),
            formType=form_type,
            # NOVOS CAMPOS PARA O INDICADOR
            referrerFirstName=request.data.get('referrerFirstName', ''),
            referrerEmail=request.data.get('referrerEmail', ''),

        )
        sheet_data_dict = model_to_dict(sheet_data)
        sheet_data_dict['company_name'] = sheet_data.company.name if sheet_data.company else None
        # Opcional: Adicione os campos do indicador no retorno se precisar no frontend
        sheet_data_dict['referrerFirstName'] = sheet_data.referrerFirstName
        sheet_data_dict['referrerEmail'] = sheet_data.referrerEmail
        return Response(sheet_data_dict)
