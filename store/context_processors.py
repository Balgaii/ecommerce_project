from .models import StoreSetting, Cart

def store_settings(request):
    settings = StoreSetting.objects.first()
    if not settings:
        settings = StoreSetting.objects.create()
    
    cart_count = 0
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_count = cart.total_items
    else:
        session_key = request.session.session_key
        if session_key:
            cart = Cart.objects.filter(session_key=session_key).first()
            if cart:
                cart_count = cart.total_items

    return {
        'store_settings': settings,
        'global_cart_count': cart_count,
    }