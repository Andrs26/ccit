from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('inicio/', views.home, name='home'),
    path('users/', views.user_list, name='user_list'),  # Ver todos los usuarios
    path('user/edit/<int:user_id>/', views.edit_user, name='edit_user'),  # Editar un usuario
    path('user/delete/<int:user_id>/', views.delete_user, name='delete_user'),  # Eliminar un usuario
    path('user/reset_user_password/<int:user_id>/', views.reset_user_password, name='reset_user_password'),  #* Restablecer contraseña desde Admin
    path('user/create/', views.create_user, name='create_user'),  # Crear un nuevo usuario
    path('usuarios/cambiar_estado/<int:user_id>/', views.cambiar_estado_usuario, name='cambiar_estado_usuario'),
    #* 
    path('user/reset-password/', views.reset_password, name='reset_password'), #* Restablecer contraseña con PIN desde Login (Ingresar PIN)
    path('user/change-password-reset/<int:user_id>/', views.change_password_reset, name='change_password_reset'),  # Cambiar contraseña

     #* Enlace de "Olvidaste tu contraseña"
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='auth/password_reset.html'), name='password_reset'),
    
    #* Mensaje después de solicitar el restablecimiento
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), name='password_reset_done'),
    
    #* Página para ingresar la nueva contraseña (desde el link enviado)
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'), name='password_reset_confirm'),
    
    #* Página de éxito después de cambiar la contraseña
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'), name='password_reset_complete'),
]