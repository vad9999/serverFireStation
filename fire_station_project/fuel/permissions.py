# app_name/permissions.py
from rest_framework.permissions import BasePermission


class CanBookCarFromMobile(BasePermission):
    """
    Разрешает доступ только если:
    - пользователь аутентифицирован;
    - его роль разрешена для мобильного бронирования;
    - токен выдан с client="mobile".
    """
    def has_permission(self, request, view):
        user = request.user
        payload = request.auth or {}

        if not user or not getattr(user, 'role', None):
            return False

        client = payload.get("client")
        return bool(
            client == "mobile" and
            getattr(user.role, "can_use_mobile_booking", False)
        )