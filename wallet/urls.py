from django.urls import path
from . import views  # Use relative import for cleaner code

urlpatterns = [
    # Pages
    path('', views.landing_page, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Auth API
    path('auth/nonce/', views.get_nonce, name='get_nonce'),
    path('auth/verify/', views.verify_signature, name='verify_signature'),
    path('logout/', views.logout_view, name='logout'),
]