# fuel/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    RankViewSet, RoleViewSet, RoleSubstitutionViewSet,
    DriverLicenseViewSet, UserViewSet,
    RequiredRoleViewSet, WaybillViewSet, SignatureViewSet,
    CarViewSet, PassengerCarViewSet, FireTruckViewSet,
    PassengerCarWaybillViewSet, PassengerCarWaybillRecordViewSet,
    FireTruckWaybillViewSet, FireTruckWaybillRecordViewSet,
)
from .views_auth import LoginView

router = DefaultRouter()
router.register(r'ranks', RankViewSet)
router.register(r'roles', RoleViewSet)
router.register(r'role-substitutions', RoleSubstitutionViewSet)
router.register(r'driver-licenses', DriverLicenseViewSet)
router.register(r'users', UserViewSet)

router.register(r'required-roles', RequiredRoleViewSet)
router.register(r'signatures', SignatureViewSet)
router.register(r'waybills', WaybillViewSet, basename='waybill')

router.register(r'cars', CarViewSet)
router.register(r'passenger-cars', PassengerCarViewSet)
router.register(r'fire-trucks', FireTruckViewSet)

router.register(r'passenger-car-waybills', PassengerCarWaybillViewSet)
router.register(r'passenger-car-records', PassengerCarWaybillRecordViewSet)
router.register(r'fire-truck-waybills', FireTruckWaybillViewSet)
router.register(r'fire-truck-records', FireTruckWaybillRecordViewSet)

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='login'),
]

urlpatterns += router.urls