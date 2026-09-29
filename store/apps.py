from django.apps import AppConfig

class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'

    def ready(self):
        # Python 3.14 & Django template context compatibility fix
        try:
            from django.template.context import BaseContext, Context
            
            def fixed_base_copy(self):
                dup = object.__new__(self.__class__)
                dup.__dict__.update(self.__dict__)
                if hasattr(self, 'dicts'):
                    dup.dicts = list(self.dicts)
                return dup

            BaseContext.__copy__ = fixed_base_copy
            Context.__copy__ = fixed_base_copy
        except Exception:
            pass

        # Admin Superuser & Staff Forcefully Create/Update
        from django.contrib.auth.models import User
        try:
            user, created = User.objects.get_or_create(username='admin')
            user.set_password('admin12345')
            user.is_staff = True
            user.is_superuser = True
            user.save()
        except Exception:
            pass