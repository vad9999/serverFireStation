# fuel/views_auth.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import User
from .auth import create_access_token


class LoginView(APIView):
    """
    POST /api/auth/login/
    {
      "login": "...",
      "password": "...",
      "client": "web" | "mobile"
    }
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        login = request.data.get("login")
        password = request.data.get("password")
        client = request.data.get("client", "web")

        if not login or not password:
            return Response(
                {"detail": "login и password обязательны"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(login=login)
        except User.DoesNotExist:
            return Response(
                {"detail": "Неверный логин или пароль"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return Response(
                {"detail": "Неверный логин или пароль"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access_token = create_access_token(user, client_type=client)

        return Response(
            {
                "access": access_token,
                "user": {
                    "id": user.id,
                    "login": user.login,
                    "role": user.role_id,
                    "name": user.name,
                    "surname": user.surname,
                    "last_name": user.last_name,
                },
            },
            status=status.HTTP_200_OK,
        )