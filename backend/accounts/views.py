from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer


def serialize_user(user):
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.get_full_name(),
        "is_staff": user.is_staff,
    }


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfTokenView(APIView):
    """Sets the csrftoken cookie so the frontend can send X-CSRFToken on writes."""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"success": True})


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CurrentUserView(APIView):
    """Returns the signed-in user, or authenticated=false. Also refreshes the CSRF cookie."""
    permission_classes = [AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            return Response({"authenticated": True, "user": serialize_user(request.user)})
        return Response({"authenticated": False, "user": None})


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "error": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(
            request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {"success": False, "error": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(request, user)
        return Response({"success": True, "user": serialize_user(user)})


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logout(request)
        return Response({"success": True})
