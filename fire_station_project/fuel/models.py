from django.db import models, transaction
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password, identify_hasher
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import date


# --- Мягкое удаление ---

class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return super().update(deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()

    def all_with_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

    def only_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db).dead()

class SoftDeleteAllManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

class SoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = SoftDeleteAllManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def hard_delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)


# --- Основные таблицы ---

# --- Общие таблицы ---
class Role(SoftDeleteModel):
    name = models.CharField(
        max_length=50,
        unique=True,
        null=False,
        help_text="название"
    )

    def __str__(self):
        return self.name

class Permission(SoftDeleteModel):
    role = models.OneToOneField(
        Role,
        on_delete=models.CASCADE,
        null=False,
        related_name="role"
    )

    can_use_mobile_booking = models.BooleanField(default=False)

    can_create_users = models.BooleanField(default=False)
    can_delete_users = models.BooleanField(default=False)
    can_update_users = models.BooleanField(default=False)
    view_users = models.BooleanField(default=False)

    can_create_fire_trucks = models.BooleanField(default=False)
    can_delete_fire_trucks = models.BooleanField(default=False)
    can_update_fire_trucks = models.BooleanField(default=False)
    view_fire_trucks = models.BooleanField(default=False)

    can_create_fire_truck_waybills = models.BooleanField(default=False)
    can_delete_fire_truck_waybills = models.BooleanField(default=False)
    can_update_fire_truck_waybills = models.BooleanField(default=False)
    can_download_fire_truck_waybills = models.BooleanField(default=False)
    view_fire_truck_waybills = models.BooleanField(default=False)

    can_create_fire_truck_waybills_record = models.BooleanField(default=False)
    can_delete_fire_truck_waybills_record = models.BooleanField(default=False)
    can_update_fire_truck_waybills_record = models.BooleanField(default=False)

    can_create_fire_truck_norms = models.BooleanField(default=False)
    can_delete_fire_truck_norms = models.BooleanField(default=False)
    can_update_fire_truck_norms = models.BooleanField(default=False)
    view_fire_truck_norms = models.BooleanField(default=False)

    can_download_fire_truck_reports = models.BooleanField(default=False)
    view_fire_truck_reports = models.BooleanField(default=False)

    can_create_passenger_cars = models.BooleanField(default=False)
    can_delete_passenger_cars = models.BooleanField(default=False)
    can_update_passenger_cars = models.BooleanField(default=False)
    view_passenger_cars = models.BooleanField(default=False)

    can_create_passenger_cars_waybills = models.BooleanField(default=False)
    can_delete_passenger_cars_waybills = models.BooleanField(default=False)
    can_update_passenger_cars_waybills = models.BooleanField(default=False)
    can_download_passenger_cars_waybills = models.BooleanField(default=False)
    view_passenger_cars_waybills = models.BooleanField(default=False)

    can_create_passenger_cars_waybills_record = models.BooleanField(default=False)
    can_delete_passenger_cars_waybills_record = models.BooleanField(default=False)
    can_update_passenger_cars_waybills_record = models.BooleanField(default=False)

    can_create_passenger_cars_norms = models.BooleanField(default=False)
    can_delete_passenger_cars_norms = models.BooleanField(default=False)
    can_update_passenger_cars_norms = models.BooleanField(default=False)
    view_passenger_cars_norms = models.BooleanField(default=False)

    can_download_passenger_cars_reports = models.BooleanField(default=False)
    view_passenger_cars_reports = models.BooleanField(default=False)

