from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('talento/home/', views.home_rrhh, name='home_rrhh'),
    path('reloj/datos/', views.datos_crudos_reloj, name='datos_crudos_reloj'),
    path('talento/usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('talento/usuarios/agregar/', views.agregar_usuario, name='agregar_usuario'),
    path('talento/usuarios/editar/<int:usuario_id>/', views.editar_usuario, name='editar_usuario'),
    path('talento/usuarios/eliminar/<int:usuario_id>/', views.eliminar_usuario, name='eliminar_usuario'),

    #* -------------------------------------------------------------------------------------------------------- Asistencias
    path('asistencias/sincronizar/', views.sincronizar_datos_ajax, name='sincronizar_datos'),
    path('talento/asistencias/', views.listar_asistencias, name='listar_asistencias'),

    #* -------------------------------------------------------------------------------------------------------- RH ADMIN
    path('talento/admin/colaboradores/', views.listar_colaboradores, name='listar_colaboradores'),
    path('talento/admin/colaboradores/<int:colaborador_id>/', views.ver_colaborador, name='ver_colaborador'),
    path('talento/admin/colaboradores/crear', views.crear_colaborador, name='crear_colaborador'),
    path('talento/admin/colaboradores/editar/<int:colaborador_id>/', views.editar_colaborador, name='editar_colaborador'),
    path('talento/admin/colaboradores/cambiar_estado/<int:colaborador_id>/', views.cambiar_estado_colaborador, name='cambiar_estado_colaborador'),
    path('reporte-asistencias/', views.listar_colaboradores_reporte, name="reporte_colaboradores"),
    path('reporte-asistencias/<int:colaborador_id>/editar/', views.editar_reporte_colaborador, name="editar_reporte_colaborador"),
    path('talento/admin/reporte_colaborador/pdf/<int:colaborador_id>/', views.generar_pdf_reporte_colaborador, name='pdf_reporte_colaborador'),

    #* -------------------------------------------------------------------------------------------------------- RH ADMIN - PARAMETROS
    path('talento/admin/horarios_laborales/', views.listar_horarios, name='horarios_laborales'),
    path('talento/admin/horarios_laborales/crear/', views.crear_horario, name='crear_horario'),
    path('talento/admin/horarios_laborales/editar/<int:horario_id>/', views.editar_horario, name='editar_horario'),
    path('talento/admin/horarios_laborales/eliminar/<int:horario_id>/', views.eliminar_horario, name='eliminar_horario'),
    path('colaborador/<int:colaborador_id>/agregar-historial/', views.agregar_historial_horario, name='agregar_historial_horario'),
    path('colaborador/editar-historial/<int:historial_id>/', views.editar_historial_horario, name='editar_historial_horario'),
    path('colaborador/eliminar-historial/<int:historial_id>/', views.eliminar_historial_horario, name='eliminar_historial_horario'),
    
]