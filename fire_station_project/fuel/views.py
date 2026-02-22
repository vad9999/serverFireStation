# fuel/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils.dateparse import parse_date

from .models import (
    Role, Permission, User,
    PassengerCar, NormsPassengerCars, PassengerCarWaybill,
    PassengerCarWaybillRecord, OdometerFuelPassengerCar,
    FireTruck, NormsFireTruck, FireTruckWaybill,
    FireTruckWaybillRecord, OdometerFuelFireTruck,
)
from .serializers import (
    RoleSerializer, PermissionSerializer, UserSerializer,
    PassengerCarSerializer, NormsPassengerCarsSerializer,
    PassengerCarWaybillSerializer, PassengerCarWaybillRecordSerializer,
    OdometerFuelPassengerCarSerializer,
    FireTruckSerializer, NormsFireTruckSerializer,
    FireTruckWaybillSerializer, FireTruckWaybillRecordSerializer,
    OdometerFuelFireTruckSerializer,
)


class SoftDeleteModelViewSet(viewsets.ModelViewSet):
    """
    Базовый ViewSet: DELETE делает мягкое удаление.
    """
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- Роли и права ------------------------------------------------------------

class RoleViewSet(SoftDeleteModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer


class PermissionViewSet(SoftDeleteModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer


# --- Пользователи ------------------------------------------------------------

class UserViewSet(SoftDeleteModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


# --- Легковые ---------------------------------------------------------------

class PassengerCarViewSet(SoftDeleteModelViewSet):
    queryset = PassengerCar.objects.all()
    serializer_class = PassengerCarSerializer


class NormsPassengerCarsViewSet(SoftDeleteModelViewSet):
    queryset = NormsPassengerCars.objects.all()
    serializer_class = NormsPassengerCarsSerializer

    @action(detail=False, methods=['get'], url_path='for-date')
    def for_date(self, request):
        """
        GET /api/passenger-car-norms/for-date/?car=<id>&season=<summer|winter>&date=YYYY-MM-DD

        Возвращает последнюю норму для указанной машины и сезона
        на дату документа (date__lte=дата, сортировка по дате/ID).
        """
        car_id = request.query_params.get('car')
        season = request.query_params.get('season')
        date_str = request.query_params.get('date')

        if not car_id or not season or not date_str:
            return Response(
                {"detail": "Параметры car, season и date обязательны"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        doc_date = parse_date(date_str)
        if not doc_date:
            return Response(
                {"detail": "Неверный формат date, ожидается YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        norm = (
            NormsPassengerCars.objects
            .filter(car_id=car_id, season=season, date__lte=doc_date)
            .order_by('-date', '-id')
            .first()
        )
        if not norm:
            return Response(
                {"detail": "Норма не найдена"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(norm)
        return Response(serializer.data)


class OdometerFuelPassengerCarViewSet(SoftDeleteModelViewSet):
    queryset = OdometerFuelPassengerCar.objects.all()
    serializer_class = OdometerFuelPassengerCarSerializer

    @action(detail=False, methods=['get'], url_path='last')
    def last_record(self, request):
        """
        GET /api/passenger-car-odometer-fuel/last/?car=<id>

        Возвращает последнюю запись по данному автомобилю
        (по дате и ID).
        """
        car_id = request.query_params.get('car')
        if not car_id:
            return Response(
                {"detail": "Параметр car обязателен"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        obj = (
            OdometerFuelPassengerCar.objects
            .filter(car_id=car_id)
            .order_by('-date', '-id')
            .first()
        )
        if not obj:
            return Response(
                {"detail": "Записей не найдено"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(obj)
        return Response(serializer.data)


class PassengerCarWaybillViewSet(SoftDeleteModelViewSet):
    queryset = PassengerCarWaybill.objects.all()
    serializer_class = PassengerCarWaybillSerializer


class PassengerCarWaybillRecordViewSet(SoftDeleteModelViewSet):
    queryset = PassengerCarWaybillRecord.objects.select_related('passenger_car_waybill')
    serializer_class = PassengerCarWaybillRecordSerializer


# --- Пожарные ---------------------------------------------------------------

class FireTruckViewSet(SoftDeleteModelViewSet):
    queryset = FireTruck.objects.all()
    serializer_class = FireTruckSerializer


class NormsFireTruckViewSet(SoftDeleteModelViewSet):
    queryset = NormsFireTruck.objects.all()
    serializer_class = NormsFireTruckSerializer

    @action(detail=False, methods=['get'], url_path='for-date')
    def for_date(self, request):
        """
        GET /api/fire-truck-norms/for-date/?car=<id>&season=<summer|winter>&date=YYYY-MM-DD

        Возвращает последнюю норму для указанного ПА и сезона
        на дату документа (date__lte=дата).
        """
        car_id = request.query_params.get('car')
        season = request.query_params.get('season')
        date_str = request.query_params.get('date')

        if not car_id or not season or not date_str:
            return Response(
                {"detail": "Параметры car, season и date обязательны"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        doc_date = parse_date(date_str)
        if not doc_date:
            return Response(
                {"detail": "Неверный формат date, ожидается YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        norm = (
            NormsFireTruck.objects
            .filter(car_id=car_id, season=season, date__lte=doc_date)
            .order_by('-date', '-id')
            .first()
        )
        if not norm:
            return Response(
                {"detail": "Норма не найдена"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(norm)
        return Response(serializer.data)


class OdometerFuelFireTruckViewSet(SoftDeleteModelViewSet):
    queryset = OdometerFuelFireTruck.objects.all()
    serializer_class = OdometerFuelFireTruckSerializer

    @action(detail=False, methods=['get'], url_path='last')
    def last_record(self, request):
        """
        GET /api/fire-truck-odometer-fuel/last/?car=<id>

        Возвращает последнюю запись по данному пожарному автомобилю.
        """
        car_id = request.query_params.get('car')
        if not car_id:
            return Response(
                {"detail": "Параметр car обязателен"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        obj = (
            OdometerFuelFireTruck.objects
            .filter(car_id=car_id)
            .order_by('-date', '-id')
            .first()
        )
        if not obj:
            return Response(
                {"detail": "Записей не найдено"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(obj)
        return Response(serializer.data)


class FireTruckWaybillViewSet(SoftDeleteModelViewSet):
    queryset = FireTruckWaybill.objects.all()
    serializer_class = FireTruckWaybillSerializer


class FireTruckWaybillRecordViewSet(SoftDeleteModelViewSet):
    queryset = FireTruckWaybillRecord.objects.select_related('fire_truck_waybill')
    serializer_class = FireTruckWaybillRecordSerializer