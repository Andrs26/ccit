from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('colaboradores/', views.colaboradores_home, name='colaboradores_home'),
    path('colaboradores-nueva-visita/', views.nueva_visita, name='colaboradores-nueva-visita'),
    path('colaboradores-save-visita/', views.guardar_visita, name='colaboradores-save-visita'),
    path('nuevo_evento/', views.nuevo_evento, name='nuevo_evento'),
    path('salida_mea_visita/', views.salida_mea_visita, name='salida_mea_visita'),
    path('detalle_visita_agendada/<int:id>', views.detalle_visita_agendada, name='detalle_visita_agendada'),
    path('detalle_visita_dentro/<int:id>', views.detalle_visita_dentro, name='detalle_visita_dentro'),
    path('nueva-visita-agendada/<int:id>', views.nueva_visita_agendada, name='nueva-visita-agendada'),

    path('colaborador/visitas/', views.visitas_colaborador, name='visitas_colaborador'),
    path('colaborador/eventos_capacitaciones/', views.eventos_capacitaciones_colaborador, name='eventos_capacitaciones_colaborador'),
    
    path('editar_visita_agendada/', views.editar_visita_agendada, name='editar_visita_agendada'),
]