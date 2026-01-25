from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    
    # API endpoints for wallet auth
    path('wallet/api/get_nonce/', views.get_nonce, name='get_nonce'),
    path('wallet/api/verify_signature/', views.verify_signature, name='verify_signature'),
]
