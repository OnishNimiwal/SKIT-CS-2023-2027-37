import os
from django.conf import settings
from django.db import models

class Document(models.Model):
    # Uploader; documents are only visible to their owner
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="documents"
    )
    file = models.FileField(upload_to="documents/%Y/%m/")
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10)  # 'PDF' or 'TXT'
    extracted_text = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.original_name} ({self.file_type}) - {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"

    def delete(self, *args, **kwargs):
        """Clean up the local physical file upon model deletion."""
        if self.file and os.path.isfile(self.file.path):
            try:
                os.remove(self.file.path)
            except OSError:
                pass
        super().delete(*args, **kwargs)
