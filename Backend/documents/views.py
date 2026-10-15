from pathlib import Path

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.rag import delete_document, ingest_file
from .models import Document
from .serializers import DocumentUploadSerializer

ALLOWED = {".pdf", ".docx", ".txt", ".md"}


class DocumentListCreateView(GenericAPIView):
    parser_classes = [MultiPartParser]
    serializer_class = DocumentUploadSerializer   # makes the browsable API show a file picker
    queryset = Document.objects.all()             # needed by the browsable API renderer

    def get(self, request):
        docs = Document.objects.order_by("-uploaded_at")
        return Response([
            {"id": d.id, "title": d.title, "chunks": d.chunk_count, "uploaded_at": d.uploaded_at}
            for d in docs
        ])

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        f = serializer.validated_data["file"]

        if Path(f.name).suffix.lower() not in ALLOWED:
            return Response(
                {"error": "Only PDF, DOCX, TXT, MD supported"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        doc = Document.objects.create(file=f, title=f.name)
        try:
            doc.chunk_count = ingest_file(doc.file.path, doc.id, f.name)
            doc.save(update_fields=["chunk_count"])
        except Exception as e:
            doc.file.delete(save=False)
            doc.delete()
            return Response(
                {"error": f"Indexing failed: {e}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {"id": doc.id, "title": doc.title, "chunks": doc.chunk_count},
            status=status.HTTP_201_CREATED,
        )


class DocumentDetailView(APIView):
    def delete(self, request, pk):
        try:
            doc = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        delete_document(doc.id)
        doc.file.delete(save=False)
        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)