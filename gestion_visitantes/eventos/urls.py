from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('guardar_evento/', views.guardar_evento, name='guardar_evento'),
    path('editar_evento/<int:id>', views.editar_evento, name='editar_evento'),
    path('save_editar_evento/', views.save_editar_evento, name='save_editar_evento'),
    path('evento/actualizar_participante/<int:participante_id>/', views.actualizar_participante, name='actualizar_participante'),

]