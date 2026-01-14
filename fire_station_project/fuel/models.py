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
    # Текущее показание одометра легкового авто (км)
    odometer = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=False,
        help_text="Текущее показание одометра, км",
    )

    # Текущее количество топлива в баке перед последним выездом (л)
    fuel = models.DecimalField(
        max_digits=8,         # до 99999.999 л
        decimal_places=3,
        null=False,
        help_text="Показания топлива перед выездом, л",
    )

    # ===== НОРМЫ РАСХОДА ПО МАРШРУТАМ (зима) =====

    # Норма расхода зимой по ОБЛАСТИ, л/км (или л/100 км — как у вас по методике)
    winter_area = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=False,
        help_text="Норма расхода зимой по области, л/км",
    )

    # Норма расхода зимой по ГОРОДУ, л/км
    winter_city = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=False,
        help_text="Норма расхода зимой по городу, л/км",
    )

    # ===== НОРМЫ РАСХОДА (лето) =====

    # Норма расхода летом по ОБЛАСТИ, л/км
    summer_area = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=False,
        help_text="Норма расхода летом по области, л/км",
    )

    # Норма расхода летом по ГОРОДУ, л/км
    summer_city = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=False,
        help_text="Норма расхода летом по городу, л/км",
    )

    # Связь с базовой машиной (шасси, номер и т.п.)
    car = models.OneToOneField(
        Car,
        on_delete=models.CASCADE,
        null=False,
        related_name="passenger_car",
        help_text="Базовый автомобиль, к которому относится эта легковая машина",
    )

    def __str__(self):
        return f"{self.car.number} (легковой)"

class FireTruck(SoftDeleteModel):
    # Текущее показание одометра (км).
    # Можно обновлять по последней записи карточки.
    odometer = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=False,
        help_text="Текущее показание одометра, км",
    )

    # Тип пожарного автомобиля (АЦ-3,2-40 и т.п.)
    type = models.CharField(
        max_length=60,
        null=False,
        help_text="Тип пожарного автомобиля",
    )

    # Текущее количество топлива в баке (на момент последнего выезда), л
    fuel = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=False,
        help_text="Показания топлива перед последним выездом, л",
    )

    # ===== НОРМЫ РАСХОДА ЗИМОЙ =====

    # Норма по пробегу зимой, л/км
    winter_km = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=False,
        help_text="Норма расхода зимой по пробегу, л/км",
    )

    # Норма зимой без насоса, л/ед.времени (например, л/мин или л/час)
    winter_without_pump = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=False,
        help_text="Норма расхода зимой без насоса, л/ед.времени",
    )

    # Норма зимой с насосом, л/ед.времени
    winter_with_pump = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=False,
        help_text="Норма расхода зимой с насосом, л/ед.времени",
    )

    # ===== НОРМЫ РАСХОДА ЛЕТОМ =====

    # Норма по пробегу летом, л/км
    summer_km = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=False,
        help_text="Норма расхода летом по пробегу, л/км",
    )

    # Норма летом без насоса, л/ед.времени
    summer_without_pump = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=False,
        help_text="Норма расхода летом без насоса, л/ед.времени",
    )

    # Норма летом с насосом, л/ед.времени
    summer_with_pump = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=False,
        help_text="Норма расхода летом с насосом, л/ед.времени",
    )

    # Связь с базовым автомобилем (шасси)
    car = models.OneToOneField(
        Car,
        on_delete=models.CASCADE,
        null=False,
        related_name="fire_truck",
        help_text="Базовый автомобиль, на шасси которого выполнен пожарный",
    )
    
class PassengerCarWaybill(SoftDeleteModel):
    # Связь 1:1 с общим путевым листом (шапка документа)
    waybill = models.OneToOneField(
        Waybill,
        on_delete=models.CASCADE,
        null=False,
        related_name="passenger_car_waybill",
        help_text="Путевой лист, к которому относится работа легкового автомобиля",
    )

    # Легковой автомобиль, чья работа фиксируется в этом путевом
    passenger_car = models.ForeignKey(
        PassengerCar,
        on_delete=models.PROTECT,
        null=False,
        related_name="waybills",
        help_text="Легковой автомобиль",
    )

    # Больше полей здесь не нужно: год, месяц, начальные остатки
    # можно посчитать на фронте:
    #  - year, month: из waybill.from_date
    #  - начальные остатки: по первой записи PassengerCarWaybillRecord

class FireTruckWaybill(SoftDeleteModel):
    waybill = models.OneToOneField(Waybill, on_delete=models.CASCADE, null=False)
    fire_truck = models.ForeignKey(
        FireTruck,
        on_delete=models.PROTECT,
        null=False,
        related_name="waybills",
        help_text="Пожарный автомобиль",
    )

