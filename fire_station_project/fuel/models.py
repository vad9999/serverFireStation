# models.py
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password, identify_hasher


# --- Soft delete ---

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


# --- Основные справочники ---

class Rank(SoftDeleteModel):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Role(SoftDeleteModel):
    name = models.CharField(max_length=50, unique=True)
    can_use_mobile_booking = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class RoleSubstitution(SoftDeleteModel):
    """
    substitute_role может подписывать вместо main_role.
    """
    main_role = models.ForeignKey(
        Role, on_delete=models.CASCADE,
        related_name='substituted_by',
    )
    substitute_role = models.ForeignKey(
        Role, on_delete=models.CASCADE,
        related_name='can_substitute_for',
    )

    class Meta:
        unique_together = ('main_role', 'substitute_role')

    def __str__(self):
        return f"{self.substitute_role} за {self.main_role}"

class DriverLicense(SoftDeleteModel):
    number = models.CharField(max_length=10, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.number

class User(SoftDeleteModel):
    name = models.CharField(max_length=40, null=False)
    surname = models.CharField(max_length=40, null=False)
    last_name = models.CharField(max_length=40, null=False)

    login = models.CharField(max_length=15, unique=True, null=False)
    password = models.CharField(max_length=300, null=False)
    phone = models.CharField(max_length=12, unique=True, null=False)

    rank = models.ForeignKey(Rank, on_delete=models.CASCADE, null=False, related_name='users')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=False, related_name='users')
    driver_license = models.OneToOneField(DriverLicense, on_delete=models.CASCADE, related_name='user')

    def __str__(self):
        return f"{self.surname} {self.name} {self.last_name} ({self.login})"

    # ---------- работа с паролем ----------

    def set_password(self, raw_password: str) -> None:
        """
        Установить пароль пользователю (с хешированием).
        """
        self.password = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """
        Проверить пароль.
        """
        return check_password(raw_password, self.password)

    def save(self, *args, **kwargs):
        """
        Автоматически захешировать пароль, если он ещё в открытом виде.
        Это на случай, если кто-то присвоил self.password вручную.
        """
        if self.password:
            try:
                # если пароль уже в виде хеша, identify_hasher его "узнает"
                identify_hasher(self.password)
            except ValueError:
                # не смогли распознать хеш — считаем, что это raw_password
                self.password = make_password(self.password)

        super().save(*args, **kwargs)
    
class RequiredRole(SoftDeleteModel):
    """
    Роль, подпись которой ОБЯЗАТЕЛЬНА для любого путевого листа.
    """
    role = models.OneToOneField(
        Role,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='required_role_meta',
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Обязательная роль: {self.role.name}"

class Waybill(SoftDeleteModel):
    date = models.DateField()
    from_date = models.DateField()
    for_date = models.DateField()
    number = models.PositiveBigIntegerField(null=False)

    def __str__(self):
        return f"Путевой лист от {self.date} - {self.number}"

class Signature(SoftDeleteModel):
    """
    Фактическая подпись под путевым листом.
    """

    waybill = models.ForeignKey(
        Waybill,
        on_delete=models.CASCADE,
        null=False,
        related_name='signatures',
        help_text="Путевой лист, который подписывается",
    )

    required_role = models.ForeignKey(
        RequiredRole,
        on_delete=models.CASCADE,
        null=False,
        related_name='signatures',
        help_text="Какую обязательную роль закрывает эта подпись",
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=False,
        related_name='signatures',
        help_text="Пользователь, который поставил подпись",
    )

    signed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Дата и время, когда подпись была поставлена",
    )

    class Meta:
        # один слот обязательной роли по одному путевому листу — одна строка
        unique_together = ('waybill', 'required_role')

    def __str__(self):
        return f"{self.waybill_id}: {self.user} за {self.required_role.role.name}"

    # -------- ВАЛИДАЦИЯ ЧЕРЕЗ services.can_user_sign_required_role --------

    def clean(self):
        """
        Проверка, что self.user имеет право подписать слот self.required_role.
        Логика вынесена в services.can_user_sign_required_role.
        """
        super().clean()

        # если объект ещё не до конца заполнен (например, в админке) — пропускаем
        if not self.user_id or not self.required_role_id:
            return

        from .services import can_user_sign_required_role  # локальный импорт, без циклов

        if not can_user_sign_required_role(self.user, self.required_role):
            raise ValidationError("У этого пользователя нет права подписать этот слот")

    def save(self, *args, **kwargs):
        # full_clean вызывает clean() + проверяет типы полей
        self.full_clean()
        return super().save(*args, **kwargs)
    
