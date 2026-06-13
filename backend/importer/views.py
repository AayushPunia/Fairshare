import json
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import ImportSession, ImportAnomaly
from .serializers import (
    ImportSessionSerializer, ImportSessionListSerializer,
    ImportAnomalySerializer, ResolveAnomalySerializer,
)
from .parser import parse_csv_file
from .analyzer import analyze_rows
from .importer import commit_import
from .ai_service import enhance_all_anomalies, categorize_expense
from groups.models import Group


class ImportUploadView(APIView):
    """
    POST: Upload a CSV file and run Phase 1 (parse) + Phase 2 (analyze).
    Returns the import session with detected anomalies for user review.
    """
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        csv_file = request.FILES.get('file')
        group_id = request.data.get('group_id')

        if not csv_file:
            return Response(
                {'error': 'No file uploaded'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not group_id:
            return Response(
                {'error': 'group_id is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return Response(
                {'error': 'Group not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Read file content
        file_content = csv_file.read().decode('utf-8-sig')  # Handle BOM

        # Phase 1: Parse and normalize
        rows, parser_anomalies = parse_csv_file(file_content)

        # Phase 2: Analyze for business logic issues
        analyzer_anomalies = analyze_rows(rows)

        # Combine all anomalies
        all_anomalies = parser_anomalies + analyzer_anomalies

        # Try to enhance with AI (non-blocking)
        try:
            all_anomalies = enhance_all_anomalies(all_anomalies, rows)
        except Exception:
            pass  # AI enhancement is optional

        # Create import session
        session = ImportSession.objects.create(
            group=group,
            uploaded_by=request.user,
            filename=csv_file.name,
            status='reviewing',
            raw_data=[_serialize_row(r) for r in rows],
            total_rows=len(rows),
            anomalies_count=len(all_anomalies),
        )

        # Create anomaly records
        for anomaly in all_anomalies:
            ImportAnomaly.objects.create(
                import_session=session,
                row_number=anomaly['row_number'],
                field=anomaly['field'],
                anomaly_type=anomaly['anomaly_type'],
                original_value=anomaly['original_value'],
                corrected_value=anomaly.get('corrected_value', ''),
                severity=anomaly['severity'],
                auto_resolved=anomaly.get('auto_resolved', False),
                user_action='auto_fixed' if anomaly.get('auto_resolved') else 'pending',
                description=anomaly['description'],
                ai_description=anomaly.get('ai_description', ''),
                related_row=anomaly.get('related_row'),
            )

        return Response(
            ImportSessionSerializer(session).data,
            status=status.HTTP_201_CREATED,
        )


class ImportSessionDetailView(APIView):
    """GET: Get import session details with anomalies."""

    def get(self, request, session_id):
        try:
            session = ImportSession.objects.prefetch_related('anomalies').get(id=session_id)
        except ImportSession.DoesNotExist:
            return Response(
                {'error': 'Import session not found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ImportSessionSerializer(session).data)


class ImportResolveView(APIView):
    """
    POST: Resolve anomalies — user approves, modifies, or skips each one.
    This is Meera's requirement: "I want to approve anything the app deletes or changes."
    """

    def post(self, request, session_id):
        try:
            session = ImportSession.objects.get(id=session_id)
        except ImportSession.DoesNotExist:
            return Response(
                {'error': 'Import session not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        resolutions = request.data.get('resolutions', [])

        for resolution in resolutions:
            serializer = ResolveAnomalySerializer(data=resolution)
            serializer.is_valid(raise_exception=True)
            vd = serializer.validated_data

            try:
                anomaly = ImportAnomaly.objects.get(
                    id=vd['anomaly_id'],
                    import_session=session,
                )
            except ImportAnomaly.DoesNotExist:
                continue

            action = vd['action']
            if action == 'approve':
                anomaly.user_action = 'user_approved'
            elif action == 'modify':
                anomaly.user_action = 'user_modified'
                anomaly.corrected_value = vd.get('corrected_value', anomaly.corrected_value)
            elif action == 'skip':
                anomaly.user_action = 'skipped'

            anomaly.save()

        return Response({'status': 'ok'})


class ImportConfirmView(APIView):
    """
    POST: Confirm import — commit all resolved data to the database.
    Only works if all critical anomalies have been resolved.
    """

    def post(self, request, session_id):
        try:
            session = ImportSession.objects.get(id=session_id)
        except ImportSession.DoesNotExist:
            return Response(
                {'error': 'Import session not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check for unresolved critical anomalies
        unresolved_critical = session.anomalies.filter(
            severity='critical',
            user_action='pending',
        ).count()

        if unresolved_critical > 0:
            return Response(
                {'error': f'{unresolved_critical} critical anomalies must be resolved before confirming import.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Build resolved rows from raw_data + anomaly resolutions
        raw_rows = session.raw_data
        anomalies = session.anomalies.all()

        # Determine which rows to skip
        skipped_rows = set()
        settlement_rows = set()

        for anomaly in anomalies:
            if anomaly.user_action == 'skipped':
                skipped_rows.add(anomaly.row_number)
            elif anomaly.anomaly_type == 'duplicate' and anomaly.user_action in ('user_approved', 'auto_fixed'):
                skipped_rows.add(anomaly.row_number)  # Skip the duplicate
            elif anomaly.anomaly_type == 'settlement_as_expense' and anomaly.user_action != 'skipped':
                settlement_rows.add(anomaly.row_number)
            elif anomaly.anomaly_type == 'zero_amount' and anomaly.user_action == 'user_approved':
                skipped_rows.add(anomaly.row_number)

        # Build final rows
        resolved_rows = []
        for row in raw_rows:
            row_num = row.get('row_number', 0)

            if row_num in skipped_rows:
                row['action'] = 'skip'
            elif row_num in settlement_rows:
                row['action'] = 'settlement'
            else:
                row['action'] = 'import'

            resolved_rows.append(row)

        # Commit to database
        stats = commit_import(session_id, resolved_rows)

        return Response({
            'status': 'completed',
            'stats': stats,
        })


class ImportReportView(APIView):
    """
    GET: Get the full import report — all anomalies and their resolutions.
    This is the deliverable "Import report produced by your app when it ingests the CSV."
    """

    def get(self, request, session_id):
        try:
            session = ImportSession.objects.prefetch_related('anomalies').get(id=session_id)
        except ImportSession.DoesNotExist:
            return Response(
                {'error': 'Import session not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        anomalies = session.anomalies.all().order_by('row_number')

        report = {
            'session': {
                'id': session.id,
                'filename': session.filename,
                'status': session.status,
                'total_rows': session.total_rows,
                'imported_rows': session.imported_rows,
                'skipped_rows': session.skipped_rows,
                'anomalies_count': session.anomalies_count,
                'uploaded_at': session.created_at.isoformat() if session.created_at else None,
                'completed_at': session.completed_at.isoformat() if session.completed_at else None,
            },
            'summary': {
                'info': anomalies.filter(severity='info').count(),
                'warning': anomalies.filter(severity='warning').count(),
                'error': anomalies.filter(severity='error').count(),
                'critical': anomalies.filter(severity='critical').count(),
                'auto_fixed': anomalies.filter(auto_resolved=True).count(),
                'user_resolved': anomalies.filter(
                    user_action__in=['user_approved', 'user_modified']
                ).count(),
                'skipped': anomalies.filter(user_action='skipped').count(),
            },
            'anomalies': ImportAnomalySerializer(anomalies, many=True).data,
        }

        return Response(report)


def _serialize_row(row):
    """Convert a parsed row to JSON-serializable format."""
    serialized = {}
    for key, value in row.items():
        if hasattr(value, 'as_tuple'):  # Decimal
            serialized[key] = str(value)
        elif isinstance(value, dict):
            serialized[key] = {k: str(v) if hasattr(v, 'as_tuple') else v for k, v in value.items()}
        else:
            serialized[key] = value
    return serialized
