from rest_framework import viewsets, permissions, views, response, status, serializers
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer, OpenApiResponse
from .models import ExportJob
from .serializers import ExportJobSerializer
from apps.calllogs.models import CallLog
from django.http import HttpResponse
from django.utils import timezone
import openpyxl
from openpyxl.styles import Font
import io
from apps.common.utils import apply_branch_filter

class ExportViewSet(viewsets.ModelViewSet):
    serializer_class = ExportJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ExportJob.objects.all().order_by('-created_at')
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
        return super().destroy(request, *args, **kwargs)

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
        
        # Create the job record
        # Store filters in error_message or a JSON field (simplified for now by just using query parameters in re-generation)
        job = ExportJob.objects.create(
            user=request.user,
            export_type=export_type,
            status='processing',
            # We use error_message as a temporary storage for filters as JSON string to avoid migration
            error_message=str({
                'branch': request.data.get('branch'),
                'group': request.data.get('group'),
                'start_date': request.data.get('start_date'),
                'end_date': request.data.get('end_date'),
            })
        )
        
        try:
            if export_type == 'call_logs':
                # Generate Excel synchronously for now as requested
                queryset = CallLog.objects.all().select_related('branch', 'device').order_by('-call_time')
                queryset = apply_branch_filter(queryset, "branch_id", request.user)
                
                # Apply filters
                branch = request.data.get('branch')
                group = request.data.get('group')
                start_date = request.data.get('start_date')
                end_date = request.data.get('end_date')
                
                if branch:
                    queryset = queryset.filter(branch_id=branch)
                elif group:
                    queryset = queryset.filter(branch__branch_group_id=group)
                if start_date:
                    queryset = queryset.filter(call_time__date__gte=start_date)
                if end_date:
                    queryset = queryset.filter(call_time__date__lte=end_date)
                
                workbook = openpyxl.Workbook()
                worksheet = workbook.active
                worksheet.title = "Call Logs"
                
                headers = ['Type', 'Number', 'Duration (s)', 'SIM Slot', 'Branch Group', 'Branch', 'Device ID', 'Time']
                header_font = Font(bold=True)
                for col_num, header_title in enumerate(headers, 1):
                    cell = worksheet.cell(row=1, column=col_num)
                    cell.value = header_title
                    cell.font = header_font
                
                for row_num, log in enumerate(queryset, 2):
                    worksheet.cell(row=row_num, column=1).value = log.call_type
                    worksheet.cell(row=row_num, column=2).value = log.phone_number
                    worksheet.cell(row=row_num, column=3).value = log.duration
                    worksheet.cell(row=row_num, column=4).value = log.sim_slot
                    worksheet.cell(row=row_num, column=5).value = log.branch.branch_group.name if log.branch and log.branch.branch_group else "N/A"
                    worksheet.cell(row=row_num, column=6).value = log.branch.spa_name if log.branch else "N/A"
                    worksheet.cell(row=row_num, column=7).value = log.device.device_id if log.device else "N/A"
                    if log.call_time:
                        worksheet.cell(row=row_num, column=8).value = log.call_time.strftime("%Y-%m-%d %H:%M:%S")
                
                # We could save this to a file or storage, but for "direct" we can store in memory 
                # or just mark as completed. Since we need a later download, let's actually 
                # for now just mark all existing and new as completed and generate on the fly 
                # in the download view to avoid complex storage setup if not needed.
                
                job.status = 'completed'
                job.file_name = f"call_logs_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                job.save()
                
                return response.Response(ExportJobSerializer(job).data, status=status.HTTP_201_CREATED)
            else:
                job.status = 'failed'
                job.error_message = f"Unsupported export type: {export_type}"
                job.save()
                return response.Response({"error": "Unsupported type"}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
            job.save()
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
            
            # Re-generate the file for download (simplified version to avoid storage issues)
            queryset = CallLog.objects.all().select_related('branch', 'device').order_by('-call_time')
            queryset = apply_branch_filter(queryset, "branch_id", request.user)
            
            # Re-apply filters from stored data
            try:
                import ast
                filters = ast.literal_eval(job.error_message) if job.error_message else {}
                branch = filters.get('branch')
                group = filters.get('group')
                start_date = filters.get('start_date')
                end_date = filters.get('end_date')
                
                if branch:
                    queryset = queryset.filter(branch_id=branch)
                elif group:
                    queryset = queryset.filter(branch__branch_group_id=group)
                if start_date:
                    queryset = queryset.filter(call_time__date__gte=start_date)
                if end_date:
                    queryset = queryset.filter(call_time__date__lte=end_date)
            except:
                pass # Fallback to no filters if parsing fails
            
            workbook = openpyxl.Workbook()
            worksheet = workbook.active
            worksheet.title = "Call Logs"
            
            headers = ['Type', 'Number', 'Duration (s)', 'SIM Slot', 'Branch Group', 'Branch', 'Device ID', 'Time']
            for col_num, header_title in enumerate(headers, 1):
                worksheet.cell(row=1, column=col_num).value = header_title
            
            for row_num, log in enumerate(queryset, 2):
                worksheet.cell(row=row_num, column=1).value = log.call_type
                worksheet.cell(row=row_num, column=2).value = log.phone_number
                worksheet.cell(row=row_num, column=3).value = log.duration
                worksheet.cell(row=row_num, column=4).value = log.sim_slot
                worksheet.cell(row=row_num, column=5).value = log.branch.branch_group.name if log.branch and log.branch.branch_group else "N/A"
                worksheet.cell(row=row_num, column=6).value = log.branch.spa_name if log.branch else "N/A"
                worksheet.cell(row=row_num, column=7).value = log.device.device_id if log.device else "N/A"
                if log.call_time:
                    worksheet.cell(row=row_num, column=8).value = log.call_time.strftime("%Y-%m-%d %H:%M:%S")

            output = io.BytesIO()
            workbook.save(output)
            output.seek(0)
            
            file_response = HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            file_response['Content-Disposition'] = f'attachment; filename="{job.file_name or "export.xlsx"}"'
            return file_response
            
        except ExportJob.DoesNotExist:
            return response.Response({"error": "Export job not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return response.Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
