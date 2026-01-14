# transport/services.py
from django.core.exceptions import PermissionDenied

from .models import (
    User,
    RequiredRole,
    RoleSubstitution,
    Signature,
    Waybill,
)


def can_user_sign_required_role(user: User, req: RequiredRole) -> bool:
    """
    Может ли данный пользователь закрыть подпись для требуемой роли req.
    1) Если его роль = требуемой роли — да.
    2) Если его роль указана как заместитель для требуемой роли — тоже да.
    """
    user_role = user.role

    # ТУТ БЫЛА ОШИБКА: не нужен оператор :=, нужно обычное сравнение
    if user_role.id == req.role_id:
        return True

    # проверяем, есть ли подстановка: req.role -> user.role
    return RoleSubstitution.objects.filter(
        main_role=req.role,
        substitute_role=user_role,
    ).exists()


def sign_waybill_for_required_role(
    user: User,
    waybill: Waybill,
    req: RequiredRole,
) -> Signature:
    """
    Подписать путевой лист waybill пользователем user в слоте обязательной роли req.
    """
    if not can_user_sign_required_role(user, req):
        raise PermissionDenied("У вас нет права подписать этот слот")

    signature, created = Signature.objects.get_or_create(
        waybill=waybill,
        required_role=req,
        defaults={'user': user},
    )

    # Слот уже был подписан другим пользователем
    if not created and signature.user_id != user.id:
        raise PermissionDenied("Этот слот уже подписан другим пользователем")

    return signature