class FireTruckWaybillRecord(SoftDeleteModel):
    # Привязка к карточке пожарного автомобиля (месяц/машина)
    fire_truck_waybill = models.ForeignKey(
        FireTruckWaybill,
        on_delete=models.CASCADE,
        null=False,
        related_name="records",
        help_text="Эксплуатационная карточка, к которой относится запись",
    )

    # (1) Дата работы автомобиля
    date = models.DateField(
        null=False,
        help_text="Дата работы пожарного автомобиля",
    )

    # (2) Наименование и место работы
    place_of_work = models.CharField(
        max_length=255,
        null=False,
        help_text="Наименование и место работы автомобиля",
    )

    # (4–5) Время выезда
    departure_time = models.TimeField(
        null=False,
        help_text="Время выезда автомобиля",
    )

    # (6–7) Время возвращения
    return_time = models.TimeField(
        null=False,
        help_text="Время возвращения автомобиля",
    )

    # (3) Наличие ГСМ перед выездом, л
    fuel_before_departure = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        help_text="Количество топлива в баке перед выездом, л",
    )

    # (8) Показания спидометра перед выездом, км
    odometer_before = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        help_text="Показание одометра перед выездом, км",
    )

    # Показания спидометра после возвращения, км
    # (в файле нет отдельной колонки, но без этого не посчитать пробег)
    odometer_after = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        help_text="Показание одометра после возвращения, км",
    )

    # ===== Время работы по видам, всё в минутах (колонки 11–18) =====

    fire_time_with_pump = models.PositiveIntegerField(
        default=0,
        help_text="Время работы на пожарах с насосом, мин",
    )
    fire_time_without_pump = models.PositiveIntegerField(
        default=0,
        help_text="Время работы на пожарах без насоса, мин",
    )

    training_time_with_pump = models.PositiveIntegerField(
        default=0,
        help_text="Время работы на учениях с насосом, мин",
    )
    training_time_without_pump = models.PositiveIntegerField(
        default=0,
        help_text="Время работы на учениях без насоса, мин",
    )

    shift_change_time_with_pump = models.PositiveIntegerField(
        default=0,
        help_text="Время работы при смене караула с насосом, мин",
    )
    shift_change_time_without_pump = models.PositiveIntegerField(
        default=0,
        help_text="Время работы при смене караула без насоса, мин",
    )

    other_time_with_pump = models.PositiveIntegerField(
        default=0,
        help_text="Прочие работы автомобиля с насосом, мин",
    )
    other_time_without_pump = models.PositiveIntegerField(
        default=0,
        help_text="Прочие работы автомобиля без насоса, мин",
    )

    # (22) Заправка за рейс, л
    fuel_refueled = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        default=0,
        help_text="Заправлено топлива за время этой записи, л",
    )

    class Meta:
        ordering = ["date", "departure_time"]

class PassengerCarWaybillRecord(SoftDeleteModel):
    # Привязка к путевому листу легкового автомобиля (шапке)
    passenger_car_waybill = models.ForeignKey(
        PassengerCarWaybill,
        on_delete=models.CASCADE,
        null=False,
        related_name="records",
        help_text="Путевой лист легкового автомобиля, к которому относится запись",
    )

    # (1) Дата работы автомобиля
    date = models.DateField(
        null=False,
        help_text="Дата работы легкового автомобиля",
    )

    # (2) Фамилия, инициалы водителя
    driver = models.ForeignKey(User, on_delete=models.CASCADE, null=False, related_name='driver', help_text='водитель')

    # (3) Наличие ГСМ перед выездом, л
    fuel_before_departure = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=False,
        help_text="Количество топлива в баке перед выездом, л",
    )

    # (8) Показания спидометра перед выездом, км
    odometer_before = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=False,
        help_text="Показание одометра перед выездом, км",
    )

    # Показания спидометра после возвращения, км
    # (в таблице нет отдельной колонки, но без этого нельзя точно посчитать пробег)
    odometer_after = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=False,
        help_text="Показание одометра после возвращения, км",
    )

   # (10) Пройдено по ГОРОДУ, км
    distance_city_km = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=False,
        help_text="Пробег по городу за поездку, км",
    )

    # (11) Пройдено по ОБЛАСТИ, км
    distance_area_km = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=False,
        help_text="Пробег по области за поездку, км",
    )

    # (17) Заправка топлива, л
    fuel_refueled = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        default=0,
        help_text="Заправлено топлива за время этой записи, л",
    )

    class Meta:
        ordering = ["date", "driver_name"]

    def __str__(self):
        return f"{self.date} — {self.driver_name}"