class User(SoftDeleteModel):
    name = models.CharField(
        max_length=40,
        null=False
    )

    surname = models.CharField(
        max_length=40,
        null=False
    )
    
    last_name = models.CharField(
        max_length=40,
        null=False
    )

    login = models.CharField(
        max_length=15,
        unique=True,
        null=False
    )
    
    password = models.CharField(
        max_length=300,
        null=False
    )

    phone = models.CharField(
        max_length=12,
        unique=True,
        null=False
    )

    driver_license = models.CharField(
        max_length=10,
        unique=True,
        null=True
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        null=False,
        related_name='users'
    )

    def __str__(self):
        return f"{self.surname} {self.name} {self.last_name} ({self.login})"

    # ---------- работа с паролем ----------

    def set_password(self, raw_password: str) -> None:
        self.password = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.password)

    def save(self, *args, **kwargs):
        if self.password:
            try:
                identify_hasher(self.password)
            except ValueError:
                self.password = make_password(self.password)

        super().save(*args, **kwargs)

class Season(models.TextChoices):
    WINTER = 'winter', 'Зима'
    SUMMER = 'summer', 'Лето'

class FuelType(models.TextChoices):
    PETROL = 'petrol', 'Бензин'
    DIESEL = 'diesel', 'Дизельное топливо'


# --- Таблицы легкового автомобиля ---
class PassengerCar(SoftDeleteModel):
    number = models.CharField(
        max_length=9,
        null=False,
        unique=True,
        help_text="гос. номер"
    )

    brand = models.CharField(
        null=False,
        help_text="марка"
    )

    model = models.CharField(
        null=False,
        help_text="модель"
    )

    def __str__(self):
        return f"легковой автомобиль с гос. номером {self.number} "  

class NormsPassengerCars(SoftDeleteModel):
    car = models.ForeignKey(
        PassengerCar,
        on_delete=models.CASCADE,
        related_name="norms",
    )

    season = models.CharField(
        max_length=10,
        choices=Season.choices,
        null=False,
        help_text="сезон",
    )

    city_norm = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        null=False,
        help_text="норма на 1 км по городу, л/км",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    area_norm = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        null=False,
        help_text="норма на 1 км по области, л/км",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    date = models.DateField(
        default=date.today,
        null=False,
        help_text="дата утверждения нормы",
    )

    def __str__(self):
        return f"Норма {self.car.number} {self.season} от {self.date}"

class PassengerCarWaybill(SoftDeleteModel):
    number = models.CharField(
        max_length=6,
        null=False,
        help_text="номер путевого листа",
        unique=True,
    )

    car = models.ForeignKey(
        PassengerCar,
        on_delete=models.CASCADE,
        null=False,
        related_name="waybills",
    )

    driver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="passenger_car_driver",
        null=False,
        help_text="водитель"
    )

    date = models.DateField(
        default=date.today,
        null=False,
        help_text="дата путевого листа",
    )

    norm_season = models.CharField(
        max_length=10,
        choices=Season.choices,
        null=False,
        help_text="сезон нормы"
    )

    fuel_type = models.CharField(
        max_length=10,
        choices=FuelType.choices,
        null=False,
        help_text="тип топлива"
    )

    # --- агрегатные поля (заполняются автоматически) ---

    upon_issuance = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        default=Decimal('0.000'),
        help_text="наличие ГСМ при выдаче, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    total_spent = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        default=Decimal('0.000'),
        help_text="всего израсходовано, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    total_received = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        default=Decimal('0.000'),
        help_text="всего получено (заправки), л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    required_by_norm = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        default=Decimal('0.000'),
        help_text="положено по норме, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    availability_upon_delivery = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        default=Decimal('0.000'),
        help_text="наличие при сдаче, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    savings = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        default=Decimal('0.000'),
        help_text="экономия, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    overrun = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        default=Decimal('0.000'),
        help_text="перерасход, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    def __str__(self):
        return f"Путевой лист {self.car.number} от {self.date}"

    # ---- пересчёт агрегатов ----

    def recalc_totals(self, save=True):
        """
        Пересчитать агрегатные поля на основе записей и начального состояния.
        """
        # начальное топливо (берём последнюю запись по машине на дату путевого)
        start_state = (
            OdometerFuelPassengerCar.objects
            .filter(car=self.car, date__lte=self.date)
            .order_by('-date', '-id')
            .first()
        )
        self.upon_issuance = start_state.fuel if start_state else Decimal('0.000')

        qs = self.records.all()

        agg = qs.aggregate(
            total_spent=Sum('fuel_used'),
            total_received=Sum('fuel_refueled'),
            required_by_norm=Sum('fuel_used_normal'),
        )

        self.total_spent = agg['total_spent'] or Decimal('0.000')
        self.total_received = agg['total_received'] or Decimal('0.000')
        self.required_by_norm = agg['required_by_norm'] or Decimal('0.000')

        last_record = qs.order_by('-id').first()
        self.availability_upon_delivery = (
            last_record.fuel_on_return if last_record else self.upon_issuance
        )

        # экономия / перерасход
        diff = self.required_by_norm - self.total_spent
        if diff >= 0:
            self.savings = diff
            self.overrun = Decimal('0.000')
        else:
            self.savings = Decimal('0.000')
            self.overrun = -diff

        if save:
            self.save(
                update_fields=[
                    'upon_issuance',
                    'total_spent',
                    'total_received',
                    'required_by_norm',
                    'availability_upon_delivery',
                    'savings',
                    'overrun',
                ]
            )

