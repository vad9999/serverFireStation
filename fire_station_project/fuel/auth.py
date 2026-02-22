# fuel/auth.py
import jwt
from datetime import datetime, timedelta, timezone

from django.conf import settings
from rest_framework import authentication, exceptions

from .models import User


JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_LIFETIME_MINUTES = 60


def create_access_token(user: User, client_type: str = "web") -> str:
    """
    Создаёт JWT access-токен для пользователя.
    client_type: "web" или "mobile".
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "login": user.login,
        "role": user.role_id,
        "client": client_type,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_LIFETIME_MINUTES),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_access_token(token: str) -> dict:
    """
    Декодирует и проверяет access-токен.
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


class JWTAuthentication(authentication.BaseAuthentication):
    """
    DRF-аутентификация по заголовку Authorization: Bearer <token>
    """

    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).decode("utf-8")

        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            return None

        token = parts[1]

        try:
            payload = decode_access_token(token)
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Токен истёк")
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed("Неверный токен")

        user_id = payload.get("sub")
        if not user_id:
            raise exceptions.AuthenticationFailed("Некорректный токен")

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("Пользователь не найден")

        return user, payload