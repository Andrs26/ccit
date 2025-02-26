from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('visitas/', views.visitas, name='visitas'),
    path('eventos_capacitaciones/', views.eventos_capacitaciones, name='eventos_capacitaciones'),
    path('nueva-visita/', views.nueva_visita, name='nueva-visita'),
    path('nueva-visita-agendada/<int:id>', views.nueva_visita_agendada, name='nueva-visita-agendada'),
    path('guardar_visita/', views.guardar_visita, name='guardar_visita'),
    path('guardar_visita_agendada/', views.guardar_visita_agendada, name='guardar_visita_agendada'),
    path('salida_visita/', views.salida_visita, name='salida_visita'),
    path('parametros/', views.parametros, name='parametros'),
    path('crear_motivo/', views.crear_motivo, name='crear_motivo'),
    path('editar_motivo/<int:motivo_id>', views.editar_motivo, name='editar_motivo'),
    path('cambiar_estado_motivo/', views.cambiar_estado_motivo, name='cambiar_estado_motivo'),
    path('buscar_visitante_ajax/', views.buscar_visitante_ajax, name='buscar_visitante_ajax'),
]