class PassengerCarWaybillRecord(SoftDeleteModel):
    passenger_car_waybill = models.ForeignKey(
        PassengerCarWaybill,
        on_delete=models.CASCADE,
        null=False,
        related_name="records",
        help_text="Путевой лист легкового автомобиля",
    )

    target = models.CharField(
        max_length=255,
        null=False,
        help_text="цель выезда"
    )

    departure_time = models.TimeField(
        null=False,
        help_text="время убытия"
    )

    arrival_time = models.TimeField(
        null=False,
        help_text="время прибытия"
    )

    distance_city_km = models.PositiveIntegerField(
        null=False,
        help_text="пройдено км по городу",
        validators=[MaxValueValidator(999999)]
    )

    distance_area_km = models.PositiveIntegerField(
        null=False,
        help_text="пройдено км по области",
        validators=[MaxValueValidator(999999)]
    )

    fuel_refueled = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        default=0,
        help_text="заправка, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    fuel_used = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        help_text="израсходовано топлива, л (фактически)",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    # авто-поля (как раньше)
    odometer_after = models.PositiveIntegerField(
        null=False,
        editable=False,
        help_text="одометр после возвращения, км",
        validators=[MaxValueValidator(999999)]
    )

    fuel_before_departure = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        help_text="топливо перед выездом, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    odometer_before = models.PositiveIntegerField(
        null=False,
        editable=False,
        help_text="одометр перед выездом, км",
        validators=[MaxValueValidator(999999)]
    )

    distance_total_km = models.PositiveIntegerField(
        null=False,
        editable=False,
        help_text="всего пройдено км",
        validators=[MaxValueValidator(999999)]
    )

    fuel_used_city = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        help_text="израсходовано по городу, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    fuel_used_area = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        help_text="израсходовано по области, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    fuel_on_return = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        help_text="остаток топлива при возвращении, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    fuel_used_normal = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        help_text="израсходовано по норме, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    class Meta:
        ordering = ["id"]

    # ------------ внутренняя логика ------------

    def _fill_start_values(self):
        """
        odometer_before / fuel_before_departure берём из ПОСЛЕДНЕЙ записи
        OdometerFuelPassengerCar по этой машине.
        """
        wb = self.passenger_car_waybill
        car = wb.car

        last_state = (
            OdometerFuelPassengerCar.objects
            .filter(car=car)
            .order_by('-date', '-id')
            .first()
        )
        if not last_state:
            raise ValidationError(
                f"Не найдены последние показания одометра/топлива для {car.number}. "
                "Сначала создайте запись в OdometerFuelPassengerCar."
            )

        self.odometer_before = last_state.odometer
        self.fuel_before_departure = last_state.fuel

    def _apply_norms(self):
        """
        Тот же расчёт, который у тебя уже был:
        - distance_total_km = distance_city_km + distance_area_km
        - odometer_after = odometer_before + distance_total_km
        - fuel_used_city/area по нормам из NormsPassengerCars (по сезону и дате)
        """
        wb = self.passenger_car_waybill
        car = wb.car

        from .models import NormsPassengerCars  # локальный импорт, если нужно

        norm = (
            NormsPassengerCars.objects
            .filter(
                car=car,
                season=wb.norm_season,
                date__lte=wb.date,
            )
            .order_by('-date', '-id')
            .first()
        )
        if not norm:
            raise ValidationError(
                f"Не найдена норма для {car.number}, сезон={wb.norm_season}"
            )

        self.distance_total_km = self.distance_city_km + self.distance_area_km
        self.odometer_after = self.odometer_before + self.distance_total_km

        self.fuel_used_city = Decimal(self.distance_city_km) * norm.city_norm
        self.fuel_used_area = Decimal(self.distance_area_km) * norm.area_norm
        self.fuel_used_normal = (self.fuel_used_city or 0) + (self.fuel_used_area or 0)

    def _calc_fuel_on_return(self):
        """
        Остаток топлива = до выезда - фактический расход + заправка.
        """
        self.fuel_on_return = (
            (self.fuel_before_departure or Decimal('0.000'))
            - (self.fuel_used or Decimal('0.000'))
            + (self.fuel_refueled or Decimal('0.000'))
        )

    def save(self, *args, **kwargs):
        from .models import OdometerFuelPassengerCar  # чтобы не было циклов
        with transaction.atomic():
            self._fill_start_values()
            self._apply_norms()
            self._calc_fuel_on_return()
            super().save(*args, **kwargs)

            # создаём новый снимок в OdometerFuelPassengerCar
            OdometerFuelPassengerCar.objects.create(
                car=self.passenger_car_waybill.car,
                odometer=self.odometer_after,
                fuel=self.fuel_on_return,
                date=self.passenger_car_waybill.date,  # или date.today()
                waybill=self.passenger_car_waybill,
            )

            # пересчёт агрегатов по путевому
            self.passenger_car_waybill.recalc_totals()

