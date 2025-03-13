from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.cache import cache
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.db.models.functions import TruncDate
from django.utils.timezone import now
from django.http import JsonResponse
from django.utils import timezone
from django.urls import reverse
from django.db.models import Q
import pandas as pd
import traceback  # Para imprimir el error completo en la consola
import random
import json
import io
import os

""" Importación de los modelos """
from usuarios.models import *
from visitantes.models import *
from pertenencias.models import *
from pases.models import *

# Número máximo de intentos antes del bloqueo
MAX_ATTEMPTS = 5
LOCKOUT_TIME = 300 

# Create your views here.
def login_view(request):
    """Autentica al usuario y lo redirige al cambio de contraseña si es necesario."""
    
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Obtener intentos fallidos desde la caché
        attempts_key = f'login_attempts_{username}'
        attempts = cache.get(attempts_key, 0)

        if attempts >= MAX_ATTEMPTS:
            messages.error(request, "Tu cuenta está bloqueada. Inténtalo más tarde.")
            return render(request, 'auth/login.html')

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Restablecer los intentos fallidos al iniciar sesión correctamente
            cache.delete(attempts_key)

            # Verificar si el usuario tiene un perfil y si su PIN está vacío
            user_profile, created = UserProfile.objects.get_or_create(user=user)

            if user.last_login is None or user_profile.pin is None or user_profile.pin == '':
                messages.warning(request, "Debes cambiar tu contraseña y establecer un PIN antes de continuar.")
                login(request, user)  # Autenticamos para que pueda acceder al cambio de contraseña
                return redirect('change_password_reset', user_id=user.id)

            # Iniciar sesión y registrar evento
            login(request, user)

            evento = Eventos(
                cod_asamblea='ASAM_2025',
                accion='Inició sesión',
                usuario_registro=request.user.username
            )
            evento.save()

            # Redirigir al usuario a la página que intentaba acceder, o al inicio si no hay 'next'
            next_url = request.POST.get('next', request.GET.get('next', 'inicio/'))
            return redirect('home')

        else:
            # Intento fallido
            attempts += 1
            cache.set(attempts_key, attempts, LOCKOUT_TIME)

            remaining_attempts = MAX_ATTEMPTS - attempts
            if remaining_attempts > 0:
                messages.warning(request, f"Usuario o contraseña incorrectos. Te quedan {remaining_attempts} intentos antes del bloqueo.")
            else:
                messages.error(request, "Tu cuenta ha sido bloqueada por intentos fallidos. Inténtalo más tarde.")

    return render(request, 'auth/login.html')

def logout_view(request):
    logout(request)
    evento = Eventos(
        cod_asamblea = 'ASAM_2025',
        accion = f'Cerró sesión',
        usuario_registro = request.user.username
    )
    evento.save()
    return redirect('login')

@login_required
def home(request):
    is_visitas_recepcion_group = request.user.groups.filter(name='visitas_recepcion_group').exists()
    is_visitas_colaborador_group = request.user.groups.filter(name='visitas_colaborador_group').exists()

    return render(request, 'inicio/home.html', {
        'is_visitas_recepcion_group': is_visitas_recepcion_group,
        'is_visitas_colaborador_group': is_visitas_colaborador_group,
    })

