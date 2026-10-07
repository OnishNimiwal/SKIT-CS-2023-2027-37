from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import ChatSerializer
from .services import ask_ollama


class ChatAPIView(APIView):
    def post(self, request):
        serializer = ChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            out = ask_ollama(data["message"], data["thread_id"], data["document_ids"])
            return Response({
                "success": True,
                "response": out["answer"],
                "sources": out["sources"],
                "model": "local-ollama",
                "external_api": False,
                "thread_id": data["thread_id"],
            })
        except Exception:
            return Response({
                "success": False,
                "error": "Local AI server is unavailable.",
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)