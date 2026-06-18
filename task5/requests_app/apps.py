from django.apps import AppConfig


class RequestsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'requests_app'
    verbose_name = 'Портал заявок'

    def ready(self):
        from . import services  # noqa: F401
