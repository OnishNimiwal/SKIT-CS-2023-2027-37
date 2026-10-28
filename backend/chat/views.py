from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatSerializer
from .services import ask_ollama

class ChatAPIView(APIView):
    def post(self, request):
        serializer = ChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            answer = ask_ollama(serializer.validated_data["message"])
            return Response({
                "success": True,
                "response": answer,
                "model": "local-ollama",
                "external_api": False,
            })
        except Exception:
            return Response({
                "success": False,
                "error": "Local AI server is unavailable.",
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
