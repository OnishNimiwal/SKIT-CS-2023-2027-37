"""Updated documents/views.py — supports all multimodal formats."""

from pathlib import Path

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.rag import delete_document, ingest_file
from chat.multimodal_extractor import ALL_SUPPORTED
from .models import Document
from .serializers import DocumentUploadSerializer

# Build allowed set from the extractor so we never drift out of sync
ALLOWED = ALL_SUPPORTED


class DocumentListCreateView(GenericAPIView):
    parser_classes = [MultiPartParser]
    serializer_class = DocumentUploadSerializer
    queryset = Document.objects.all()

    def get(self, request):
        docs = Document.objects.order_by("-uploaded_at")
        return Response([
            {
                "id": d.id,
                "title": d.title,
                "format": d.source_format,
                "embedding_status": d.embedding_status,
                "chunks": d.chunk_count,
                "uploaded_at": d.uploaded_at,
            }
            for d in docs
        ])

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded = serializer.validated_data["file"]
        ext = Path(uploaded.name).suffix.lower()

        if ext not in ALLOWED:
            return Response(
                {
                    "error": f"Unsupported file type '{ext}'.",
                    "supported": sorted(ALLOWED),
                },
                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        # Save the document record first (status = pending)
        doc = Document.objects.create(
            file=uploaded,
            title=Path(uploaded.name).stem,
            embedding_status="pending",
        )

        # Ingest synchronously (for large files consider Celery task)
        try:
            count = ingest_file(doc.file.path, str(doc.id))
            # Detect format from extractor result
            from chat.multimodal_extractor import extract_from_file
            meta = extract_from_file(doc.file.path)
            doc.chunk_count = count
            doc.source_format = meta["format"]
            doc.embedding_status = "done"
        except Exception as exc:
            doc.embedding_status = "failed"
            doc.save(update_fields=["embedding_status"])
            return Response(
                {"error": f"Ingestion failed: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        doc.save(update_fields=["chunk_count", "source_format", "embedding_status"])

        return Response(
            {
                "id": doc.id,
                "title": doc.title,
                "format": doc.source_format,
                "chunks": doc.chunk_count,
                "embedding_status": doc.embedding_status,
            },
            status=status.HTTP_201_CREATED,
        )


class DocumentDetailView(APIView):

    def get(self, request, pk):
        try:
            doc = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return Response({"error": "Not found"}, status=404)
        return Response({
            "id": doc.id,
            "title": doc.title,
            "format": doc.source_format,
            "embedding_status": doc.embedding_status,
            "chunks": doc.chunk_count,
            "uploaded_at": doc.uploaded_at,
            "file_url": request.build_absolute_uri(doc.file.url),
        })

    def delete(self, request, pk):
        try:
            doc = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

        delete_document(str(doc.id))
        doc.file.delete(save=False)
        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
