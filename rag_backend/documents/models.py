"""Updated Document model — adds source_format and embedding_status fields."""

from django.db import models


class Document(models.Model):
    """Tracks every uploaded file and its ChromaDB ingestion state."""

    class EmbeddingStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        DONE    = "done",    "Done"
        FAILED  = "failed",  "Failed"

    file             = models.FileField(upload_to="documents/")
    title            = models.CharField(max_length=255, blank=True)

    # NEW: format label returned by multimodal_extractor (e.g. "PDF", "CSV")
    source_format    = models.CharField(max_length=64, blank=True, default="")

    # NEW: ingestion lifecycle tracking
    embedding_status = models.CharField(
        max_length=16,
        choices=EmbeddingStatus.choices,
        default=EmbeddingStatus.PENDING,
    )

    chunk_count  = models.IntegerField(default=0)
    uploaded_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.source_format or 'unknown'}) — {self.embedding_status}"
