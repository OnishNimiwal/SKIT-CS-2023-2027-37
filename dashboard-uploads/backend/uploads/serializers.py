from rest_framework import serializers

from .models import Upload


class UploadSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    text_preview = serializers.SerializerMethodField()
    char_count = serializers.SerializerMethodField()

    class Meta:
        model = Upload
        fields = [
            "id", "original_name", "modality", "size", "status", "note",
            "file_url", "text_preview", "char_count", "created_at",
        ]

    def get_file_url(self, obj):
        request = self.context.get("request")
        url = obj.file.url if obj.file else ""
        return request.build_absolute_uri(url) if request and url else url

    def get_text_preview(self, obj):
        return obj.extracted_text[:1500]

    def get_char_count(self, obj):
        return len(obj.extracted_text)
