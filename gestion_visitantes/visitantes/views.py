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
import pandas as pd
import traceback  # Para imprimir el error completo en la consola
import random
import json
import io
import os

""" Importación de los modelos """
from usuarios.models import *
from visitantes.models import *

# Create your views here.
@login_required
def visitas(request):
    return render(request, 'inicio/inicio.html', {
        # 'is_admin_group': is_admin_group,
        # 'is_super_admin': is_super_admin,
        # 'is_estandar_group': is_estandar_group,
    })

#* Asi se muestra una vista
@login_required
def nueva_visita(request):
    return render(request, 'visitantes/nueva-visita.html')

def guardar_algo(request):
    if request.method == "POST":
        nombre = request.POST.get('nombre')
        documento = request.POST.get('documento_identificacion')

        # Validación de campos obligatorios
        if nombre and documento:
            nuevo_registro = Visita(
                nombre=nombre,
                documento_identificacion=documento
            )
            nuevo_registro.save()  # Guardar en la base de datos
            messages.success(request, "Registro guardado con éxito.")
        else:
            messages.error(request, "Todos los campos son obligatorios.")

    return redirect('nombre_de_la_vista')  # Redirigir después de guardar

#* Ejemplo de Función para Editar un registro
def editar_algo(request, id):
    registro = Visita.objects.get(id=id) #* Visita es el modelo/tabla de la DB

    if request.method == "POST":
        nombre = request.POST.get('nombre')
        documento = request.POST.get('documento_identificacion')

        # Validación y actualización de datos
        if nombre and documento:
            registro.nombre = nombre
            registro.documento_identificacion = documento
            registro.save()  # Guardar cambios en la base de datos
            messages.success(request, "Registro actualizado con éxito.")
        else:
            messages.error(request, "Todos los campos son obligatorios.")
        
    return redirect('nombre_de_la_vista')  # Redirigir después de editar

#* Ejemplo de Función para Eliminar un registro 
def eliminar_algo(request, id):
    try:
        registro = Visita.objects.get(id=id)
        registro.delete()  # Eliminar el registro de la base de datos
        messages.success(request, "Registro eliminado con éxito.")
    except Visita.DoesNotExist:
        messages.error(request, "El registro no existe.")
    
    return redirect('nombre_de_la_vista')  # Redirigir después de eliminar