class Car(SoftDeleteModel):
    number = models.CharField(max_length=9, unique=True)
    brand = models.CharField(max_length=30, help_text='марка машины')
    model = models.CharField(max_length=60)

    def __str__(self):
        return f"{self.number} ({self.brand} {self.model})"
    
class PassengerCar(SoftDeleteModel):
    odometer = models.DecimalField(max_digits=7, decimal_places=2,
                                   help_text="Текущее показание одометра, км")
    fuel = models.DecimalField(max_digits=8, decimal_places=3,
                               help_text="Показания топлива перед выездом, л")

    winter_area = models.DecimalField(max_digits=5, decimal_places=3,
                                      help_text="Норма зимой по области, л/км")
    winter_city = models.DecimalField(max_digits=5, decimal_places=3,
                                      help_text="Норма зимой по городу, л/км")
    summer_area = models.DecimalField(max_digits=5, decimal_places=3,
                                      help_text="Норма летом по области, л/км")
    summer_city = models.DecimalField(max_digits=5, decimal_places=3,
                                      help_text="Норма летом по городу, л/км")

    car = models.OneToOneField(
        Car, on_delete=models.CASCADE,
        related_name="passenger_car",
    )

    def __str__(self):
        return f"{self.car.number} (легковой)"
    
class FireTruck(SoftDeleteModel):
    odometer = models.DecimalField(max_digits=7, decimal_places=2,
                                   help_text="Текущее показание одометра, км")
    type = models.CharField(max_length=60, help_text="Тип пожарного автомобиля")
    fuel = models.DecimalField(max_digits=8, decimal_places=3,
                               help_text="Показания топлива перед последним выездом, л")

    winter_km = models.DecimalField(max_digits=5, decimal_places=3,
                                    help_text="Норма зимой по пробегу, л/км")
    winter_without_pump = models.DecimalField(max_digits=5, decimal_places=3,
                                              help_text="Норма зимой без насоса, л/ед.времени")
    winter_with_pump = models.DecimalField(max_digits=5, decimal_places=3,
                                           help_text="Норма зимой с насосом, л/ед.времени")

    summer_km = models.DecimalField(max_digits=5, decimal_places=3,
                                    help_text="Норма летом по пробегу, л/км")
    summer_without_pump = models.DecimalField(max_digits=5, decimal_places=3,
                                              help_text="Норма летом без насоса, л/ед.времени")
    summer_with_pump = models.DecimalField(max_digits=5, decimal_places=3,
                                           help_text="Норма летом с насосом, л/ед.времени")

    car = models.OneToOneField(
        Car, on_delete=models.CASCADE,
        related_name="fire_truck",
    )

    def __str__(self):
        return f"{self.car.number} ({self.type})"
    
class Season(models.TextChoices):
    WINTER = 'winter', 'Зимняя норма'
    SUMMER = 'summer', 'Летняя норма'

class PassengerCarWaybill(SoftDeleteModel):
    waybill = models.OneToOneField(
        Waybill,
        on_delete=models.CASCADE,
        related_name="passenger_car_waybill",
    )
    passenger_car = models.ForeignKey(
        PassengerCar,
        on_delete=models.PROTECT,
        related_name="waybills",
    )

