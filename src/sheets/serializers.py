# serializers.py
from rest_framework import serializers
from .models import SheetData
from src.company.models import Company

class SheetDataSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        allow_null=True,
        required=False
    )  # Garante que company é um ID

    class Meta:
        model = SheetData
        fields = [
            'id', 'zipCode', 'coverageType', 'insuranceCoverage',
            'householdIncome', 'firstName', 'lastName', 'dob', 'address',
            'datetime', 'city', 'state', 'email', 'phone', 'company'
        ]
        read_only_fields = ['datetime']