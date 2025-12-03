from django.urls import path
from . import views

urlpatterns = [
    # Seller coupon management
    path('', views.list_my_coupons, name='list_my_coupons'),
    path('create/', views.create_coupon, name='create_coupon'),
    path('<int:coupon_id>/', views.get_coupon_detail, name='get_coupon_detail'),
    path('<int:coupon_id>/update/', views.update_coupon, name='update_coupon'),
    path('<int:coupon_id>/delete/', views.delete_coupon, name='delete_coupon'),
    path('<int:coupon_id>/usages/', views.get_coupon_usages, name='get_coupon_usages'),

    # Customer coupon validation
    path('validate/', views.validate_coupon, name='validate_coupon'),
]