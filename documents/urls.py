from django.urls import path
from .views import DocumentUploadView, DocumentListView, DocumentDeleteView

urlpatterns = [
    path("", DocumentListView.as_view()),
    path("upload/", DocumentUploadView.as_view()),
    path("<int:pk>/", DocumentDeleteView.as_view()),
]