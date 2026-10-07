from django.db import models


class Document(models.Model):
    file = models.FileField(upload_to="documents/")
    title = models.CharField(max_length=255, blank=True)
    chunk_count = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or self.file.name