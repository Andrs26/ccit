from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('visitas/', views.visitas, name='visitas'),
    path('nueva-visita/', views.nueva_visita, name='nueva-visita'),
]