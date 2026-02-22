# fuel/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views_auth import LoginView
from .views import (
    RoleViewSet, PermissionViewSet, UserViewSet,
    PassengerCarViewSet, NormsPassengerCarsViewSet,
    PassengerCarWaybillViewSet, PassengerCarWaybillRecordViewSet,
    OdometerFuelPassengerCarViewSet,
    FireTruckViewSet, NormsFireTruckViewSet,
    FireTruckWaybillViewSet, FireTruckWaybillRecordViewSet,
    OdometerFuelFireTruckViewSet,
)

router = DefaultRouter()

# Роли и права
router.register(r'roles', RoleViewSet)
router.register(r'permissions', PermissionViewSet)

# Пользователи
router.register(r'users', UserViewSet)

# Легковой авто
router.register(r'passenger-cars', PassengerCarViewSet)
router.register(r'passenger-car-norms', NormsPassengerCarsViewSet)
router.register(r'passenger-car-odometer-fuel', OdometerFuelPassengerCarViewSet)
router.register(r'passenger-car-waybills', PassengerCarWaybillViewSet)
router.register(r'passenger-car-records', PassengerCarWaybillRecordViewSet)

# Пожарный авто
router.register(r'fire-trucks', FireTruckViewSet)
router.register(r'fire-truck-norms', NormsFireTruckViewSet)
router.register(r'fire-truck-odometer-fuel', OdometerFuelFireTruckViewSet)
router.register(r'fire-truck-waybills', FireTruckWaybillViewSet)
router.register(r'fire-truck-records', FireTruckWaybillRecordViewSet)

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='login'),
]

urlpatterns += router.urls