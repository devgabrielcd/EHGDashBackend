# src/analytics/api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("revenue_series/", views.revenue_series, name="analytics_revenue_series"),
    path("users_product_mix/", views.users_product_mix, name="analytics_users_product_mix"),
    path("top_entities/", views.top_entities, name="analytics_top_entities"),
    path("activity_feed/", views.activity_feed, name="analytics_activity_feed"),

]
