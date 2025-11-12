from django.urls import path
from . import views

urlpatterns = [
    # Shop management
    path('register/', views.register_shop, name='register_shop'),
    path('my-shop/', views.get_my_shop, name='get_my_shop'),
    path('update/', views.update_shop, name='update_shop'),

    # Public shop endpoints
    path('approved/', views.list_approved_shops, name='list_approved_shops'),
    path('<int:shop_id>/', views.get_shop_detail, name='get_shop_detail'),

    # Categories
    path('categories/', views.list_categories, name='list_categories'),
    path('categories/<int:category_id>/', views.get_category_detail, name='get_category_detail'),
]