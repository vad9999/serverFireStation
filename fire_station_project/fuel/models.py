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
    driver_license = models.ForeignKey(DriverLicense, on_delete=models.CASCADE, related_name='license')
    
    def __str__(self):
	    return f"{self.name} - {self.surname} - {self.last_name} - {self.login}"
    
class RequiredRole(SoftDeleteModel):
    role = models.OneToOneField(Role, on_delete=models.CASCADE, primary_key=True, related_name='role')

class Waybill(SoftDeleteModel):
    pass