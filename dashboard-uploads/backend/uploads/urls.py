from django.urls import path

from .views import UploadDetailView, UploadListCreateView

urlpatterns = [
    path("", UploadListCreateView.as_view(), name="upload-list-create"),
    path("<int:pk>/", UploadDetailView.as_view(), name="upload-detail"),
]
