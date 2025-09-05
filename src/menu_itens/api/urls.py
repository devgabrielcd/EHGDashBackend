from django.urls import path
from .views import SidebarView

app_name = "menu_itens_api"

urlpatterns = [
    path("sidebar/", SidebarView.as_view(), name="sidebar"),
]