class OdometerFuelPassengerCar(SoftDeleteModel):
    car = models.ForeignKey(
        PassengerCar,
        on_delete=models.CASCADE,
        related_name="odometer_fuel_records",
        null=False,
        blank=True,   # можно не заполнять в форме, если есть waybill
        help_text="автомобиль",
    )

    odometer = models.PositiveIntegerField(
        null=False,
        blank=True,   # можно не заполнять в форме, если есть waybill
        help_text="показания одометра, км",
        validators=[MaxValueValidator(999999)]
    )

    fuel = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        blank=True,   # можно не заполнять в форме, если есть waybill
        help_text="остаток топлива, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    date = models.DateField(
        default=date.today,
        null=False,
        help_text="дата состояния",
    )

    waybill = models.ForeignKey(
        PassengerCarWaybill,
        on_delete=models.CASCADE,
        related_name="odometer_fuel_states",
        null=True,
        blank=True,   # можно без путевого, тогда всё вручную
        help_text="путевой лист (если указан, данные подтянутся автоматически)",
    )

    def clean(self):
        """
        Логика:
        - если waybill указан:
            - car берём из waybill.car, если не указан;
            - если odometer/fuel не заданы — пытаемся взять из последней записи waybill'a;
            - если у waybill'a нет записей и одометр/топливо не указаны вручную — ошибка.
        - если waybill НЕ указан:
            - car, odometer, fuel ОБЯЗАТЕЛЬНЫ.
        """
        super().clean()

        # если указан путевой лист
        if self.waybill_id:
            # подтягиваем машину из путевого, если не указана
            if self.car_id is None:
                self.car = self.waybill.car

            # ищем последнюю запись по этому путевому
            last_rec = (
                self.waybill.records
                .order_by('-id')
                .first()
            )

            # если нет записей и пользователь не указал значения — ошибка
            if last_rec is None and (self.odometer is None or self.fuel is None):
                raise ValidationError(
                    "У путевого листа нет записей. "
                    "Укажите одометр и остаток топлива вручную, либо создайте записи."
                )

            # если одометр не указан — берём из последней записи
            if self.odometer is None and last_rec is not None:
                self.odometer = last_rec.odometer_after

            # если топливо не указано — берём из последней записи
            if self.fuel is None and last_rec is not None:
                self.fuel = last_rec.fuel_on_return

            # если дату не указали — можно взять из путевого или последней записи
            if self.date is None:
                self.date = last_rec.arrival_time.date() if last_rec else self.waybill.date

        else:
            # waybill НЕ указан → всё вручную
            errors = {}
            if self.car_id is None:
                errors['car'] = "Обязательно, если не указан путевой лист"
            if self.odometer is None:
                errors['odometer'] = "Обязательно, если не указан путевой лист"
            if self.fuel is None:
                errors['fuel'] = "Обязательно, если не указан путевой лист"

            if errors:
                raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # гарантируем, что перед сохранением срабатывает clean()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.car.number} {self.date}: {self.odometer} км, {self.fuel} л"    
    


