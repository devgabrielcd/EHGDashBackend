from rest_framework import serializers
from src.users.models import Profile


class ProfileSerializer(serializers.ModelSerializer):

    user = serializers.ReadOnlyField(source='user.user.username')
    user_type = serializers.CharField(source="user_type.user_type", allow_null=True)
    user_role = serializers.CharField(source="user_role.user_role", allow_null=True)

    class Meta:
        model = Profile
        fields = [
            "id", "user_type", "user_role", "first_name", "middle_name", "last_name",
            "phone_number", "phone_number_type", "email", "date_of_birth", "signed_date", "image"
        ]

class EmployeeSerializer(serializers.ModelSerializer):
    user_type = serializers.ReadOnlyField(source='user_type.user_type')  # Obtém o valor do campo relacionado
    user_role = serializers.ReadOnlyField(source='user_role.user_role')  # Obtém o valor do campo relacionado
    user_role_id = serializers.ReadOnlyField(source='user_role.id')  # Obtém o ID do UserRole
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Profile
        fields = '__all__'
