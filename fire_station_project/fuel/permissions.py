# fuel/permissions.py
from rest_framework.permissions import BasePermission


class CanBookCarFromMobile(BasePermission):
    """
    Разрешает доступ только если:
    - пользователь аутентифицирован;
    - токен выдан с client="mobile";
    - у роли пользователя Permission.can_use_mobile_booking = True.
    """

    def has_permission(self, request, view):
        user = request.user
        payload = request.auth or {}

        # 1. Пользователь должен быть аутентифицирован и иметь роль
        role = getattr(user, 'role', None)
        if not user or not role:
            return False

        # 2. Токен должен быть выдан именно для мобильного клиента
        client = payload.get("client")
        if client != "mobile":
            return False

        # 3. Берём объект Permission, связанный с ролью
        # В модели Permission: related_name="role"
        # Значит у Role обратное поле называется role
        perm = getattr(role, "role", None)  # Permission или None

        return bool(perm and perm.can_use_mobile_booking)