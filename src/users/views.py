from django.shortcuts import redirect

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Profile


# def _users_counter():  # Static paramenters, need to make dinamic
#     users_counter = {
#         'customers': len(Profile.objects.filter(user_type__user_type='Customer')),
#         'agents': len(Profile.objects.filter(user_type__user_type='Agent')),
#         'managers':  len(Profile.objects.filter(user_type__user_type='Manager')),
#         'employees': len(Profile.objects.filter(user_type__user_type='Employee')),
#     }
#
#     return users_counter
#
#
# def theme(request):
#
#     profile_get = Profile.objects.filter(user=request.user).first()
#
#     if profile_get.theme == 'light':
#         profile_get.theme = 'dark'
#         profile_get.save()
#     elif profile_get.theme == 'dark':
#         profile_get.theme = 'light'
#         profile_get.save()
#
#     return redirect('dashboard')


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        """
        #  ADD Extra fields to the JWT token to user identification
        :param attrs:
        :return:
        """

        # The default result (access/refresh tokens)
        data = super(MyTokenObtainPairSerializer, self).validate(attrs)
        print(data)
        profile_qs = Profile.objects.filter(user__id=self.user.id).first()

        # Added id of user to token package
        data.update({'id': self.user.profile.id, 'user_type': profile_qs.user_type.id, 'user_role': profile_qs.user_role.id})

        return data


class MyTokenObtainPairView(TokenObtainPairView):

    serializer_class = MyTokenObtainPairSerializer

# https://stackoverflow.com/questions/53480770/how-to-return-custom-data-with-access-and-refresh-tokens-to-identify-users-in-dj


class LogoutView(APIView):  # Test it better, responding 200 but the next still logged
    def post(self, request):
        try:
            print('aquiohhhh')
            # Deleting the tokens on the client side
            response = Response({'success': 'User successfully logged out.'}, status=status.HTTP_200_OK)
            print('response:', response)
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
            return response
        except Exception as e:
            return Response({'error': 'Failed to log out.'}, status=status.HTTP_400_BAD_REQUEST)