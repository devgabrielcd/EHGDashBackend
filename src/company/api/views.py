from django.forms import model_to_dict
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView

from src.company.models import Company


class CompanyListAPIView(APIView):
    def get(self, request):
        company = Company.objects.all().values(
            'id', 'name', 'address', 'email', 'phone', 'website')
        print('company', company)
        return Response(company)

    def post(self, request):
        company = Company.objects.create(
            name=request.data.get('name'),
            address=request.data.get('address'),
            email=request.data.get('email'),
            phone=request.data.get('phone'),
            website=request.data.get('website')
        )
        company_data = model_to_dict(company, fields=['id', 'name', 'address', 'email', 'phone', 'website'])
        print('company', company_data)
        return Response(company_data)


class CompanyDetailsAPIView(APIView):
    def get(self, request, pk):
        company = Company.objects.filter(id=pk).first()
        if company:
            return Response(model_to_dict(company, fields=['id', 'name', 'address', 'email', 'phone', 'website']))
        raise Http404("Company not found")

    def put(self, request, pk):
        company = Company.objects.filter(id=pk).first()
        if company:
            company.name = request.data.get('name', company.name)
            company.address = request.data.get('address', company.address)
            company.email = request.data.get('email', company.email)
            company.phone = request.data.get('phone', company.phone)
            company.website = request.data.get('website', company.website)
            company.save()

            updated_data = model_to_dict(company, fields=['id', 'name', 'address', 'email', 'phone', 'website'])
            return Response(updated_data)
        raise Http404("Company not found")

    def delete(self, request, pk):
        company = Company.objects.filter(id=pk).first()
        if company:
            company.delete()
            return Response({"detail": "Company deleted successfully"})
        raise Http404("Company not found")