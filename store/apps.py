from django.apps import AppConfig

class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'

    def ready(self):
        # 1. Python 3.14 aur Django 5 template compatibility fix (Monkey Patch)
        try:
            from django.template.context import Context
            if hasattr(Context, '__copy__'):
                old_copy = Context.__copy__
                def new_copy(self):
                    dup = old_copy(self)
                    if not hasattr(dup, 'dicts') and hasattr(self, 'dicts'):
                        dup.dicts = list(self.dicts)
                    return dup
                Context.__copy__ = new_copy
        except Exception:
            pass

        # 2. Admin Superuser & Staff Forcefully Create/Update
        from django.contrib.auth.models import User
        try:
            user, created = User.objects.get_or_create(username='admin')
            user.set_password('admin12345')
            user.is_staff = True
            user.is_superuser = True
            user.save()
        except Exception:
            pass