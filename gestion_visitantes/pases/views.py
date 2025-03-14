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


# Create your views here.
@login_required
def pases(request):
    pases_base = PaseAcceso.objects.all()

    paginator_pases = Paginator(pases_base, 10)
    page_pases = request.GET.get('page_pases')
    pases = paginator_pases.get_page(page_pases)

    return render(request, 'pases/pases.html', {
        'pases': pases
    })

@login_required
def buscar_pase(request):
    search_query = request.GET.get('search', '').strip()
    
    if search_query:
        queryset = PaseAcceso.objects.filter(
            Q(numero_pase__icontains=search_query) | Q(lugares_acceso__icontains=search_query)
        )
    else:
        queryset = PaseAcceso.objects.all()
    
    return render(request, 'pases/pases.html', {
        'pases': queryset,
        'search_query': search_query,
    })

@login_required
def crear_pase(request):
    return render(request, 'pases/crear_pase.html')

def save_pase(request):
    if request.method == 'POST':
        numero_pase = request.POST['numero_pase']
        lugares_acceso = request.POST['lugares_acceso']

        pase = PaseAcceso(
            numero_pase = numero_pase,
            lugares_acceso = lugares_acceso,
            estado = 'activo',
            estado_pase = 'Disponible',
        )
        pase.save()

        messages.success(request, "Pase creado correctamente.")
        return redirect('pases')

@login_required
def editar_pase(request, id):
    pase = PaseAcceso.objects.get(id=id)
    return render(request, 'pases/editar_pase.html', {
        'pase': pase
    })

def edit_pase(request):
    if request.method == 'POST':
        id = request.POST['id']
        pase = PaseAcceso.objects.get(id=id)

        numero_pase = request.POST['numero_pase']
        lugares_acceso = request.POST['lugares_acceso']
        estado_pase = request.POST['estado_pase']

        pase.numero_pase = numero_pase
        pase.lugares_acceso = lugares_acceso
        pase.estado_pase = estado_pase
        pase.save()

        messages.success(request, "Pase creado correctamente.")
        return redirect('pases')

@login_required
def eliminar_pase(request, id):
    pase = PaseAcceso.objects.get(id=id)
    pase.delete()
    messages.info(request, "Pase eliminado.")
    return redirect('pases')

from django.core.mail import send_mail
from django.contrib.auth import get_user_model
User = get_user_model()

@login_required
def reportar_pase(request, id):
    pase = PaseAcceso.objects.get(id=id)
    visitas = Visita.objects.filter(estado_visitante = 'in', num_pase=pase.numero_pase).count()
    num_pase = pase.numero_pase
    if visitas > 0:
        messages.warning(request, f"El pase {num_pase} se encuentra asignado a una visita, no se puede reportar un pase en uso.")
        return redirect('pases_recepcion')
    else:
        comentario_reporte = request.POST['comentario_reporte']
        nuevo_estado = request.POST['estado_pase']

        pase.comentario_reporte = comentario_reporte
        pase.estado_pase = nuevo_estado
        pase.save()
        
        # Enviar correo a todos los usuarios en el grupo "visitas_it_group"
        try:
            grupo_visitas = Group.objects.get(name="visitas_it_group")
            usuarios_destino = grupo_visitas.user_set.filter(email__isnull=False).exclude(email="")  # Solo usuarios con email

            if usuarios_destino.exists():
                subject = f"Notificación: Reporte de pase {nuevo_estado}."
                message = f"Hola,\n\nSe ha reportado el pase de acceso {num_pase} como {nuevo_estado}, motivo: {comentario_reporte}.\n\nSaludos,\nEquipo CCIT"
                recipient_list = [usuario.email for usuario in usuarios_destino]

                send_mail(
                    subject,
                    message,
                    None,  # Puedes cambiarlo a DEFAULT_FROM_EMAIL si lo tienes configurado en settings.py
                    recipient_list,
                    fail_silently=False,
                )
                print(f"Correo enviado a: {', '.join(recipient_list)}")
            else:
                print("No hay usuarios en el grupo con correo electrónico.")
        except Group.DoesNotExist:
            print("El grupo 'visitas_it_group' no existe.")

        messages.info(request, f"Pase {num_pase} reportado.")
        return redirect('pases_recepcion')

def cambiar_estado_pase(request, pase_id):
    try:
        data = json.loads(request.body)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": "Error al procesar JSON: " + str(e)
        }, status=400)
    
    # Se espera que en el JSON se envíe un campo "estado" con el nuevo estado ("activo" o "inactivo")
    new_estado = data.get("estado")
    if not new_estado:
        return JsonResponse({
            "success": False,
            "message": "No se proporcionó el nuevo estado."
        }, status=400)
    
    try:
        pase = PaseAcceso.objects.get(id=pase_id)
    except PaseAcceso.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Pase no encontrado."
        }, status=404)
    
    # Actualizar el estado del pase
    pase.estado = new_estado
    pase.save()
    
    return JsonResponse({
        "success": True,
        "estado": new_estado
    })