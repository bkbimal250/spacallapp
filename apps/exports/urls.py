from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExportViewSet, GenerateExportView, DownloadExportView

router = DefaultRouter()
router.register(r'', ExportViewSet, basename='export')

urlpatterns = [
    path('generate/', GenerateExportView.as_view(), name='export-generate'),
    path('<int:pk>/download/', DownloadExportView.as_view(), name='export-download'),
    path('', include(router.urls)),
]