#* --------------------------------------------------------------- Función de usuarios
#? Vista para ver la lista de usuarios
@login_required
def user_list(request):
    is_super_admin_group = request.user.groups.filter(name='super_admin').exists()
    is_admin_group = request.user.groups.filter(name='admin_group').exists()

    # Filtrar usuarios según el grupo del usuario autenticado
    if is_super_admin_group:
        users = User.objects.prefetch_related('groups').all()  # Super admin ve todos los usuarios
    elif is_admin_group:
        users = User.objects.prefetch_related('groups').exclude(groups__name="super_admin")  # Admin NO ve super_admin
    else:
        messages.error(request, "Acceso no permitido.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    # Agregar un atributo a cada usuario para facilitar la lógica en el template
    for user in users:
        user.is_estandar_group = user.groups.filter(name="estandar_group").exists()

    # Registrar acceso en eventos
    Eventos.objects.create(
        cod_asamblea='ASAM_2025',
        accion='Accedió al listado de usuarios',
        usuario_registro=request.user.username
    )

    return render(request, 'auth/user_list.html', {
        'users': users,
        'is_admin_group': is_admin_group,
        'is_super_admin_group': is_super_admin_group
    })

#? Vista para crear un nuevo usuario
@login_required
def create_user(request):
    if request.user.groups.filter(name='admin_group').exists() or request.user.groups.filter(name='super_admin').exists():
        if request.method == 'POST':
            username = request.POST['username']
            password = request.POST['password']
            email = request.POST['email']
            pin = request.POST['pin']
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            selected_groups = request.POST.getlist('groups[]')

            # Validaciones
            if get_user_model().objects.filter(username=username).exists():
                messages.error(request, "El nombre de usuario ya está registrado.")
                return redirect('create_user')

            # Crear el usuario
            user = get_user_model().objects.create_user(
                username=username, password=password, email=email,
                first_name=first_name, last_name=last_name
            )

            # Asignar grupo (rol) al usuario
            for group_name in selected_groups:
                group = Group.objects.get(name=group_name)
                user.groups.add(group)

            # Crear el perfil del usuario con el PIN
            user_profile = UserProfile(user=user, pin=pin)
            user_profile.save()

            evento = Eventos(
                cod_asamblea = 'ASAM_2025',
                accion = f'Creó al usuario {username}',
                usuario_registro = request.user.username
            )
            evento.save()

            messages.success(request, "Usuario creado correctamente.")
            return redirect('user_list')
        
        # Pasamos los grupos disponibles al template para seleccionarlos
        groups = Group.objects.all()
        return render(request, 'auth/create_user.html', {'groups': groups})
        
    # Si el usuario está en el grupo 'estándar_group', lo redirigimos y mostramos mensaje
    elif request.user.groups.filter(name='estándar_group').exists():
        messages.error(request, "Acceso no permitido. No tiene los permisos necesarios para acceder.")
        return redirect(request.META.get('HTTP_REFERER', '/'))  # Regresa donde estaba
    
    # En caso de que no pertenezca a ninguno de los grupos, también redirigimos
    else:
        messages.error(request, "Acceso no permitido. No tiene los permisos necesarios.")
        return redirect(request.META.get('HTTP_REFERER', '/'))  # Regresa donde estaba

#? Vista para editar la información de un usuario
@login_required
def edit_user(request, user_id):
    if request.user.groups.filter(name='admin_group').exists() or request.user.groups.filter(name='super_admin').exists():
        user = get_object_or_404(User, pk=user_id)  # Obtener el usuario por id
        current_group = user.groups.first() if user.groups.exists() else None  # Obtener el grupo actual del usuario

        if request.method == 'POST':
            user.first_name = request.POST['first_name']
            user.last_name = request.POST['last_name']
            user.email = request.POST['email']
            pin = request.POST['pin']
            # Obtener el nuevo grupo del formulario
            group_names = request.POST.getlist('groups')

            # Actualizar grupo (rol)
            if group_names:
                user.groups.clear()
                for group_name in group_names:
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)

            # Guardar cambios del usuario y su perfil (PIN)
            user.save()

            # Si tienes un modelo de perfil de usuario, lo puedes actualizar aquí también.
            # Actualiza el PIN en el perfil de usuario si tienes UserProfile
            user_profile = user.userprofile
            user_profile.pin = pin
            user_profile.save()

            evento = Eventos(
                cod_asamblea = 'ASAM_2025',
                accion = f'Editó al {user.username}',
                usuario_registro = request.user.username
            )
            evento.save()

            messages.success(request, "Usuario actualizado correctamente.")
            return redirect('user_list')

        # Obtener todos los grupos para mostrarlos en el formulario
        groups = Group.objects.all()

        return render(request, 'auth/edit_user.html', {'user': user, 'groups': groups, 'current_group': current_group})
        
    # Si el usuario está en el grupo 'estándar_group', lo redirigimos y mostramos mensaje
    elif request.user.groups.filter(name='estándar_group').exists():
        messages.error(request, "Acceso no permitido. No tiene los permisos necesarios para acceder.")
        return redirect(request.META.get('HTTP_REFERER', '/'))  # Regresa donde estaba
    
    # En caso de que no pertenezca a ninguno de los grupos, también redirigimos
    else:
        messages.error(request, "Acceso no permitido. No tiene los permisos necesarios.")
        return redirect(request.META.get('HTTP_REFERER', '/'))  # Regresa donde estaba