class PassengerCarWaybillRecord(SoftDeleteModel):
    # Шапка путевого листа
    passenger_car_waybill = models.ForeignKey(
        PassengerCarWaybill,
        on_delete=models.CASCADE,
        null=False,
        related_name="records",
        help_text="Путевой лист легкового автомобиля, к которому относится запись",
    )

    # Дата и водитель
    date = models.DateField(
        null=False,
        help_text="Дата работы легкового автомобиля",
    )
    driver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=False,
        related_name='driving_records',
        help_text='Водитель',
    )

    # ------ ПОЛЯ, КОТОРЫЕ ВВОДИТ ПОЛЬЗОВАТЕЛЬ ------

    # Показание одометра ПОСЛЕ возвращения, км
    odometer_after = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=False,
        help_text="Показание одометра после возвращения, км",
    )

    # Пробег по городу и по области (водитель/механик вводят вручную)
    distance_city_km = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=False,
        help_text="Пробег по городу за поездку, км",
    )
    distance_area_km = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=False,
        help_text="Пробег по области за поездку, км",
    )

    # Заправка топлива за поездку, л
    fuel_refueled = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        default=0,
        help_text="Заправлено топлива за время этой записи, л",
    )

    # Сезон (по нему выбираем нормы)
    season = models.CharField(
        max_length=10,
        choices=Season.choices,
        default=Season.SUMMER,
        help_text="Какую норму применить для расчёта (зимняя/летняя)",
    )

    # ------ ПОЛЯ, КОТОРЫЕ ЗАПОЛНЯЮТСЯ АВТОМАТИЧЕСКИ ------

    # Наличие ГСМ перед выездом, л
    fuel_before_departure = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        editable=False,
        help_text="Количество топлива в баке перед выездом, л (автоматически)",
    )

    # Одометр ПЕРЕД выездом, км
    odometer_before = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False,
        help_text="Показание одометра перед выездом, км (автоматически)",
    )

    # Слепок норм, использованных при расчёте
    norm_city = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        editable=False,
        help_text="Норма по городу, л/км, применённая для этой записи",
    )
    norm_area = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        editable=False,
        help_text="Норма по области, л/км, применённая для этой записи",
    )

    # Вычисляемые итоговые поля
    distance_total_km = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False,
        help_text="Общий пробег за поездку, км",
    )
    fuel_used_city = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        editable=False,
        help_text="Израсходовано топлива по городу, л",
    )
    fuel_used_area = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        editable=False,
        help_text="Израсходовано топлива по области, л",
    )
    fuel_used_total = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        editable=False,
        help_text="Всего израсходовано топлива, л",
    )
    fuel_on_return = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        editable=False,
        help_text="Остаток топлива в баке при возвращении, л",
    )

    class Meta:
        ordering = ["date", "driver_id"]

    def __str__(self):
        return f"{self.date} — {self.driver}"

    # --------- СЛУЖЕБНЫЕ МЕТОДЫ ДЛЯ РАСЧЁТА ---------

    def _fill_start_values(self):
        """
        Заполнить odometer_before и fuel_before_departure,
        если они ещё не заданы (новая запись).
        Берём их:
        - из предыдущей записи этого же путевого листа;
        - или из текущего состояния PassengerCar.
        """
        if self.odometer_before is not None and self.fuel_before_departure is not None:
            return

        car = self.passenger_car_waybill.passenger_car

        # предыдущая запись данного путевого
        last = (
            PassengerCarWaybillRecord.objects
            .filter(passenger_car_waybill=self.passenger_car_waybill)
            .exclude(pk=self.pk)
            .order_by('-date', '-id')
            .first()
        )

        if last:
            self.odometer_before = last.odometer_after
            self.fuel_before_departure = last.fuel_on_return
        else:
            # первая запись для этого путевого — берём из машины
            self.odometer_before = car.odometer
            self.fuel_before_departure = car.fuel

    def _recalc(self):
        """
        Пересчитать нормы и расход по пробегу.
        """
        car = self.passenger_car_waybill.passenger_car

        # Выбор норм по сезону
        if self.season == Season.WINTER:
            self.norm_city = car.winter_city
            self.norm_area = car.winter_area
        else:
            self.norm_city = car.summer_city
            self.norm_area = car.summer_area

        # Общий пробег
        self.distance_total_km = (self.distance_city_km or 0) + (self.distance_area_km or 0)

        # Расход по город/область
        self.fuel_used_city = (self.distance_city_km or 0) * (self.norm_city or 0)
        self.fuel_used_area = (self.distance_area_km or 0) * (self.norm_area or 0)
        self.fuel_used_total = (self.fuel_used_city or 0) + (self.fuel_used_area or 0)

        # Остаток топлива при возвращении
        self.fuel_on_return = (
            (self.fuel_before_departure or 0) +
            (self.fuel_refueled or 0) -
            (self.fuel_used_total or 0)
        )

    def _update_car_state(self):
        """
        Обновить одометр и остаток топлива у PassengerCar
        по результатам этой записи.
        """
        car = self.passenger_car_waybill.passenger_car

        # Одометр: всегда берём максимальное значение
        if self.odometer_after and self.odometer_after > (car.odometer or 0):
            car.odometer = self.odometer_after

        # Остаток топлива = fuel_on_return последней записи по факту
        if self.fuel_on_return is not None:
            car.fuel = self.fuel_on_return

        car.save(update_fields=['odometer', 'fuel'])

    def save(self, *args, **kwargs):
        with transaction.atomic():
            self._fill_start_values()
            self._recalc()
            super().save(*args, **kwargs)
            self._update_car_state()
    
