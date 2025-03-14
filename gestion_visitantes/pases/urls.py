from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('pases/', views.pases, name='pases'),
    path('pases/buscar_pase', views.buscar_pase, name='buscar_pase'),
    path('pases/cambiar_estado_pase/<int:pase_id>/', views.cambiar_estado_pase, name='cambiar_estado_pase'),
    path('crear_pase/', views.crear_pase, name='crear_pase'),
    path('save_pase/', views.save_pase, name='save_pase'),
    path('editar_pase/<int:id>', views.editar_pase, name='editar_pase'),
    path('edit_pase/', views.edit_pase, name='edit_pase'),
    path('eliminar_pase/<int:id>', views.eliminar_pase, name='eliminar_pase'),
]