# --- Таблицы пожарного автомобиля ---
class FireTruck(SoftDeleteModel):
    number = models.CharField(
        max_length=9,
        null=False,
        unique=True,
        help_text="гос. номер"
    )

    brand = models.CharField(
        max_length=60,
        null=False,
        help_text="марка"
    )

    model = models.CharField(
        max_length=60,
        null=False,
        help_text="модель"
    )

    type = models.CharField(
        max_length=60,
        null=False,
        help_text="тип"
    )

    def __str__(self):
        return f"Пожарный автомобиль с гос. номером {self.number}"
    
class NormsFireTruck(SoftDeleteModel):
    car = models.ForeignKey(
        FireTruck,
        on_delete=models.CASCADE,
        related_name="norms",
    )

    season = models.CharField(
        max_length=10,
        choices=Season.choices,
        null=False,
        help_text="сезон"
    )

    with_pump_norm = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        help_text="норма с насосом, л/мин (или др.ед.)",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    without_pump_norm = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        help_text="норма без насоса, л/мин (или др.ед.)",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    km_norm = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        help_text="норма по пробегу, л/км",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    date = models.DateField(
        default=date.today,
        null=False,
        help_text="дата утверждения нормы"
    )

    def __str__(self):
        return f"Норма {self.car.number} {self.season} от {self.date}"

