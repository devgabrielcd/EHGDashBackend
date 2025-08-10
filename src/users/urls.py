from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

# from .views import ProfileListCreateAPIView, ProfileDetailAPIView, MyTokenObtainPairView
from .views import MyTokenObtainPairView

urlpatterns = [
    path('auth/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('profiles/', ProfileListCreateAPIView.as_view(), name='profile_list_create'),
    # path('profiles/<int:pk>/', ProfileDetailAPIView.as_view(), name='edit_profile'),
    path('api/', include('src.users.api.urls')),

]