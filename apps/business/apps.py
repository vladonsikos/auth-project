from django.apps import AppConfig


class BusinessConfig(AppConfig):
    """Конфигурация приложения business (товары, заказы, магазины)."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.business'
