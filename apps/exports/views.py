from rest_framework import viewsets, permissions, views, response, status
from .models import ExportJob
from .serializers import ExportJobSerializer

class ExportViewSet(viewsets.ModelViewSet):
    queryset = ExportJob.objects.all().order_by('-created_at')
    serializer_class = ExportJobSerializer
    permission_classes = [permissions.IsAuthenticated]

class GenerateExportView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        export_type = request.data.get('type')
        # Logic to trigger export task (Celery)
        # For now, just create a record
        job = ExportJob.objects.create(
            user=request.user,
            export_type=export_type,
            status='pending',
            # file_name='pending.csv'
        )
        return response.Response(ExportJobSerializer(job).data, status=status.HTTP_201_CREATED)

class DownloadExportView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        # Logic to serve the file
        return response.Response({"message": "Download logic here"}, status=status.HTTP_200_OK)
