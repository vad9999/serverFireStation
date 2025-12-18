from django.db import models
from django.utils import timezone

# Для мягкого удаления
class SoftDeleteQuerySet(models.QuerySet):
    """
    QuerySet, который:
    - при .delete() делает мягкое удаление (проставляет deleted_at)
    - умеет отдавать только живые / только удалённые / всё
    """

    def delete(self):
        """
        Мягкое удаление для queryset'а:
        Car.objects.filter(...).delete()
        -> просто проставит deleted_at для всех записей.
        """
        return super().update(deleted_at=timezone.now())

    def hard_delete(self):
        """
        Настоящее удаление из БД для queryset'а.
        """
        return super().delete()

    def alive(self):
        """
        Только не удалённые записи (deleted_at IS NULL).
        """
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        """
        Только "удалённые" (deleted_at IS NOT NULL).
        """
        return self.filter(deleted_at__isnull=False)


class SoftDeleteManager(models.Manager):
    """
    Менеджер по умолчанию: показывает только живые записи.
    """

    def get_queryset(self):
        # Базовый queryset — живые записи
        return SoftDeleteQuerySet(self.model, using=self._db).alive()

    # Доп. методы, если вдруг понадобятся:
    def all_with_deleted(self):
        """
        Все записи, включая помеченные как удалённые.
        """
        return SoftDeleteQuerySet(self.model, using=self._db)

    def only_deleted(self):
        """
        Только удалённые записи.
        """
        return SoftDeleteQuerySet(self.model, using=self._db).dead()


class SoftDeleteAllManager(models.Manager):
    """
    Альтернативный менеджер: ВСЕ записи, включая удалённые.
    Удобно использовать в админке или при отладке.
    """

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteModel(models.Model):
    """
    Абстрактная модель с мягким удалением.
    Наследуемся от неё вместо models.Model.
    """
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Дата/время мягкого удаления записи",
    )

    # Менеджер по умолчанию — только живые записи
    objects = SoftDeleteManager()
    # Доп. менеджер — все записи
    all_objects = SoftDeleteAllManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """
        Мягкое удаление экземпляра:
        obj.delete() -> просто проставит deleted_at.
        """
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def hard_delete(self, using=None, keep_parents=False):
        """
        Настоящее удаление строки из БД (если нужно).
        """
        return super().delete(using=using, keep_parents=keep_parents)

# Основные таблицы

class Rank(SoftDeleteModel):
    name = models.CharField(max_length=50, null=False, unique=True)
    
    def __str__(self):
	    return f"{self.name}"
    
class Role(SoftDeleteModel):
    name = models.CharField(max_length=50, null=False, unique=True)
    
    def __str__(self):
	    return f"{self.name}"
    
class DriverLicense(SoftDeleteModel):
    number = models.CharField(max_length=10, null=False, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    
    def __str__(self):
	    return f"{self.number}"
    
class User(SoftDeleteModel):
    name = models.CharField(max_length=40, null=False)
    surname = models.CharField(max_length=40, null=False)
    last_name = models.CharField(max_length=40, null=False)
    
    login = models.CharField(max_length=15, unique=True, null=False)
    password = models.CharField(max_length=300, null=False)
    phone = models.CharField(max_length=12, unique=True, null=False)
	
    rank = models.ForeignKey(Rank, on_delete=models.CASCADE, null=False, related_name='rank')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=False, related_name='role')
    driver_license = models.OneToOneField(DriverLicense, on_delete=models.CASCADE, related_name='license')
    
    def __str__(self):
	    return f"{self.name} - {self.surname} - {self.last_name} - {self.login}"
    
class RequiredRole(SoftDeleteModel):
    role = models.OneToOneField(Role, on_delete=models.CASCADE, primary_key=True, related_name='role', null=False)

class Waybill(SoftDeleteModel):
    date = models.DateField(null=False)
    from_date = models.DateField(null=False)
    for_date = models.DateField(null=False)

class Signatures(SoftDeleteModel):
    required_role = models.ForeignKey(RequiredRole, null=False, on_delete=models.CASCADE, primary_key=True, related_name='role')
    waybill = models.ForeignKey(Waybill, null=False, on_delete=models.CASCADE, primary_key=True, related_name='waybill')
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE, related_name='user')

    def __str__(self):
        return f"{self.required_role} - {self.waybill} - {self.user}"
    
class Car(SoftDeleteModel):
    number = models.CharField(max_length=9, unique=True, null=False)
    brand = models.CharField(max_length=30, null=False, help_text='марка машины')
    model = models.CharField(max_length=60, null=False)

class PassengerCar(SoftDeleteModel):
    odometer = models.DecimalField(max_digits=7, decimal_places=2, help_text='показание одометра', null=False)
    fuel = models.DecimalField(max_digits=3, decimal_places=3, help_text='показания топлива перед выездом', null=False)

    winter_area = models.DecimalField(max_digits=2, decimal_places=3, help_text='норма расхода зимой по области', null=False)
    winter_city = models.DecimalField(max_digits=2, decimal_places=3, help_text='норма расхода зимой по городу', null=False)
    summer_area = models.DecimalField(max_digits=2, decimal_places=3, help_text='норма расхода летом по области', null=False)
    summer_city = models.DecimalField(max_digits=2, decimal_places=3, help_text='норма расхода летом по городу', null=False)

    car = models.OneToOneField(Car, on_delete=models.CASCADE, null=False)

class FireTruck(SoftDeleteModel):
    odometer = models.DecimalField(max_digits=7, decimal_places=2, help_text='показание одометра', null=False)
    type = models.CharField(max_length=60, null=False)
    fuel = models.DecimalField(max_digits=3, decimal_places=3, help_text='показания топлива перед выездом', null=False)

    winter_km = models.DecimalField(max_digits=2, decimal_places=3, help_text='норма расхода зимой по км', null=False)
    winter_without_pump = models.DecimalField(max_digits=2, decimal_places=3, help_text='норма расхода зимой без насоса', null=False)
    winter_with_pump = models.DecimalField(max_digits=2, decimal_places=3, help_text='норма расхода зимой с насосом', null=False)
    summer_km = models.DecimalField(max_digits=2, decimal_places=3, help_text='норма расхода летом по км', null=False)
    summer_without_pump = models.DecimalField(max_digits=2, decimal_places=3, help_text='норма расхода летом без насоса', null=False)
    summer_with_pump = models.DecimalField(max_digits=2, decimal_places=3, help_text='норма расхода летом с насосом', null=False)

    car = models.OneToOneField(Car, on_delete=models.CASCADE, null=False)
    
class PassengerCarWaybill(SoftDeleteModel):
    waybill = models.OneToOneField(Waybill, on_delete=models.CASCADE, null=False)

class FireTruckWaybill(SoftDeleteModel):
    waybill = models.OneToOneField(Waybill, on_delete=models.CASCADE, null=False)

class FireTruckWaybillRecord(SoftDeleteModel):
    date = models.DateField(null=False)
    name = models.CharField(max_length=255, null=False)
    
