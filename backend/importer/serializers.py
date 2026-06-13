from rest_framework import serializers
from .models import ImportSession, ImportAnomaly


class ImportAnomalySerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportAnomaly
        fields = [
            'id', 'row_number', 'field', 'anomaly_type',
            'original_value', 'corrected_value', 'severity',
            'auto_resolved', 'user_action', 'description',
            'ai_description', 'related_row',
        ]


class ImportSessionSerializer(serializers.ModelSerializer):
    anomalies = ImportAnomalySerializer(many=True, read_only=True)

    class Meta:
        model = ImportSession
        fields = [
            'id', 'group', 'uploaded_by', 'filename', 'status',
            'total_rows', 'imported_rows', 'skipped_rows',
            'anomalies_count', 'anomalies', 'created_at', 'completed_at',
        ]
        read_only_fields = ['id', 'uploaded_by', 'created_at']


class ImportSessionListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views (no anomalies)."""
    class Meta:
        model = ImportSession
        fields = [
            'id', 'group', 'filename', 'status',
            'total_rows', 'imported_rows', 'skipped_rows',
            'anomalies_count', 'created_at', 'completed_at',
        ]


class ResolveAnomalySerializer(serializers.Serializer):
    anomaly_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=['approve', 'modify', 'skip'])
    corrected_value = serializers.CharField(required=False, allow_blank=True)
