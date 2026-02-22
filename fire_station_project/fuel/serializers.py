# fuel/serializers.py
from rest_framework import serializers
from .models import (
    Role, Permission, User,
    PassengerCar, NormsPassengerCars, PassengerCarWaybill,
    PassengerCarWaybillRecord, OdometerFuelPassengerCar,
    FireTruck, NormsFireTruck, FireTruckWaybill,
    FireTruckWaybillRecord, OdometerFuelFireTruck,
)


# --- Роли и права ------------------------------------------------------------

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'


# --- Пользователь ------------------------------------------------------------

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


# --- Легковой автомобиль -----------------------------------------------------

class PassengerCarSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassengerCar
        fields = '__all__'


class NormsPassengerCarsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NormsPassengerCars
        fields = '__all__'


class OdometerFuelPassengerCarSerializer(serializers.ModelSerializer):
    class Meta:
        model = OdometerFuelPassengerCar
        fields = '__all__'


class PassengerCarWaybillSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassengerCarWaybill
        fields = '__all__'
        read_only_fields = [
            'upon_issuance',
            'total_spent',
            'total_received',
            'required_by_norm',
            'availability_upon_delivery',
            'savings',
            'overrun',
        ]


class PassengerCarWaybillRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassengerCarWaybillRecord
        fields = '__all__'
        read_only_fields = [
            'fuel_before_departure',
            'odometer_before',
            'odometer_after',
            'distance_total_km',
            'fuel_used_city',
            'fuel_used_area',
            'fuel_on_return',
            'fuel_used_normal',
        ]


# --- Пожарный автомобиль -----------------------------------------------------

class FireTruckSerializer(serializers.ModelSerializer):
    class Meta:
        model = FireTruck
        fields = '__all__'


class NormsFireTruckSerializer(serializers.ModelSerializer):
    class Meta:
        model = NormsFireTruck
        fields = '__all__'


class OdometerFuelFireTruckSerializer(serializers.ModelSerializer):
    class Meta:
        model = OdometerFuelFireTruck
        fields = '__all__'


class FireTruckWaybillSerializer(serializers.ModelSerializer):
    class Meta:
        model = FireTruckWaybill
        fields = '__all__'
        read_only_fields = [
            'upon_issuance',
            'total_spent',
            'total_received',
            'required_by_norm',
            'availability_upon_delivery',
            'savings',
            'overrun',
        ]


class FireTruckWaybillRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = FireTruckWaybillRecord
        fields = '__all__'
        read_only_fields = [
            'fuel_before_departure',
            'odometer_before',
            'distance_km',
            'fuel_on_return',
            'fuel_used_by_distance',
            'fuel_used_with_pump',
            'fuel_used_without_pump',
            'fuel_used_normal',
        ]