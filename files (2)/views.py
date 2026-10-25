from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import Upload
from .serializers import UploadSerializer


class UploadListCreateView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        qs = Upload.objects.all()
        modality = request.query_params.get("modality")
        if modality in Upload.Modality.values:
            qs = qs.filter(modality=modality)
        return Response(UploadSerializer(qs, many=True, context={"request": request}).data)

    def post(self, request):
        file = request.FILES.get("file")
        if file is None:
            return Response({"error": 'No file received (form field must be named "file").'},
                            status=status.HTTP_400_BAD_REQUEST)
        error, modality = services.validate(file)
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        upload = Upload.objects.create(file=file, original_name=file.name, modality=modality, size=file.size)
        services.process(upload)  # runs synchronously; slow OCR/ASR handlers will make this request slow
        upload.save()
        return Response(UploadSerializer(upload, context={"request": request}).data,
                        status=status.HTTP_201_CREATED)


class UploadDetailView(APIView):
    def delete(self, request, pk):
        get_object_or_404(Upload, pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
