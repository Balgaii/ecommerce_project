import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from .models import Product, Category, Cart, CartItem, Order, OrderItem, CustomerProfile, StoreSetting
from .forms import UserRegistrationForm, CheckoutForm

def home_view(request):
    featured_products = Product.objects.filter(is_available=True, is_featured=True)[:8]
    latest_products = Product.objects.filter(is_available=True).order_by('-created_at')[:8]
    categories = Category.objects.all()[:6]
    return render(request, 'store/home.html', {
        'featured_products': featured_products,
        'latest_products': latest_products,
        'categories': categories
    })

def shop_view(request):
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.all()
    
    category_slug = request.GET.get('category')
    search_query = request.GET.get('q')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort')
    featured_only = request.GET.get('featured')

    if category_slug:
        products = products.filter(category__slug=category_slug)
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) | 
            Q(sku__iexact=search_query)
        )
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    if featured_only:
        products = products.filter(is_featured=True)

    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('-id')

    return render(request, 'store/shop.html', {
        'products': products,
        'categories': categories,
        'selected_category': category_slug,
        'search_query': search_query or ''
    })

def product_detail_view(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.filter(category=product.category, is_available=True).exclude(id=product.id)[:4]
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products
    })

def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_key=session_key)
    return cart

def cart_view(request):
    cart = get_or_create_cart(request)
    setting = StoreSetting.objects.first()
    delivery = setting.delivery_charges if setting else 5.00
    total_with_delivery = cart.subtotal + delivery if cart.subtotal > 0 else 0
    return render(request, 'store/cart.html', {
        'cart': cart,
        'delivery_charges': delivery,
        'total_with_delivery': total_with_delivery
    })

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if not product.is_available or product.stock <= 0:
        messages.error(request, f"{product.name} is currently unavailable or out of stock.")
        return redirect('product_detail', slug=product.slug)

    cart = get_or_create_cart(request)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        if cart_item.quantity + 1 > product.stock:
            messages.warning(request, "Cannot add more than available stock.")
        else:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f"Updated quantity for {product.name}.")
    else:
        messages.success(request, f"Added {product.name} to your cart.")
    
    return redirect('cart')

def update_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    action = request.GET.get('action')
    if action == 'inc':
        if item.quantity < item.product.stock:
            item.quantity += 1
            item.save()
        else:
            messages.warning(request, "Reached maximum available stock.")
    elif action == 'dec':
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
    return redirect('cart')

def remove_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect('cart')

def checkout_view(request):
    cart = get_or_create_cart(request)
    if not cart.items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('shop')

    setting = StoreSetting.objects.first()
    delivery = setting.delivery_charges if setting else 5.00

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            for item in cart.items.all():
                if not item.product.is_available or item.quantity > item.product.stock:
                    messages.error(request, f"Product {item.product.name} is out of stock or unavailable.")
                    return redirect('cart')

            order_id = str(uuid.uuid4())[:8].upper()
            subtotal = cart.subtotal
            total = subtotal + delivery

            order = Order.objects.create(
                order_id=order_id,
                user=request.user if request.user.is_authenticated else None,
                full_name=form.cleaned_data['full_name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address'],
                city=form.cleaned_data['city'],
                postal_code=form.cleaned_data['postal_code'],
                order_notes=form.cleaned_data['order_notes'],
                subtotal=subtotal,
                delivery_charges=delivery,
                total=total,
                status='Pending',
                payment_method='Cash on Delivery'
            )

            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    price=item.product.get_price,
                    quantity=item.quantity
                )
                item.product.stock -= item.quantity
                if item.product.stock <= 0:
                    item.product.stock = 0
                item.product.save()

            cart.items.all().delete()
            return redirect('order_confirmation', order_id=order.order_id)
    else:
        initial_data = {}
        if request.user.is_authenticated:
            try:
                profile = request.user.profile
                initial_data = {
                    'full_name': request.user.get_full_name() or request.user.username,
                    'email': request.user.email,
                    'phone': profile.phone,
                    'address': profile.address,
                    'city': profile.city,
                    'postal_code': profile.postal_code,
                }
            except CustomerProfile.DoesNotExist:
                pass
        form = CheckoutForm(initial=initial_data)

    return render(request, 'store/checkout.html', {
        'form': form,
        'cart': cart,
        'delivery_charges': delivery,
        'total_with_delivery': cart.subtotal + delivery
    })

def order_confirmation_view(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    return render(request, 'store/order_confirmation.html', {'order': order})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['email'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['full_name']
            )
            CustomerProfile.objects.create(
                user=user,
                phone=form.cleaned_data['phone']
            )
            messages.success(request, "Registration successful! You can now log in.")
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'store/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username_or_email, password=password)
        if not user:
            try:
                u_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=u_obj.username, password=password)
            except User.DoesNotExist:
                pass

        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid credentials. Please check your email and password.")
    return render(request, 'store/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('home')

@login_required
def dashboard_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/dashboard.html', {'orders': orders})

@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'store/order_detail.html', {'order': order})

def about_view(request):
    return render(request, 'store/about.html')

def contact_view(request):
    if request.method == 'POST':
        messages.success(request, "Thank you for contacting us! We will get back to you shortly.")
        return redirect('contact')
    return render(request, 'store/contact.html')

def custom_404(request, exception):
    return render(request, 'store/404.html', status=404)

def custom_403(request, exception):
    return render(request, 'store/403.html', status=403)

def custom_500(request):
    return render(request, 'store/500.html', status=500)