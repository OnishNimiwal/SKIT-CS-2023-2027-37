from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver


def upload_path(instance, filename):
    return f"uploads/{instance.modality}/{filename}"


class Upload(models.Model):
    class Modality(models.TextChoices):
        DOCUMENT = "document", "Document"
        IMAGE = "image", "Image"
        AUDIO = "audio", "Audio"

    class Status(models.TextChoices):
        PROCESSED = "processed", "Text extracted"
        STORED = "stored", "Stored"      # saved, but no extractor configured for this type
        FAILED = "failed", "Processing failed"

    file = models.FileField(upload_to=upload_path)
    original_name = models.CharField(max_length=255)
    modality = models.CharField(max_length=16, choices=Modality.choices)
    size = models.PositiveBigIntegerField(default=0)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.STORED)
    note = models.TextField(blank=True)
    extracted_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.original_name} ({self.modality})"


@receiver(post_delete, sender=Upload)
def delete_file_from_disk(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)
