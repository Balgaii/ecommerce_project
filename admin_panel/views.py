from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from store.models import Product, Category, Order, CustomerProfile, StoreSetting
from store.forms import ProductForm
from django.db.models import Sum, Count

def admin_check(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@user_passes_test(admin_check, login_url='login')
def admin_dashboard(request):
    total_products = Product.objects.count()
    total_customers = CustomerProfile.objects.count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='Pending').count()
    completed_orders = Order.objects.filter(status='Delivered').count()
    cancelled_orders = Order.objects.filter(status='Cancelled').count()
    total_sales = Order.objects.exclude(status='Cancelled').aggregate(Sum('total'))['total__sum'] or 0.00
    low_stock_products = Product.objects.filter(stock__lte=5).count()
    recent_orders = Order.objects.order_by('-created_at')[:5]

    return render(request, 'admin_panel/dashboard.html', {
        'total_products': total_products,
        'total_customers': total_customers,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'total_sales': total_sales,
        'low_stock_products': low_stock_products,
        'recent_orders': recent_orders,
    })

@user_passes_test(admin_check, login_url='login')
def admin_products(request):
    products = Product.objects.all().order_by('-id')
    return render(request, 'admin_panel/products.html', {'products': products})

@user_passes_test(admin_check, login_url='login')
def admin_product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Product added successfully!")
            return redirect('admin_products')
    else:
        form = ProductForm()
    return render(request, 'admin_panel/product_form.html', {'form': form, 'title': 'Add Product'})

@user_passes_test(admin_check, login_url='login')
def admin_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully!")
            return redirect('admin_products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'admin_panel/product_form.html', {'form': form, 'title': 'Edit Product'})

@user_passes_test(admin_check, login_url='login')
def admin_product_toggle(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_available = not product.is_available
    product.save()
    status_msg = "available" if product.is_available else "unavailable"
    messages.success(request, f"Product {product.name} marked as {status_msg}.")
    return redirect('admin_products')

@user_passes_test(admin_check, login_url='login')
def admin_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.success(request, "Product deleted successfully.")
    return redirect('admin_products')

@user_passes_test(admin_check, login_url='login')
def admin_orders(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/orders.html', {'orders': orders})

@user_passes_test(admin_check, login_url='login')
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order.order_id} status updated to {new_status}.")
            return redirect('admin_order_detail', order_id=order.order_id)
    return render(request, 'admin_panel/order_detail.html', {'order': order})

@user_passes_test(admin_check, login_url='login')
def admin_customers(request):
    customers = CustomerProfile.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/customers.html', {'customers': customers})

@user_passes_test(admin_check, login_url='login')
def admin_categories(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        if name:
            Category.objects.create(name=name, description=description)
            messages.success(request, "Category created successfully.")
            return redirect('admin_categories')
    return render(request, 'admin_panel/categories.html', {'categories': categories})

@user_passes_test(admin_check, login_url='login')
def admin_settings(request):
    setting = StoreSetting.objects.first()
    if not setting:
        setting = StoreSetting.objects.create()
    if request.method == 'POST':
        setting.store_name = request.POST.get('store_name', setting.store_name)
        setting.contact_email = request.POST.get('contact_email', setting.contact_email)
        setting.contact_phone = request.POST.get('contact_phone', setting.contact_phone)
        setting.store_address = request.POST.get('store_address', setting.store_address)
        setting.delivery_charges = request.POST.get('delivery_charges', setting.delivery_charges)
        setting.currency = request.POST.get('currency', setting.currency)
        setting.save()
        messages.success(request, "Store settings saved successfully.")
        return redirect('admin_settings')
    return render(request, 'admin_panel/settings.html', {'setting': setting})