#? Vista para eliminar un usuario
@login_required
def delete_user(request, user_id):
    if request.user.groups.filter(name='super_admin').exists():
        user = get_object_or_404(User, pk=user_id)
        user.delete()

        evento = Eventos(
            cod_asamblea = 'ASAM_2025',
            accion = f'Eliminó el usuario {user.username}',
            usuario_registro = request.user.username
        )
        evento.save()

        messages.success(request, "Usuario eliminado correctamente.")
        return redirect('user_list')
        
    # Si el usuario está en el grupo 'estándar_group', lo redirigimos y mostramos mensaje
    elif request.user.groups.filter(name='estándar_group').exists():
        messages.error(request, "Acceso no permitido. No tiene los permisos necesarios para acceder.")
        return redirect(request.META.get('HTTP_REFERER', '/'))  # Regresa donde estaba
    
    # En caso de que no pertenezca a ninguno de los grupos, también redirigimos
    else:
        messages.error(request, "Acceso no permitido. No tiene los permisos necesarios.")
        return redirect(request.META.get('HTTP_REFERER', '/'))  # Regresa donde estaba

# ✅ Formulario extendido para cambiar contraseña y PIN
class PasswordPinChangeForm(PasswordChangeForm):
    pin = forms.CharField(
        max_length=6,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control w", "placeholder": "Nuevo PIN"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["pin"].label = "Nuevo PIN (opcional)"

@login_required
def change_password(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user_profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = PasswordChangeForm(user, request.POST)
        new_pin = request.POST.get('pin')

        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)  # Mantener sesión activa

            # Guardar el nuevo PIN si el usuario ingresó uno
            if new_pin:
                user_profile.pin = new_pin
                user_profile.save()

            messages.success(request, "Contraseña y PIN cambiados correctamente.")
            return redirect('inicio')
        else:
            # 🔹 Agregar errores al sistema de mensajes
            for error in form.errors.values():
                messages.error(request, error.as_text())

    else:
        form = PasswordChangeForm(user)

    return render(request, 'auth/change_password.html', {'form': form, 'user': user})

@login_required
def change_password_reset(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user_profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = PasswordChangeForm(user, request.POST)
        new_pin = request.POST.get('pin')

        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)  # Mantener sesión activa

            # Guardar el nuevo PIN si el usuario ingresó uno
            if new_pin:
                user_profile.pin = new_pin
                user_profile.save()

            messages.success(request, "Contraseña y PIN cambiados correctamente.")
            return redirect('inicio')
        else:
            # 🔹 Agregar errores al sistema de mensajes
            for error in form.errors.values():
                messages.error(request, error.as_text())

    else:
        form = PasswordChangeForm(user)

    return render(request, 'auth/change_password_reset.html', {'form': form, 'user': user})

@login_required
def reset_user_password(request, user_id):
    """Permite al administrador restablecer la contraseña de un usuario a una genérica."""
    
    # Verificar si el usuario autenticado es un administrador
    if not request.user.is_superuser and not request.user.groups.filter(name='admin_group').exists():
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('user_list')

    user = get_object_or_404(User, pk=user_id)

    # Establecer la nueva contraseña genérica
    nueva_contraseña = "Camara20*"
    user.password = make_password(nueva_contraseña)  # Encriptar la nueva contraseña
    user.save()

    # Marcar el usuario como si nunca hubiera iniciado sesión para forzarlo a cambiarla
    user.last_login = None
    user.save()

    # Restablecer también el PIN si lo deseamos (opcional)
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    user_profile.pin = None  # Forzar a que el usuario también ingrese un nuevo PIN
    user_profile.save()

    messages.success(request, f"La contraseña de {user.username} ha sido restablecida. Ahora deberá cambiarla al iniciar sesión.")
    return redirect('user_list')  # Redirigir a la lista de usuarios o a donde prefieras

def reset_password(request):
    """Verifica el PIN del usuario y lo redirige a cambiar la contraseña"""
    if request.method == "POST":
        username = request.POST.get("user")
        pin = request.POST.get("pin")

        try:
            user = User.objects.get(username=username)
            profile = UserProfile.objects.get(user=user)

            if profile.pin == pin:
                # Redirigir al usuario para establecer una nueva contraseña
                return redirect(reverse('set_new_password', args=[user.id]))
            else:
                messages.error(request, "El PIN ingresado es incorrecto.")
        except User.DoesNotExist:
            messages.error(request, "El usuario no existe.")
        except UserProfile.DoesNotExist:
            messages.error(request, "Este usuario no tiene un PIN registrado.")

    return render(request, "auth/reset_password.html")

from django.utils.crypto import get_random_string
def verificar_pin(request):
    if request.method == "POST":
        username = request.POST.get("user").strip()
        pin = request.POST.get("pin").strip()

        # Buscar usuario
        user = get_object_or_404(User, username=username)

        # Verificar si el PIN es correcto
        if user.userprofile.pin == pin:
            # Generar un token temporal en cache (expira en 5 min)
            token = get_random_string(32)
            cache.set(f"reset_token_{token}", user.id, timeout=300)

            # Redirigir al usuario a la pantalla de cambio de contraseña con el token
            return redirect(reverse('cambiar_contrasena', args=[token]))
        else:
            messages.error(request, "PIN incorrecto. Inténtalo de nuevo.")
            return redirect('verificar_pin')

    return render(request, "auth/password_reset.html")

from django.http import HttpResponseForbidden
def cambiar_contrasena(request, token):
    # Verificar si el token es válido en cache
    user_id = cache.get(f"reset_token_{token}")

    if not user_id:
        return HttpResponseForbidden("Token inválido o expirado.")

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        nueva_contrasena = request.POST.get("password").strip()
        confirmar_contrasena = request.POST.get("confirm_password").strip()

        if nueva_contrasena != confirmar_contrasena:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect(reverse("cambiar_contrasena", args=[token]))

        # Guardar la nueva contraseña
        user.password = make_password(nueva_contrasena)
        user.save()

        # Eliminar el token después del uso
        cache.delete(f"reset_token_{token}")

        messages.success(request, "Contraseña cambiada con éxito. Inicia sesión con tu nueva contraseña.")
        return redirect("login")

    return render(request, "auth/password_reset_confirm.html", {"token": token})


@login_required
def cambiar_estado_usuario(request, user_id):
    if request.method == "POST":
        # Obtener el usuario que se quiere modificar
        user = get_object_or_404(User, id=user_id)

        # Verificar los permisos del usuario autenticado
        is_super_admin_group = request.user.groups.filter(name='super_admin').exists()
        is_admin_group = request.user.groups.filter(name='admin_group').exists()

        # Verificar el grupo del usuario objetivo
        is_target_standard_group = user.groups.filter(name="estandar_group").exists()
        is_target_admin_group = user.groups.filter(name="admin_group").exists()
        is_target_super_admin = user.groups.filter(name="super_admin").exists()

        # Reglas de permisos
        if is_super_admin_group:
            pass  # Puede cambiar el estado de cualquier usuario

        elif is_admin_group:
            if not is_target_standard_group:
                return JsonResponse({'success': False, 'message': 'No tienes permiso para cambiar el estado de este usuario.'}, status=403)

        else:
            return JsonResponse({'success': False, 'message': 'Acceso no autorizado.'}, status=403)

        # Cambiar el estado del usuario (activo o inactivo)
        user.is_active = not user.is_active
        user.save()

        # Guardar evento
        Eventos.objects.create(
            cod_asamblea='ASAM_2025',
            accion=f'Cambió el estado del usuario {user.username}',
            usuario_registro=request.user.username
        )

        return JsonResponse({'success': True, 'new_status': user.is_active})

    return JsonResponse({'success': False, 'message': 'Método no permitido.'}, status=405)
        
#* ************************************************************************************************** ----- LOGS DE EVENTOS
def eventos(request):
    if request.user.groups.filter(name='admin_group').exists() or request.user.groups.filter(name='super_admin'):
        logs = Eventos.objects.order_by('-created_at')
        is_admin_group = request.user.groups.filter(name='admin_group').exists()
        is_estandar_group = request.user.groups.filter(name='estandar_group').exists()
        is_super_admin = request.user.groups.filter(name='super_admin').exists()

        cod_asambleas_unicos = Eventos.objects.values_list("cod_asamblea", flat=True).distinct()
        usuarios_unicos = Eventos.objects.values_list("usuario_registro", flat=True).distinct()
        
        disabled = 1

        paginator = Paginator(logs, 10)  # 10 empresas por página
        page = request.GET.get('page')
        eventos = paginator.get_page(page)

        return render(request, 'eventos/logs.html', {
            'eventos': eventos,
            "cod_asambleas_unicos": cod_asambleas_unicos,
            "usuarios_unicos": usuarios_unicos,
            'is_admin_group': is_admin_group,
            'is_super_admin': is_super_admin,
            'is_estandard_group': is_estandar_group,
            'disabled': disabled
        })
        
    # Si el usuario está en el grupo 'estándar_group', lo redirigimos y mostramos mensaje
    elif request.user.groups.filter(name='estandar_group').exists():
        messages.error(request, "Acceso no permitido. No tiene los permisos necesarios para acceder.")
        return redirect(request.META.get('HTTP_REFERER', '/'))  # Regresa donde estaba
    
    # En caso de que no pertenezca a ninguno de los grupos, también redirigimos
    else:
        messages.error(request, "Acceso no permitido. No tiene los permisos necesarios.")
        return redirect(request.META.get('HTTP_REFERER', '/'))  # Regresa donde estaba
    
from django.http import JsonResponse
from django.shortcuts import render
from datetime import timedelta

def filtrar_eventos(request):
    cod_asamblea = request.GET.get("cod_asamblea", "")
    usuario = request.GET.get("usuario", "")
    fecha = request.GET.get("fecha", "")
    page = int(request.GET.get("page", 1))  # Obtener el número de página

    eventos = Eventos.objects.all().order_by("-created_at")  # Ordenar de más reciente a más antiguo

    # Aplicar filtros si están seleccionados
    if cod_asamblea:
        eventos = eventos.filter(cod_asamblea=cod_asamblea)
    if usuario:
        eventos = eventos.filter(usuario_registro=usuario)
    if fecha:
        eventos = eventos.filter(created_at__date=fecha)

    # Paginación: 10 eventos por página
    paginator = Paginator(eventos, 10)
    eventos_page = paginator.get_page(page)

    eventos_data = list(eventos_page.object_list.values("usuario_registro", "accion", "created_at"))

    return JsonResponse({
        "eventos": eventos_data,
        "current_page": eventos_page.number,
        "total_pages": paginator.num_pages,
        "has_next": eventos_page.has_next(),
        "has_previous": eventos_page.has_previous(),
    })

import openpyxl
from django.http import HttpResponse

def exportar_eventos(request):
    cod_asamblea = request.GET.get("cod_asamblea", "")
    usuario = request.GET.get("usuario", "")
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    eventos = Eventos.objects.all().order_by("-created_at")

    # Aplicar filtros si están seleccionados
    if cod_asamblea:
        eventos = eventos.filter(cod_asamblea=cod_asamblea)
    if usuario:
        eventos = eventos.filter(usuario_registro=usuario)
    if fecha_inicio and fecha_fin:
        eventos = eventos.filter(created_at__date__range=[fecha_inicio, fecha_fin])
    elif fecha_inicio:
        eventos = eventos.filter(created_at__date__gte=fecha_inicio)
    elif fecha_fin:
        eventos = eventos.filter(created_at__date__lte=fecha_fin)

    # Crear un nuevo archivo Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Eventos"
    ws.append(["Usuario", "Acción", "Fecha", "Hora"])

    # Agregar los datos con ajuste de hora (-6 horas)
    for evento in eventos:
        fecha_evento = evento.created_at - timedelta(hours=6)
        ws.append([
            evento.usuario_registro,
            evento.accion,
            fecha_evento.date(),
            fecha_evento.time()
        ])

    # Crear respuesta HTTP con el archivo Excel
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="eventos.xlsx"'
    wb.save(response)

    return response