from django.contrib import admin
from .models import ImportSession, ImportAnomaly


@admin.register(ImportSession)
class ImportSessionAdmin(admin.ModelAdmin):
    list_display = ['filename', 'group', 'status', 'total_rows', 'imported_rows',
                    'skipped_rows', 'anomalies_count', 'created_at']
    list_filter = ['status', 'group']
    search_fields = ['filename']
    readonly_fields = ['raw_data']


@admin.register(ImportAnomaly)
class ImportAnomalyAdmin(admin.ModelAdmin):
    list_display = ['import_session', 'row_number', 'anomaly_type', 'severity',
                    'user_action', 'auto_resolved']
    list_filter = ['severity', 'anomaly_type', 'user_action', 'auto_resolved']
    search_fields = ['description', 'original_value']
