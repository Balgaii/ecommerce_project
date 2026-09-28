from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('products/', views.admin_products, name='admin_products'),
    path('products/add/', views.admin_product_add, name='admin_product_add'),
    path('products/edit/<int:pk>/', views.admin_product_edit, name='admin_product_edit'),
    path('products/toggle/<int:pk>/', views.admin_product_toggle, name='admin_product_toggle'),
    path('products/delete/<int:pk>/', views.admin_product_delete, name='admin_product_delete'),
    path('orders/', views.admin_orders, name='admin_orders'),
    path('orders/<str:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('customers/', views.admin_customers, name='admin_customers'),
    path('categories/', views.admin_categories, name='admin_categories'),
    path('settings/', views.admin_settings, name='admin_settings'),
]