class FireTruckWaybill(SoftDeleteModel):
    waybill = models.OneToOneField(
        Waybill, on_delete=models.CASCADE,
        related_name='fire_truck_waybill',
    )
    fire_truck = models.ForeignKey(
        FireTruck,
        on_delete=models.PROTECT,
        related_name="waybills",
    )

class FireTruckWaybillRecord(SoftDeleteModel):
    fire_truck_waybill = models.ForeignKey(
        FireTruckWaybill,
        on_delete=models.CASCADE,
        null=False,
        related_name="records",
        help_text="Эксплуатационная карточка, к которой относится запись",
    )

    # Базовая информация
    date = models.DateField(
        null=False,
        help_text="Дата работы пожарного автомобиля",
    )
    place_of_work = models.CharField(
        max_length=255,
        null=False,
        help_text="Наименование и место работы автомобиля",
    )
    departure_time = models.TimeField(
        null=False,
        help_text="Время выезда автомобиля",
    )
    return_time = models.TimeField(
        null=False,
        help_text="Время возвращения автомобиля",
    )

    # -------- ПОЛЯ, КОТОРЫЕ ВВОДИТ ПОЛЬЗОВАТЕЛЬ --------

    # Показание одометра ПОСЛЕ возвращения, км
    odometer_after = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=False,
        help_text="Показание одометра после возвращения, км",
    )

    # Заправка за рейс, л
    fuel_refueled = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        default=0,
        help_text="Заправлено топлива за время этой записи, л",
    )

    # Время работы, мин (всё вводит пользователь)
    fire_time_with_pump = models.PositiveIntegerField(default=0)
    fire_time_without_pump = models.PositiveIntegerField(default=0)
    training_time_with_pump = models.PositiveIntegerField(default=0)
    training_time_without_pump = models.PositiveIntegerField(default=0)
    shift_change_time_with_pump = models.PositiveIntegerField(default=0)
    shift_change_time_without_pump = models.PositiveIntegerField(default=0)
    other_time_with_pump = models.PositiveIntegerField(default=0)
    other_time_without_pump = models.PositiveIntegerField(default=0)

    # Сезон (по нему выбираем нормы из FireTruck)
    season = models.CharField(
        max_length=10,
        choices=Season.choices,
        default=Season.SUMMER,
        help_text="Какую норму применить (зимняя/летняя)",
    )

    # -------- ПОЛЯ, ЗАПОЛНЯЕМЫЕ АВТОМАТИЧЕСКИ --------

    # Топливо и одометр ПЕРЕД выездом
    fuel_before_departure = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        editable=False,
        help_text="Топливо перед выездом, л (автоматически)",
    )
    odometer_before = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False,
        help_text="Одометр перед выездом, км (автоматически)",
    )

    # Слепок норм расхода, применённых к ЭТОЙ записи
    norm_km = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        editable=False,
        help_text="Норма по пробегу, л/км, применённая к записи",
    )
    norm_without_pump = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        editable=False,
        help_text="Норма без насоса, л/ед.времени, применённая к записи",
    )
    norm_with_pump = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        editable=False,
        help_text="Норма с насосом, л/ед.времени, применённая к записи",
    )

    # Вычисляемые пробег и расход
    distance_km = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False,
        help_text="Пробег за поездку, км",
    )
    fuel_used_by_distance = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        editable=False,
        help_text="Топливо по пробегу, л",
    )
    fuel_used_with_pump = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        editable=False,
        help_text="Топливо при работе с насосом, л",
    )
    fuel_used_without_pump = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        editable=False,
        help_text="Топливо при работе без насоса, л",
    )
    fuel_used_total = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        editable=False,
        help_text="Всего израсходовано топлива, л",
    )
    fuel_on_return = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        editable=False,
        help_text="Остаток топлива в баке при возвращении, л",
    )

    class Meta:
        ordering = ["date", "departure_time"]

    # ---------- ВНУТРЕННЯЯ ЛОГИКА ----------

    def _fill_start_values(self):
        """
        Заполнить odometer_before и fuel_before_departure, если они ещё не заданы.
        Берём их:
        - из предыдущей записи по этому же FireTruckWaybill;
        - или из текущего состояния FireTruck (первая запись).
        """
        if self.odometer_before is not None and self.fuel_before_departure is not None:
            return

        truck = self.fire_truck_waybill.fire_truck

        last = (
            FireTruckWaybillRecord.objects
            .filter(fire_truck_waybill=self.fire_truck_waybill)
            .exclude(pk=self.pk)
            .order_by('-date', '-departure_time', '-pk')
            .first()
        )

        if last:
            self.odometer_before = last.odometer_after
            self.fuel_before_departure = last.fuel_on_return
        else:
            # первая запись по этому путевому листу
            self.odometer_before = truck.odometer
            self.fuel_before_departure = truck.fuel

    def _recalc(self):
        """
        Пересчитать нормы и расход по нормам машины и введённым минутам/одометру.
        """
        truck = self.fire_truck_waybill.fire_truck

        # выбор норм по сезону
        if self.season == Season.WINTER:
            self.norm_km = truck.winter_km
            self.norm_with_pump = truck.winter_with_pump
            self.norm_without_pump = truck.winter_without_pump
        else:
            self.norm_km = truck.summer_km
            self.norm_with_pump = truck.summer_with_pump
            self.norm_without_pump = truck.summer_without_pump

        # пробег
        self.distance_km = (self.odometer_after or 0) - (self.odometer_before or 0)

        # суммарное время с/без насоса
        minutes_with_pump = (
            self.fire_time_with_pump +
            self.training_time_with_pump +
            self.shift_change_time_with_pump +
            self.other_time_with_pump
        )
        minutes_without_pump = (
            self.fire_time_without_pump +
            self.training_time_without_pump +
            self.shift_change_time_without_pump +
            self.other_time_without_pump
        )

        # считаем расход (предполагаем, что norm_* указаны в "л за 1 минуту")
        self.fuel_used_by_distance = self.distance_km * (self.norm_km or 0)
        self.fuel_used_with_pump = minutes_with_pump * (self.norm_with_pump or 0)
        self.fuel_used_without_pump = minutes_without_pump * (self.norm_without_pump or 0)

        self.fuel_used_total = (
            (self.fuel_used_by_distance or 0) +
            (self.fuel_used_with_pump or 0) +
            (self.fuel_used_without_pump or 0)
        )

        self.fuel_on_return = (
            (self.fuel_before_departure or 0) +
            (self.fuel_refueled or 0) -
            (self.fuel_used_total or 0)
        )

    def _update_truck_state(self):
        """
        Обновить одометр и остаток топлива у FireTruck по этой записи.
        - одометр всегда растёт: ставим max(старое, odometer_after);
        - топливо = остаток после последнего рейса (fuel_on_return).
        """
        truck = self.fire_truck_waybill.fire_truck

        # обновляем одометр только если новое показание больше (не уменьшаем)
        if self.odometer_after and self.odometer_after > (truck.odometer or 0):
            truck.odometer = self.odometer_after

        # остаток топлива — по последней записи
        if self.fuel_on_return is not None:
            truck.fuel = self.fuel_on_return

        truck.save(update_fields=['odometer', 'fuel'])

    def save(self, *args, **kwargs):
        with transaction.atomic():
            self._fill_start_values()
            self._recalc()
            super().save(*args, **kwargs)
            self._update_truck_state()