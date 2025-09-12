# reports/admin.py
from django.contrib import admin, messages
from django.utils.html import format_html
from django.http import HttpResponse
from django.utils import timezone

from .models import Report

# Tenta usar um widget JSON mais amigável (opcional)
try:
    from django_json_widget.widgets import JSONEditorWidget  # pip install django-json-widget
    from django.db.models import JSONField
    HAS_JSON_WIDGET = True
except Exception:
    HAS_JSON_WIDGET = False
    JSONField = None
    JSONEditorWidget = None


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "status", "owner", "updated_at", "created_at", "open_in_app")
    list_display_links = ("name",)
    list_filter = ("status", "type", "owner", ("updated_at", admin.DateFieldListFilter), ("created_at", admin.DateFieldListFilter))
    search_fields = ("name", "type", "owner__username", "owner__email")
    ordering = ("-updated_at",)
    list_per_page = 25
    date_hierarchy = "updated_at"
    autocomplete_fields = ("owner",)
    readonly_fields = ("created_at", "updated_at")

    # >>> IMPORTANTE: aqui precisa ser um DICT, não um método <<<
    if HAS_JSON_WIDGET:
        formfield_overrides = {JSONField: {"widget": JSONEditorWidget}}
    else:
        formfield_overrides = {}

    actions = ["mark_ready", "mark_processing", "mark_failed", "duplicate_reports", "export_selected_csv"]

    def open_in_app(self, obj: Report):
        url = f"/dashboard/reports/{obj.pk}"
        return format_html('<a href="{}" target="_blank">Open</a>', url)
    open_in_app.short_description = "Open in app"

    @admin.action(description="Mark selected as Ready")
    def mark_ready(self, request, queryset):
        updated = queryset.update(status=Report.Status.READY, updated_at=timezone.now())
        self.message_user(request, f"{updated} report(s) updated to Ready.", messages.SUCCESS)

    @admin.action(description="Mark selected as Processing")
    def mark_processing(self, request, queryset):
        updated = queryset.update(status=Report.Status.PROCESSING, updated_at=timezone.now())
        self.message_user(request, f"{updated} report(s) updated to Processing.", messages.SUCCESS)

    @admin.action(description="Mark selected as Failed")
    def mark_failed(self, request, queryset):
        updated = queryset.update(status=Report.Status.FAILED, updated_at=timezone.now())
        self.message_user(request, f"{updated} report(s) updated to Failed.", messages.SUCCESS)

    @admin.action(description="Duplicate selected reports")
    def duplicate_reports(self, request, queryset):
        count = 0
        for r in queryset:
            r.pk = None
            r.name = f"{r.name} (Copy)"
            r.status = Report.Status.DRAFT
            r.save()
            count += 1
        self.message_user(request, f"{count} copy(ies) created as Draft.", messages.SUCCESS)

    @admin.action(description="Export selected to CSV")
    def export_selected_csv(self, request, queryset):
        import csv
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="reports.csv"'
        writer = csv.writer(resp)
        writer.writerow(["id", "name", "type", "status", "owner", "updated_at", "created_at"])
        for r in queryset.select_related("owner"):
            writer.writerow([
                r.pk,
                r.name,
                r.type,
                r.status,
                getattr(r.owner, "username", None) or getattr(r.owner, "email", None),
                r.updated_at.isoformat() if r.updated_at else "",
                r.created_at.isoformat() if r.created_at else "",
            ])
        return resp
