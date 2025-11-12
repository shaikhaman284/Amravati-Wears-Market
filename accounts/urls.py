from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_or_login, name='register_or_login'),
    path('verify-token/', views.verify_token, name='verify_token'),
    path('me/', views.get_current_user, name='current_user'),
    path('logout/', views.logout, name='logout'),
    path('test-register/', views.test_register, name='test_register'),  # TEMPORARY
]