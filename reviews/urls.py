from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_review, name='create_review'),
    path('product/<int:product_id>/', views.get_product_reviews, name='get_product_reviews'),
]