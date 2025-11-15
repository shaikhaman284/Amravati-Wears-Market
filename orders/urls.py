from django.urls import path
from . import views

urlpatterns = [
    # Customer order endpoints
    path('create/', views.create_order, name='create_order'),
    path('my-orders/', views.get_my_orders, name='get_my_orders'),
    path('<str:order_number>/', views.get_order_detail, name='get_order_detail'),
    path('<str:order_number>/cancel/', views.cancel_customer_order, name='cancel_customer_order'),

    # Seller order endpoints
    path('seller/orders/', views.get_seller_orders, name='get_seller_orders'),
    path('seller/dashboard/', views.get_seller_dashboard, name='get_seller_dashboard'),
    path('seller/<str:order_number>/status/', views.update_order_status, name='update_order_status'),
]