class FireTruckWaybill(SoftDeleteModel):
    number = models.CharField(
        max_length=6,
        null=False,
        help_text="номер путевого листа",
        unique=True,
    )

    car = models.ForeignKey(
        FireTruck,
        null=False,
        on_delete=models.CASCADE,
        related_name="waybills",
    )

    driver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="fire_truck_driver",
        null=False,
        help_text="водитель"
    )

    date = models.DateField(
        default=date.today,
        null=False,
        help_text="дата путевого листа",
    )

    norm_season = models.CharField(
        max_length=10,
        choices=Season.choices,
        null=False,
        help_text="сезон нормы"
    )

    fuel_type = models.CharField(
        max_length=10,
        choices=FuelType.choices,
        null=False,
        help_text="тип топлива"
    )

    # агрегаты (как у легковой)

    upon_issuance = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        default=Decimal('0.000'),
        help_text="наличие ГСМ при выдаче, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )
    total_spent = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        default=Decimal('0.000'),
        help_text="всего израсходовано, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )
    total_received = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        default=Decimal('0.000'),
        help_text="всего получено (заправки), л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )
    required_by_norm = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        default=Decimal('0.000'),
        help_text="положено по норме, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )
    availability_upon_delivery = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        default=Decimal('0.000'),
        help_text="наличие при сдаче, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )
    savings = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        default=Decimal('0.000'),
        help_text="экономия, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )
    overrun = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        default=Decimal('0.000'),
        help_text="перерасход, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    def __str__(self):
        return f"Путевой лист ПА {self.car.number} от {self.date}"

    def recalc_totals(self, save=True):
        start_state = (
            OdometerFuelFireTruck.objects
            .filter(car=self.car, date__lte=self.date)
            .order_by('-date', '-id')
            .first()
        )
        self.upon_issuance = start_state.fuel if start_state else Decimal('0.000')

        qs = self.records.all()
        agg = qs.aggregate(
            total_spent=Sum('fuel_used'),
            total_received=Sum('fuel_refueled'),
            required_by_norm=Sum('fuel_used_normal'),
        )

        self.total_spent = agg['total_spent'] or Decimal('0.000')
        self.total_received = agg['total_received'] or Decimal('0.000')
        self.required_by_norm = agg['required_by_norm'] or Decimal('0.000')

        last_record = qs.order_by('-id').first()
        self.availability_upon_delivery = (
            last_record.fuel_on_return if last_record else self.upon_issuance
        )

        diff = self.required_by_norm - self.total_spent
        if diff >= 0:
            self.savings = diff
            self.overrun = Decimal('0.000')
        else:
            self.savings = Decimal('0.000')
            self.overrun = -diff

        if save:
            self.save(update_fields=[
                'upon_issuance', 'total_spent', 'total_received',
                'required_by_norm', 'availability_upon_delivery',
                'savings', 'overrun'
            ])
    
class FireTruckWaybillRecord(SoftDeleteModel):
    fire_truck_waybill = models.ForeignKey(
        FireTruckWaybill,
        on_delete=models.CASCADE,
        null=False,
        related_name="records",
        help_text="Эксплуатационная карточка",
    )

    target = models.CharField(
        max_length=255,
        null=False,
        help_text="цель выезда"
    )

    departure_time = models.TimeField(
        null=False,
        help_text="время убытия"
    )

    arrival_time = models.TimeField(
        null=False,
        help_text="время прибытия"
    )

    odometer_after = models.PositiveIntegerField(
        null=False,
        help_text="одометр после возвращения, км",
        validators=[MaxValueValidator(999999)]
    )

    time_with_pump = models.PositiveIntegerField(
        null=False,
        help_text="время работы с насосом, мин",
        validators=[MaxValueValidator(999999)]
    )

    time_without_pump = models.PositiveIntegerField(
        null=False,
        help_text="время работы без насоса, мин",
        validators=[MaxValueValidator(999999)]
    )

    fuel_refueled = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        default=0,
        help_text="заправка, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    fuel_used = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        help_text="фактически израсходовано, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    # автоматические поля
    fuel_before_departure = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        help_text="топливо перед выездом, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    odometer_before = models.PositiveIntegerField(
        null=False,
        editable=False,
        help_text="одометр перед выездом, км",
        validators=[MaxValueValidator(999999)]
    )

    distance_km = models.PositiveIntegerField(
        null=False,
        editable=False,
        help_text="пробег, км",
        validators=[MaxValueValidator(999999)]
    )

    fuel_on_return = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        help_text="остаток топлива при возвращении, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    fuel_used_by_distance = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        help_text="Топливо по пробегу, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    fuel_used_with_pump = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        help_text="Топливо при работе с насосом, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    fuel_used_without_pump = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        help_text="Топливо при работе без насоса, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    fuel_used_normal = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        editable=False,
        help_text="израсходовано по норме, л",
        validators=[MinValueValidator(Decimal('0.000'))]
    )

    class Meta:
        ordering = ["id"]

    def _fill_start_values(self):
        wb = self.fire_truck_waybill
        car = wb.car

        last_state = (
            OdometerFuelFireTruck.objects
            .filter(car=car)
            .order_by('-date', '-id')
            .first()
        )
        if not last_state:
            raise ValidationError(
                f"Не найдены последние показания для ПА {car.number}. "
                "Сначала создайте запись в OdometerFuelFireTruck."
            )

        self.odometer_before = last_state.odometer
        self.fuel_before_departure = last_state.fuel

    def _apply_norms(self):
        wb = self.fire_truck_waybill
        car = wb.car

        norm = (
            NormsFireTruck.objects
            .filter(car=car, season=wb.norm_season, date__lte=wb.date)
            .order_by('-date', '-id')
            .first()
        )
        if not norm:
            raise ValidationError(
                f"Не найдена норма для ПА {car.number}, сезон={wb.norm_season}"
            )

        self.distance_km = self.odometer_after - self.odometer_before

        self.fuel_used_by_distance = Decimal(self.distance_km) * norm.km_norm
        self.fuel_used_with_pump = Decimal(self.time_with_pump) * norm.with_pump_norm
        self.fuel_used_without_pump = Decimal(self.time_without_pump) * norm.without_pump_norm

        self.fuel_used_normal = (
            (self.fuel_used_by_distance or 0) +
            (self.fuel_used_with_pump or 0) +
            (self.fuel_used_without_pump or 0)
        )

    def _calc_fuel_on_return(self):
        self.fuel_on_return = (
            (self.fuel_before_departure or Decimal('0.000'))
            - (self.fuel_used or Decimal('0.000'))
            + (self.fuel_refueled or Decimal('0.000'))
        )

    def save(self, *args, **kwargs):
        from .models import OdometerFuelFireTruck
        with transaction.atomic():
            self._fill_start_values()
            self._apply_norms()
            self._calc_fuel_on_return()
            super().save(*args, **kwargs)

            OdometerFuelFireTruck.objects.create(
                car=self.fire_truck_waybill.car,
                odometer=self.odometer_after,
                fuel=self.fuel_on_return,
                date=self.fire_truck_waybill.date,
                waybill=self.fire_truck_waybill,
            )

            self.fire_truck_waybill.recalc_totals()

