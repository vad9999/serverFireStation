from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets

from .models import Waybill, RequiredRole
from .serializers import WaybillSerializer, SignatureSerializer
from .services import sign_waybill_for_required_role
from .permissions import CanBookCarFromMobile

from .models import (
    Rank, Role, RoleSubstitution, DriverLicense, User,
    RequiredRole, Waybill, Signature,
    Car, PassengerCar, FireTruck,
    PassengerCarWaybill, PassengerCarWaybillRecord,
    FireTruckWaybill, FireTruckWaybillRecord,
)
from .serializers import *
from .services import can_user_sign_required_role, sign_waybill_for_required_role

class SoftDeleteModelViewSet(viewsets.ModelViewSet):
    """
    Базовый ViewSet: .destroy() делает мягкое удаление.
    """
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()     # soft-delete
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class RankViewSet(SoftDeleteModelViewSet):
    queryset = Rank.objects.all()
    serializer_class = RankSerializer


class RoleViewSet(SoftDeleteModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer


class RoleSubstitutionViewSet(SoftDeleteModelViewSet):
    queryset = RoleSubstitution.objects.all()
    serializer_class = RoleSubstitutionSerializer


class DriverLicenseViewSet(SoftDeleteModelViewSet):
    queryset = DriverLicense.objects.all()
    serializer_class = DriverLicenseSerializer


class UserViewSet(SoftDeleteModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class RequiredRoleViewSet(SoftDeleteModelViewSet):
    queryset = RequiredRole.objects.select_related('role')
    serializer_class = RequiredRoleSerializer

class SignatureViewSet(SoftDeleteModelViewSet):
    queryset = Signature.objects.select_related('waybill', 'required_role', 'user')
    serializer_class = SignatureSerializer

class WaybillViewSet(SoftDeleteModelViewSet):
    queryset = Waybill.objects.all()
    serializer_class = WaybillSerializer

    @action(detail=True, methods=['post'])
    def sign(self, request, pk=None):
        waybill = self.get_object()
        required_role_id = request.data.get('required_role')

        if not required_role_id:
            return Response(
                {"detail": "required_role is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            req = RequiredRole.objects.get(pk=required_role_id)
        except RequiredRole.DoesNotExist:
            return Response(
                {"detail": "RequiredRole not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        sig = sign_waybill_for_required_role(request.user, waybill, req)
        serializer = SignatureSerializer(sig)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CarViewSet(SoftDeleteModelViewSet):
    queryset = Car.objects.all()
    serializer_class = CarSerializer

    # если JWT-аутентификация включена глобально через REST_FRAMEWORK,
    # эту строчку можно не писать.
    # authentication_classes = [JWTAuthentication]

    @action(
        detail=True,
        methods=['post'],
        url_path='book-mobile',
        permission_classes=[CanBookCarFromMobile],
    )
    def book_mobile(self, request, pk=None):
        """
        POST /api/cars/{id}/book-mobile/
        Только через мобильное приложение и только для ролей с can_book_from_mobile = True.

        Здесь ты реализуешь свою бизнес-логику "взять машину":
        - проверить, свободна ли машина;
        - создать путевой лист / запись;
        - пометить машину как занятую и т.п.
        """
        car = self.get_object()
        user = request.user

        # Пример очень простой заглушки:
        # можно принимать из тела запроса нужные данные:
        #   {"from_date": "...", "for_date": "...", "type": "passenger" | "fire_truck", ...}
        from_date = request.data.get("from_date")
        for_date = request.data.get("for_date")

        if not from_date or not for_date:
            return Response(
                {"detail": "from_date и for_date обязательны"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # TODO: здесь твоя бизнес-логика:
        #   - создать Waybill
        #   - создать PassengerCarWaybill / FireTruckWaybill
        #   - возможно, создать первую запись в карточке и т.п.
        #
        # Сейчас просто вернём заглушку:
        data = {
            "message": "Машина успешно забронирована через мобильное приложение",
            "car_id": car.id,
            "car_number": car.number,
            "user": user.login,
            "from_date": from_date,
            "for_date": for_date,
        }
        return Response(data, status=status.HTTP_201_CREATED)


class PassengerCarViewSet(SoftDeleteModelViewSet):
    queryset = PassengerCar.objects.select_related('car')
    serializer_class = PassengerCarSerializer


class FireTruckViewSet(SoftDeleteModelViewSet):
    queryset = FireTruck.objects.select_related('car')
    serializer_class = FireTruckSerializer

class PassengerCarWaybillViewSet(SoftDeleteModelViewSet):
    queryset = PassengerCarWaybill.objects.select_related('waybill', 'passenger_car')
    serializer_class = PassengerCarWaybillSerializer


class FireTruckWaybillViewSet(SoftDeleteModelViewSet):
    queryset = FireTruckWaybill.objects.select_related('waybill', 'fire_truck')
    serializer_class = FireTruckWaybillSerializer

class PassengerCarWaybillRecordViewSet(SoftDeleteModelViewSet):
    queryset = PassengerCarWaybillRecord.objects.select_related(
        'passenger_car_waybill', 'driver'
    )
    serializer_class = PassengerCarWaybillRecordSerializer

class FireTruckWaybillRecordViewSet(SoftDeleteModelViewSet):
    queryset = FireTruckWaybillRecord.objects.select_related('fire_truck_waybill')
    serializer_class = FireTruckWaybillRecordSerializer

