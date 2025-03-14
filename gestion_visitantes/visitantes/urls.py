from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    #* *************************************************************************************************** Visitas Recepción
    path('visitas/hoy', views.inicio_recepcion, name='inicio_recepcion'),
    path('visitas/buscar_inicio_recepcion', views.buscar_inicio_recepcion, name='buscar_inicio_recepcion'),
    path('visitas/buscar_visitas_recepcion', views.buscar_visitas_recepcion, name='buscar_visitas_recepcion'),
    path('visitas/buscar_eventos_recepcion', views.buscar_eventos_recepcion, name='buscar_eventos_recepcion'),
    path('visitas/buscar_pase_recepcion', views.buscar_pase_recepcion, name='buscar_pase_recepcion'),
    path('visitas/todas', views.visitas_recepcion, name='visitas_recepcion'),
    path('nueva-visita/', views.nueva_visita, name='nueva-visita'),
    path('cambiar_pase/', views.cambiar_pase, name='cambiar_pase'),
    path('eventos_capacitaciones/', views.eventos_capacitaciones, name='eventos_capacitaciones'),
    path('pases-recepcion/', views.pases, name='pases_recepcion'),
    path('detalles_evento/<int:id>/', views.detalles_evento, name='detalles_evento'),
    path('detalles_evento_visitas/<int:id>/', views.detalles_evento_visitas, name='detalles_evento_visitas'),
    path('ingresar_visita_agendada/<int:id>/', views.ingresar_visita_agendada, name='ingresar_visita_agendada'),
    #* *************************************************************************************************** Editar
    path('salida_visita/', views.salida_visita, name='salida_visita'),
    #* *************************************************************************************************** Guardar
    path('guardar_visita/', views.guardar_visita, name='guardar_visita'),
    path('guardar_ingresar_visita_agendada/', views.guardar_ingresar_visita_agendada, name='guardar_ingresar_visita_agendada'),
    #? *************************************************************************************************** Parametros: Motivos
    path('motivos/', views.motivos, name='motivos'),
    path('crear_motivo/', views.crear_motivo, name='crear_motivo'),
    path('editar_motivo/<int:motivo_id>', views.editar_motivo, name='editar_motivo'),
    path('cambiar_estado_motivo/', views.cambiar_estado_motivo, name='cambiar_estado_motivo'),
    #? *************************************************************************************************** Parametros: Acciones
    path('acciones/', views.acciones, name='acciones'),
    path('crear_accion/', views.crear_accion, name='crear_accion'),
    path('editar_accion/<int:accion_id>', views.editar_accion, name='editar_accion'),
    path('cambiar_estado_accion/', views.cambiar_estado_accion, name='cambiar_estado_accion'),
    #? *************************************************************************************************** Parametros: Colaboradores
    path('visitas/colaboradores', views.colaboradores, name='colaboradores'),
    path('visitas/buscar_colaboradores', views.buscar_colaboradores, name='buscar_colaboradores'),
    path('crear_colaborador/', views.crear_colaborador, name='crear_colaborador'),
    path('editar_colaborador/<int:colaborador_id>', views.editar_colaborador, name='editar_colaborador'),
    path('cambiar_estado_colaborador/', views.cambiar_estado_colaborador, name='cambiar_estado_colaborador'),
    # *************************************************************************************************** AJAX
    path('buscar_visitante_ajax/', views.buscar_visitante_ajax, name='buscar_visitante_ajax'),
]