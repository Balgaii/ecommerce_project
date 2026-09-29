from django.apps import AppConfig
import os

class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'

    def ready(self):
        from django.contrib.auth.models import User
        try:
            if not User.objects.filter(is_superuser=True).exists():
                User.objects.create_superuser('admin', 'admin@thenorthgifts.com', 'admin12345')
        except Exception:
            pass