from django.urls import path
from . import views

urlpatterns = [
    # Static QR
    path('static/', views.static_qr_view, name='static_qr'),
    path('pay/static/', views.pay_static_view, name='pay_static'),
    
    # Dynamic QR
    path('create/', views.create_dynamic_qr, name='create_dynamic_qr'),
    path('pay/<str:request_id>/', views.pay_dynamic_view, name='pay_dynamic'),
    
    # Verification & History
    path('api/verify/', views.verify_transaction, name='verify_transaction'),
    path('history/', views.payment_history, name='payment_history'),
    
    # Receipt
    path('receipt/<str:tx_hash>/', views.receipt_view, name='receipt'),
    
    # Profile Entry
    path('profile/', views.profile_view, name='profile'),
]
