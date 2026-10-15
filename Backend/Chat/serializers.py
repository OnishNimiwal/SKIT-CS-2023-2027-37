from rest_framework import serializers


class ChatSerializer(serializers.Serializer):
    message = serializers.CharField(required=True, allow_blank=False)
    thread_id = serializers.CharField(required=False, default="default", max_length=100)
    document_ids = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )