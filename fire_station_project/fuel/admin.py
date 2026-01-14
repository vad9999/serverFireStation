from django.contrib import admin
from .models import (
    Rank, Role, RoleSubstitution,
    DriverLicense, User,
    RequiredRole, Waybill, Signature,
    Car, PassengerCar, FireTruck,
    PassengerCarWaybill, PassengerCarWaybillRecord,
    FireTruckWaybill, FireTruckWaybillRecord,
)


# Самый простой вариант — просто зарегистрировать модели

admin.site.register(Rank)
admin.site.register(Role)
admin.site.register(RoleSubstitution)
admin.site.register(DriverLicense)
admin.site.register(User)
admin.site.register(RequiredRole)
admin.site.register(Waybill)
admin.site.register(Signature)
admin.site.register(Car)
admin.site.register(PassengerCar)
admin.site.register(FireTruck)
admin.site.register(PassengerCarWaybill)
admin.site.register(PassengerCarWaybillRecord)
admin.site.register(FireTruckWaybill)
admin.site.register(FireTruckWaybillRecord)