from django.contrib import admin
from .models import ImportSession, ImportAnomaly


class ImportAnomalyInline(admin.TabularInline):
    model = ImportAnomaly
    extra = 0
    readonly_fields = ('row_number', 'anomaly_type', 'severity', 'original_value')


@admin.register(ImportSession)
class ImportSessionAdmin(admin.ModelAdmin):
    list_display = ('filename', 'group', 'status', 'total_rows', 'anomalies_count', 'created_at')
    list_filter = ('status',)
    inlines = [ImportAnomalyInline]


@admin.register(ImportAnomaly)
class ImportAnomalyAdmin(admin.ModelAdmin):
    list_display = ('import_session', 'row_number', 'anomaly_type', 'severity', 'user_action')
    list_filter = ('severity', 'anomaly_type', 'user_action')
