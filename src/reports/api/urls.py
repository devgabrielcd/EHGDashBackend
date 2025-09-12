from django.urls import path
from . import views

urlpatterns = [
    path("reports/", views.reports_list_create_api, name="reports-list-create"),
    path("reports/stats/", views.reports_stats_api, name="reports-stats"),
    path("report-types/", views.report_types_list_api, name="report-types"),
    path("reports/<uuid:pk>/", views.report_detail_api, name="report-detail"),
    path("reports/<uuid:pk>/export/", views.report_export_api, name="report-export"),
]
