from django.urls import path
from . import views

urlpatterns = [
    path('bledata/', views.bledata, name='bledata'),
]