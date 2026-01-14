# serializers.py
from rest_framework import serializers
from .models import (
    Rank, Role, RoleSubstitution, DriverLicense, User,
    RequiredRole, Waybill, Signature,
    Car, PassengerCar, FireTruck,
    PassengerCarWaybill, PassengerCarWaybillRecord,
    FireTruckWaybill, FireTruckWaybillRecord,
)

class RankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rank
        fields = '__all__'


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


class RoleSubstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleSubstitution
        fields = '__all__'


class DriverLicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverLicense
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True},  # не отдаём хеш во фронт
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


class RequiredRoleSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = RequiredRole
        fields = ['role', 'role_name', 'order', 'id']
        read_only_fields = ['id']

class SignatureSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='required_role.role.name', read_only=True)
    user_name = serializers.CharField(source='user.login', read_only=True)

    class Meta:
        model = Signature
        fields = ['id', 'waybill', 'required_role', 'role',
                  'user', 'user_name', 'signed_at']
        read_only_fields = ['id', 'signed_at']


class WaybillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Waybill
        fields = '__all__'

class CarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = '__all__'


class PassengerCarSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassengerCar
        fields = '__all__'


class FireTruckSerializer(serializers.ModelSerializer):
    class Meta:
        model = FireTruck
        fields = '__all__'

class PassengerCarWaybillSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassengerCarWaybill
        fields = '__all__'


class FireTruckWaybillSerializer(serializers.ModelSerializer):
    class Meta:
        model = FireTruckWaybill
        fields = '__all__'


class PassengerCarWaybillRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassengerCarWaybillRecord
        fields = '__all__'
        # вычисляемые поля считаем на бэке, с фронта не пишем
        read_only_fields = [
            'norm_city', 'norm_area',
            'distance_total_km',
            'fuel_used_city', 'fuel_used_area',
            'fuel_used_total', 'fuel_on_return',
        ]

class FireTruckWaybillRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = FireTruckWaybillRecord
        fields = '__all__'
        read_only_fields = [
            'norm_km', 'norm_with_pump', 'norm_without_pump',
            'distance_km',
            'fuel_used_by_distance',
            'fuel_used_with_pump', 'fuel_used_without_pump',
            'fuel_used_total', 'fuel_on_return',
        ]

