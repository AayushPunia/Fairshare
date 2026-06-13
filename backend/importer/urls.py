from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.ImportUploadView.as_view(), name='import-upload'),
    path('<int:session_id>/', views.ImportSessionDetailView.as_view(), name='import-detail'),
    path('<int:session_id>/resolve/', views.ImportResolveView.as_view(), name='import-resolve'),
    path('<int:session_id>/confirm/', views.ImportConfirmView.as_view(), name='import-confirm'),
    path('<int:session_id>/report/', views.ImportReportView.as_view(), name='import-report'),
]
