from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework import serializers
from .models import Company


# Listar todas as empresas
class CompanyListView(APIView):
    def get(self, request, *args, **kwargs):
        companies = Company.objects.all()  # Obtém todas as empresas

        # Serializa as empresas diretamente aqui
        company_data = [{
            'id': company.id,
            'name': company.name,
            'address': company.address,
            'phone': company.phone
        } for company in companies]

        return Response(company_data)  # Retorna os dados serializados


# Criar uma nova empresa
class CompanyCreateView(APIView):
    def post(self, request, *args, **kwargs):
        # Serializa os dados diretamente no corpo da view
        company_serializer = {
            'name': request.data.get('name'),
            'address': request.data.get('address'),
            'phone': request.data.get('phone')
        }

        # Cria a empresa
        if company_serializer['name'] and company_serializer['address'] and company_serializer['phone']:
            company = Company.objects.create(**company_serializer)
            return Response(company_serializer, status=status.HTTP_201_CREATED)  # Retorna a empresa criada
        return Response({'error': 'Dados inválidos'}, status=status.HTTP_400_BAD_REQUEST)  # Retorna erro de validação


# Detalhes, atualização e exclusão de uma empresa específica
class CompanyDetailView(APIView):
    def get_object(self, pk):
        try:
            return Company.objects.get(pk=pk)  # Busca a empresa pelo ID
        except Company.DoesNotExist:
            raise NotFound("Empresa não encontrada")  # Retorna um erro 404 se não encontrar

    def get(self, request, pk, *args, **kwargs):
        company = self.get_object(pk)  # Obtém a empresa
        # Serializa a empresa diretamente aqui
        company_data = {
            'id': company.id,
            'name': company.name,
            'address': company.address,
            'phone': company.phone
        }
        return Response(company_data)  # Retorna os dados serializados

    def put(self, request, pk, *args, **kwargs):
        company = self.get_object(pk)  # Obtém a empresa
        # Atualiza os dados da empresa
        company.name = request.data.get('name', company.name)
        company.address = request.data.get('address', company.address)
        company.phone = request.data.get('phone', company.phone)
        company.save()

        # Retorna os dados atualizados
        company_data = {
            'id': company.id,
            'name': company.name,
            'address': company.address,
            'phone': company.phone
        }
        return Response(company_data)  # Retorna os dados atualizados

    def delete(self, request, pk, *args, **kwargs):
        company = self.get_object(pk)  # Obtém a empresa
        company.delete()  # Deleta a empresa
        return Response(status=status.HTTP_204_NO_CONTENT)  # Retorna resposta sem conteúdo
