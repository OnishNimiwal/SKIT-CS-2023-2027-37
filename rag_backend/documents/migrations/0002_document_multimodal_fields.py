"""
Migration: add source_format and embedding_status to Document model.

Place this file in:   rag_backend/documents/migrations/0002_document_multimodal_fields.py
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # Replace '0001_initial' with your actual last migration name
        ("documents", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="source_format",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="document",
            name="embedding_status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("done", "Done"),
                    ("failed", "Failed"),
                ],
                default="pending",
                max_length=16,
            ),
        ),
    ]
