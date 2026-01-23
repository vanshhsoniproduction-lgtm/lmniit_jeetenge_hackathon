from django.urls import path
from . import views

urlpatterns = [
    path('summarize/', views.summarize_repo, name='summarize_repo'),
]