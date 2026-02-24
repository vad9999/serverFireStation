# fuel/auth.py
import jwt
import hashlib
from datetime import datetime, timedelta, timezone

from django.conf import settings
from rest_framework import authentication, exceptions

from .models import User


JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_LIFETIME_MINUTES = 60


def _password_fingerprint(user: User) -> str:
    """
    Возвращает отпечаток текущего пароля пользователя.
    Основан на уже захешированном поле user.password.
    Если пароль поменяли (как угодно) — отпечаток сменится.
    """
    # user.password уже хеш (make_password). Дополнительно хэшируем его,
    # чтобы не класть в токен исходный хеш из БД.
    return hashlib.sha256(user.password.encode('utf-8')).hexdigest()


def create_access_token(user: User, client_type: str = "web") -> str:
    """
    Создаёт JWT access-токен для пользователя.
    client_type: "web" или "mobile".
    В токен добавляем 'pwd_fp' — отпечаток текущего пароля.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "login": user.login,
        "role": user.role_id,
        "client": client_type,
        "pwd_fp": _password_fingerprint(user),  # отпечаток пароля
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
    DRF-аутентификация по заголовку Authorization: Bearer <token>.
    Дополнительно проверяем:
    - что пароль пользователя не менялся с момента выдачи токена.
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
            raise exceptions.AuthenticationFailed("Некорректный токен (нет sub)")

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("Пользователь не найден")

        # Проверка отпечатка пароля
        token_pwd_fp = payload.get("pwd_fp")
        if not token_pwd_fp:
            # Токен без отпечатка пароля считаем некорректным
            raise exceptions.AuthenticationFailed("Некорректный токен (нет pwd_fp)")

        current_pwd_fp = _password_fingerprint(user)
        if token_pwd_fp != current_pwd_fp:
            # Пароль менялся — токен больше не действителен
            raise exceptions.AuthenticationFailed(
                "Пароль был изменён. Авторизуйтесь снова."
            )

        return user, payload