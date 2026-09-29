from .models import StoreSetting

def store_settings(request):
    settings, created = StoreSetting.objects.get_or_create(id=1)

    if settings.store_name != 'THE NORTH GIFTS':
        settings.store_name = 'THE NORTH GIFTS'
        settings.save()

    return {
        'store_settings': settings
    }