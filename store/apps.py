from django.apps import AppConfig

class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'

    def ready(self):
        from django.contrib.auth.models import User
        try:
            # Agar user pehle se hai toh usay staff aur superuser bana do, warna naya bana do
            user, created = User.objects.get_or_create(username='admin')
            user.set_password('admin12345')
            user.is_staff = True
            user.is_superuser = True
            user.save()
        except Exception:
            pass