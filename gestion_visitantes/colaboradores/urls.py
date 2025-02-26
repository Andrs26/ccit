from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('colaboradores/', views.colaboradores_home, name='colaboradores_home'),
    path('colaboradores-nueva-visita/', views.nueva_visita, name='colaboradores-nueva-visita'),
    path('colaboradores-save-visita/', views.guardar_visita, name='colaboradores-save-visita'),
]