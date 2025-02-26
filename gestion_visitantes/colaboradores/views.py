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
from datetime import datetime
import pandas as pd
import traceback  # Para imprimir el error completo en la consola
import random
import json
import io
import os

""" Importación de los modelos """
from usuarios.models import *
from visitantes.models import *
from pases.models import *
from pertenencias.models import *

# Create your views here.
@login_required
def colaboradores_home(request):
    visitas_dentro = Visita.objects.filter(estado_visitante='in')
    visitas_agendadas = Visita.objects.filter(agendado_presente='agendado')
    visitantes_visita = VisitanesVisita.objects.all()
    pertenencias = PertenenciasVisitante.objects.all()
    pases = PaseAcceso.objects.all()

    # Crear un diccionario: { documento_identificacion: nombre }
    visitante_por_documento = {v.documento_identificacion: v.nombre for v in visitantes_visita}

    # Crear un diccionario para cada visita (clave = cod_visita)
    visitas_info = {}
    for visita in visitas_dentro:
        visitas_info[visita.cod_visita] = {
            'visita': visita,
            # Filtrar visitantes cuyo cod_visita coincida
            'visitantes': [v for v in visitantes_visita if v.cod_visita == visita.cod_visita],
            # Filtrar pertenencias cuyo cod_visita coincida
            'pertenencias': [p for p in pertenencias if p.cod_visita == visita.cod_visita],
        }
    
    return render(request, 'colaboradores/inicio.html', {
        'visitas_dentro': visitas_dentro,
        'visitas_agendadas': visitas_agendadas,
        'visitantes_visita': visitantes_visita,
        'pertenencias': pertenencias,
        'visitas_info': visitas_info,
        'pases': pases,
        'visitante_por_documento': visitante_por_documento,
    })

@login_required
def nueva_visita(request):
    motivos = MotivoVisita.objects.filter(estado='activo')
    colaboradores = Colaborador.objects.filter(estado='activo')
    areasdeptos = AreaDepto.objects.filter(estado='activo')
    pases = PaseAcceso.objects.filter(Q(estado='activo') & Q(estado_pase='Disponible'))

    return render(request, 'colaboradores/nueva-visita.html', {
        'motivos': motivos,
        'colaboradores': colaboradores,
        'areasdeptos': areasdeptos,
        'pases': pases,
    })

def guardar_visita(request):
    if request.method == "POST":
        # Recoger los datos del formulario
        motivo = request.POST.get("motivo")
        area_departamento = request.POST.get("area_departamento")
        persona_visitada = request.POST.get("persona_visitada")

        estado_visitante = 'agendado'
        agendado_presente = 'agendado'
        
        # Obtener los datos JSON
        visitantes_json = request.POST.get("visitantes_data", "[]")
        
        try:
            visitantes_data = json.loads(visitantes_json)
        except json.JSONDecodeError:
            visitantes_data = []

        # Determinar el tipo de visita
        tipo = "Individual" if len(visitantes_data) == 1 else "Grupal"
        fecha_visita = request.POST.get("fecha")
        
        # Generar cod_visita
        hoy = timezone.localdate()
        fecha_str = hoy.strftime("%Y%m%d")
        contador = Visita.objects.filter(fecha_visita=fecha_visita).count() + 1
        cod_visita = f"{fecha_str}-{contador:03d}"
        
        nombre_primero = visitantes_data[0]["nombre"] if visitantes_data else ""
        hora_ingreso = request.POST.get("hora")
        
        # Crear la Visita asignándole la foto (si la hay)
        visita = Visita.objects.create(
            cod_visita=cod_visita,
            visitante=nombre_primero,
            motivo=motivo,
            tipo=tipo,
            area_departamento=area_departamento,
            persona_visitada=persona_visitada,
            fecha_visita=fecha_visita,
            hora_ingreso=hora_ingreso,
            estado_visitante=estado_visitante,
            agendado_presente=agendado_presente,
        )
        print("2. Visita Agendada")

        # Crear registros de Visitante (sin foto)
        for index, dato in enumerate(visitantes_data):
            nombre = dato.get("nombre", "")
            documento = dato.get("documento", "")
            if Visitante.objects.filter(documento_identificacion=documento).exists():
                continue
            Visitante.objects.create(
                cod_visita=cod_visita,
                nombre=nombre,
                documento_identificacion=documento
            )
            print("3. Visitantes Guardados")
        
        # Crear registros de Visitantes de la Visita (sin foto)
        for index, dato in enumerate(visitantes_data):
            nombre = dato.get("nombre", "")
            documento = dato.get("documento", "")
            VisitanesVisita.objects.create(
                cod_visita=cod_visita,
                nombre=nombre,
                documento_identificacion=documento
            )
            print("4. Visitantes de la visita Guardados")

        messages.success(request, "Visita agendada exitosamente.")
        return redirect(request.META.get('HTTP_REFERER', '/'))
    else:
        # Renderiza el formulario (carga de motivos, colaboradores, etc.)
        motivos = MotivoVisita.objects.filter(estado='activo')
        colaboradores = Colaborador.objects.filter(estado='activo')
        areasdeptos = AreaDepto.objects.filter(estado='activo')
        pases = PaseAcceso.objects.filter(estado_pase='activo')
        
        print("0. Nada pasó")
        return render(request, 'colaboradores/nueva-visita.html', {
            'motivos': motivos,
            'colaboradores': colaboradores,
            'areasdeptos': areasdeptos,
            'pases': pases,
        })