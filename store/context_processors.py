from .models import StoreSetting

def store_settings(request):
    settings, created = StoreSetting.objects.get_or_create(id=1)
    # Agar database mein purana naam hai, toh usay code se overwrite kar dein
    if settings.store_name == 'LuxeCart' or not settings.store_name:
        settings.store_name = 'THE NORTH GIFTS'
        settings.save()
        
    return {
        'store_settings': settings
    }