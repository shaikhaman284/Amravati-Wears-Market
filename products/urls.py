from django.urls import path
from . import views

urlpatterns = [
    # Public product endpoints (for customers)
    path('', views.list_products, name='list_products'),
    path('<int:product_id>/', views.get_product_detail, name='get_product_detail'),

    # Seller product endpoints
    path('my-products/', views.list_my_products, name='list_my_products'),
    path('my-products/<int:product_id>/', views.get_my_product_detail, name='get_my_product_detail'),
    path('create/', views.create_product, name='create_product'),
    path('update/<int:product_id>/', views.update_product, name='update_product'),
    path('delete/<int:product_id>/', views.delete_product, name='delete_product'),
]