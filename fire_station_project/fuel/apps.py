# fuel/apps.py
from django.apps import AppConfig


class FuelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fuel'

    def ready(self):
        # импортируем сигналы при старте приложения
        import fuel.signals  # noqa