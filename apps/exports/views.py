import ast
import json
from datetime import date, datetime, time
from pathlib import Path
from urllib.parse import unquote, urlparse

import openpyxl
from django.conf import settings
from django.http import FileResponse
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import permissions, response, serializers, status, views, viewsets

from apps.calllogs.models import CallLog
from apps.common.utils import apply_branch_filter
from .models import ExportJob
from .serializers import ExportJobSerializer


EXPORT_MEDIA_DIR = "exports"
CALL_LOG_HEADERS = ['Type', 'Number', 'Duration (s)', 'SIM Slot', 'Branch Group', 'Branch', 'Time']
EXPORT_QUERY_CHUNK_SIZE = 10000


def _export_dir() -> Path:
    path = Path(settings.MEDIA_ROOT) / EXPORT_MEDIA_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _media_url_for(filename: str) -> str:
    return f"{settings.MEDIA_URL.rstrip('/')}/{EXPORT_MEDIA_DIR}/{filename}"


def _safe_export_path(filename: str | None) -> Path | None:
    if not filename:
        return None
    safe_name = Path(unquote(filename).replace("\\", "/")).name
    if not safe_name:
        return None
    return (_export_dir() / safe_name).resolve()


def _path_from_file_url(file_url: str | None) -> Path | None:
    if not file_url:
        return None

    media_path = urlparse(file_url).path or file_url
    media_prefix = urlparse(settings.MEDIA_URL).path.rstrip('/') + '/'
    if not media_path.startswith(media_prefix):
        return None

    relative_path = unquote(media_path[len(media_prefix):].lstrip('/')).replace('\\', '/')
    path = (Path(settings.MEDIA_ROOT) / Path(*Path(relative_path).parts)).resolve()
    export_root = _export_dir().resolve()
    if export_root not in path.parents and path != export_root:
        return None
    return path


def _json_filters(data) -> str:
    return json.dumps({
        'branch': data.get('branch') or None,
        'group': data.get('group') or None,
        'start_date': data.get('start_date') or None,
        'end_date': data.get('end_date') or None,
    })


def _load_filters(job: ExportJob) -> dict:
    if not job.error_message:
        return {}
    try:
        return json.loads(job.error_message)
    except (TypeError, ValueError, json.JSONDecodeError):
        try:
            return ast.literal_eval(job.error_message)
        except (SyntaxError, ValueError):
            return {}


def _delete_export_file(job: ExportJob) -> bool:
    file_path = _path_from_file_url(job.file_url) or _safe_export_path(job.file_name)
    if file_path and file_path.exists():
        file_path.unlink()
        return True
    return False


def _parse_filter_date(value, boundary: time):
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, boundary)
    else:
        try:
            parsed = datetime.combine(date.fromisoformat(str(value)), boundary)
        except ValueError:
            return None

    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _call_log_queryset(user, filters: dict):
    queryset = CallLog.objects.all().order_by()
    queryset = apply_branch_filter(queryset, "branch_id", user)

    branch = filters.get('branch')
    group = filters.get('group')
    start_date = filters.get('start_date')
    end_date = filters.get('end_date')

    if branch:
        queryset = queryset.filter(branch_id=branch)
    elif group:
        queryset = queryset.filter(branch__branch_group_id=group)

    start_at = _parse_filter_date(start_date, time.min)
    end_at = _parse_filter_date(end_date, time.max)
    if start_at:
        queryset = queryset.filter(call_time__gte=start_at)
    if end_at:
        queryset = queryset.filter(call_time__lte=end_at)

    return queryset.values_list(
        'call_type',
        'phone_number',
        'duration',
        'sim_slot',
        'branch__branch_group__name',
        'branch__spa_name',
        'call_time',
    )


def _write_call_logs_xlsx(user, filters: dict, file_path: Path) -> None:
    workbook = openpyxl.Workbook(write_only=True)
    worksheet = workbook.create_sheet(title="Call Logs")
    worksheet.append(CALL_LOG_HEADERS)

    for call_type, phone_number, duration, sim_slot, group_name, branch_name, call_time in _call_log_queryset(user, filters).iterator(chunk_size=EXPORT_QUERY_CHUNK_SIZE):
        worksheet.append([
            call_type,
            phone_number,
            duration,
            sim_slot,
            group_name or "N/A",
            branch_name or "N/A",
            call_time.strftime("%d/%m/%Y %H:%M:%S") if call_time else "",
        ])

    workbook.save(file_path)