class OdometerFuelFireTruck(SoftDeleteModel):
    car = models.ForeignKey(
        FireTruck,
        on_delete=models.CASCADE,
        related_name="odometer_fuel_records",
        null=False,
        blank=True,
    )
    odometer = models.PositiveIntegerField(
        null=False,
        blank=True,
        validators=[MaxValueValidator(999999)]
    )
    fuel = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=False,
        blank=True,
        validators=[MinValueValidator(Decimal('0.000'))]
    )
    date = models.DateField(
        default=date.today,
        null=False,
    )
    waybill = models.ForeignKey(
        FireTruckWaybill,
        on_delete=models.CASCADE,
        related_name="odometer_fuel_states",
        null=True,
        blank=True,
    )

    def clean(self):
        super().clean()

        if self.waybill_id:
            if self.car_id is None:
                self.car = self.waybill.car

            last_rec = (
                self.waybill.records
                .order_by('-id')
                .first()
            )

            if last_rec is None and (self.odometer is None or self.fuel is None):
                raise ValidationError(
                    "У путевого листа ПА нет записей. "
                    "Укажите одометр и топливо вручную, либо создайте записи."
                )

            if self.odometer is None and last_rec is not None:
                self.odometer = last_rec.odometer_after

            if self.fuel is None and last_rec is not None:
                self.fuel = last_rec.fuel_on_return

            if self.date is None:
                self.date = self.waybill.date
        else:
            errors = {}
            if self.car_id is None:
                errors['car'] = "Обязательно, если не указан путевой лист"
            if self.odometer is None:
                errors['odometer'] = "Обязательно, если не указан путевой лист"
            if self.fuel is None:
                errors['fuel'] = "Обязательно, если не указан путевой лист"

            if errors:
                raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.car.number} {self.date}: {self.odometer} км, {self.fuel} л"