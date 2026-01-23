from django.urls import path
from . import views

urlpatterns = [
    path('github/', views.run_github_agent, name='run_github_agent'),
    path('audio/', views.run_audio_agent, name='run_audio_agent'),
    path('stats/', views.get_dashboard_stats, name='dashboard_stats'),
    path('tx/<int:tx_id>/', views.get_transaction_details, name='tx_details'),
]