def _build_export_file(job: ExportJob, user) -> ExportJob:
    if job.export_type != 'call_logs':
        raise ValueError(f"Unsupported export type: {job.export_type}")

    filters = _load_filters(job)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = Path(job.file_name or f"call_logs_{job.id}_{timestamp}.xlsx").name
    if not filename.lower().endswith('.xlsx'):
        filename = f"{filename}.xlsx"

    file_path = _safe_export_path(filename)
    if file_path is None:
        raise ValueError("Invalid export filename")
    _write_call_logs_xlsx(user, filters, file_path)

    job.file_name = filename
    job.file_url = _media_url_for(filename)
    job.status = 'completed'
    job.save(update_fields=['file_name', 'file_url', 'status', 'updated_at'])
    return job


class ExportViewSet(viewsets.ModelViewSet):
    serializer_class = ExportJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ExportJob.objects.select_related('user').all().order_by('-created_at')
        user = self.request.user
        if getattr(user, "role", None) in ["area_manager", "spa_manager"]:
            return queryset.filter(user=user)
        return queryset

    @extend_schema(summary="List Export Jobs")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Retrieve Export Job")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Delete Export Job")
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        _delete_export_file(instance)
        instance.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)


class GenerateExportView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Generate Export",
        description="Initiates an Excel export for call logs or other data types.",
        request=inline_serializer(
            name="GenerateExportRequest",
            fields={
                "type": serializers.CharField(default="call_logs"),
                "branch": serializers.UUIDField(required=False),
                "group": serializers.UUIDField(required=False),
                "start_date": serializers.DateField(required=False),
                "end_date": serializers.DateField(required=False),
            }
        ),
        responses={201: ExportJobSerializer}
    )
    def post(self, request):
        export_type = request.data.get('type', 'call_logs')
        job = ExportJob.objects.create(
            user=request.user,
            export_type=export_type,
            status='processing',
            error_message=_json_filters(request.data),
        )

        try:
            if export_type != 'call_logs':
                job.status = 'failed'
                job.error_message = f"Unsupported export type: {export_type}"
                job.save(update_fields=['status', 'error_message', 'updated_at'])
                return response.Response({"error": "Unsupported type"}, status=status.HTTP_400_BAD_REQUEST)

            job = _build_export_file(job, request.user)
            return response.Response(ExportJobSerializer(job).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
            job.save(update_fields=['status', 'error_message', 'updated_at'])
            return response.Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DownloadExportView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Download Export File",
        description="Returns the generated Excel file for a completed export job.",
        responses={
            200: OpenApiResponse(
                description="The generated Excel file (.xlsx)",
                response=bytes,
            )
        }
    )
    def get(self, request, pk):
        try:
            job_qs = ExportJob.objects.all()
            if getattr(request.user, "role", None) in ["area_manager", "spa_manager"]:
                job_qs = job_qs.filter(user=request.user)
            job = job_qs.get(pk=pk)

            if job.status != 'completed':
                return response.Response({"error": "Export not ready"}, status=status.HTTP_400_BAD_REQUEST)

            file_path = _path_from_file_url(job.file_url)
            if file_path is None or not file_path.exists():
                job = _build_export_file(job, request.user)
                file_path = _path_from_file_url(job.file_url) or _safe_export_path(job.file_name)

            if file_path is None or not file_path.exists():
                return response.Response({"error": "Export file could not be generated"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return FileResponse(
                open(file_path, 'rb'),
                as_attachment=True,
                filename=job.file_name or file_path.name,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
        except ExportJob.DoesNotExist:
            return response.Response({"error": "Export job not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return response.Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteExportView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Delete Export Job",
        description="Deletes an export job and its associated file.",
        responses={
            204: OpenApiResponse(description="Export job deleted successfully"),
            404: OpenApiResponse(description="Export job not found"),
        }
    )
    def delete(self, request, pk):
        try:
            job_qs = ExportJob.objects.all()
            if getattr(request.user, "role", None) in ["area_manager", "spa_manager"]:
                job_qs = job_qs.filter(user=request.user)
            job = job_qs.get(pk=pk)

            _delete_export_file(job)
            job.delete()
            return response.Response(status=status.HTTP_204_NO_CONTENT)
        except ExportJob.DoesNotExist:
            return response.Response({"error": "Export job not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return response.Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

        
