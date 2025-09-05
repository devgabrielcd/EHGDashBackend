from django.http import JsonResponse
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from src.users.api.serializers import EmployeeSerializer
from src.users.models import Profile



@permission_classes([IsAuthenticated])
def detail_user_api(request, pk):  # REPLACE THIS
    data = Profile.objects.filter(id=pk).first()
    serializer = EmployeeSerializer(data)
    return JsonResponse({'user': serializer.data})


class DetailUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # Obtém o perfil do usuário pelo ID ou retorna 404 se não encontrado
        profile = get_object_or_404(Profile, id=pk)
        serializer = EmployeeSerializer(profile)
        return Response({'user': serializer.data})
