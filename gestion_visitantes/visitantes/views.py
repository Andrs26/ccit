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
from eventos.models import *

# Create your views here.
#* ************************************************************************ Principales: Mostrar datos
@login_required
def inicio_recepcion(request):
    today = timezone.localdate()
    visitas_dentro = Visita.objects.filter(estado_visitante='in').order_by('hora_ingreso')

    visitas_agendadas_hoy = Visita.objects.filter(
        Q(estado_visitante='agendado', agendado_presente='agendado'),
        fecha_visita=today
    ).order_by('fecha_visita', 'hora_ingreso')

    visitas_agendadas = Visita.objects.filter(
        Q(estado_visitante='agendado', agendado_presente='agendado'),
        fecha_visita__gt=today
    ).order_by('fecha_visita', 'hora_ingreso')

    visitantes_visita = VisitanesVisita.objects.all()
    pertenencias = PertenenciasVisitante.objects.all()
    pases = PaseAcceso.objects.all()
    pases_disponibles = PaseAcceso.objects.filter(estado_pase='Disponible').count()

    today = timezone.localdate()
    eventos_hoy = EventoCapacitacion.objects.filter(fecha=today).order_by('fecha', 'hora_inicio')
    eventos_proximos = EventoCapacitacion.objects.filter(fecha__gt=today).order_by('fecha', 'hora_inicio')

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
    
    return render(request, 'visitantes/recepcion/principales/inicio.html', {
        'visitas_dentro': visitas_dentro,
        'visitas_agendadas': visitas_agendadas,
        'visitas_agendadas_hoy': visitas_agendadas_hoy,
        'visitantes_visita': visitantes_visita,
        'pertenencias': pertenencias,
        'visitas_info': visitas_info,
        'pases': pases,
        'eventos_hoy': eventos_hoy,
        'eventos_proximos': eventos_proximos,
        'visitante_por_documento': visitante_por_documento,
        'pases_disponibles': pases_disponibles,
    })

@login_required
def buscar_inicio_recepcion(request):
    q = request.GET.get('q', '').strip()
    today = timezone.localdate()
    visitantes_visita = VisitanesVisita.objects.all()
    pertenencias = PertenenciasVisitante.objects.all()
    pases = PaseAcceso.objects.all()
    pases_disponibles = PaseAcceso.objects.filter(estado_pase='Disponible').count()

    # Crear un diccionario: { documento_identificacion: nombre }
    visitante_por_documento = {v.documento_identificacion: v.nombre for v in visitantes_visita}
    
    # Si no se proporciona query, retornamos resultados vacíos
    if not q:
        return redirect('inicio_recepcion')
    
    # Buscar en VisitanesVisita (para visitas)
    visitantes_match = VisitanesVisita.objects.filter(nombre__icontains=q)
    # Obtener los cod_visita de los visitantes encontrados
    cod_visitas = visitantes_match.values_list('cod_visita', flat=True).distinct()
    # Filtrar visitas cuya cod_visita esté en los encontrados y cuyo estado sea 'in'
    visitas_result = Visita.objects.filter(cod_visita__in=cod_visitas, estado_visitante='in').order_by('hora_ingreso')
    visitas_agendadas_result = Visita.objects.filter(cod_visita__in=cod_visitas, estado_visitante='agendado', fecha_visita=today).order_by('hora_ingreso')
    
    # Buscar en EventoVisitante (para eventos)
    evento_visitantes_match = EventoVisitante.objects.filter(nombre_visitante__icontains=q)
    # Obtener los id_evento (como cadena o número) de los registros encontrados
    id_eventos = evento_visitantes_match.values_list('id_evento', flat=True).distinct()
    # Filtrar eventos cuya id esté en los encontrados y que tengan fecha >= hoy
    eventos_result = EventoCapacitacion.objects.filter(id__in=id_eventos, fecha=today).order_by('fecha', 'hora_inicio')

    # Crear un diccionario para cada visita (clave = cod_visita)
    visitas_info = {}
    for visita in visitas_result:
        visitas_info[visita.cod_visita] = {
            'visita': visita,
            # Filtrar visitantes cuyo cod_visita coincida
            'visitantes': [v for v in visitantes_visita if v.cod_visita == visita.cod_visita],
            # Filtrar pertenencias cuyo cod_visita coincida
            'pertenencias': [p for p in pertenencias if p.cod_visita == visita.cod_visita],
        }
    
    context = {
        'resultados_visitas': visitas_result,
        'visitas_agendadas_result': visitas_agendadas_result,
        'resultados_eventos': eventos_result,
        'query': q,
        'visitantes_visita': visitantes_visita,
        'pertenencias': pertenencias,
        'visitas_info': visitas_info,
        'pases': pases,
        'visitante_por_documento': visitante_por_documento,
        'pases_disponibles': pases_disponibles,
    }
    return render(request, 'visitantes/recepcion/principales/busqueda_resultados.html', context)

@login_required
def buscar_visitas_recepcion(request):
    # Recuperar parámetros de búsqueda
    q = request.GET.get('q', '').strip()

    persona_visitada_id = request.GET.get('persona_visitada')
    persona = User.objects.get(pk=persona_visitada_id)

    fecha_str = request.GET.get('fecha', '').strip()  # formato YYYY-MM-DD
    today = timezone.localdate()
    fecha_filter = None
    if fecha_str:
        try:
            fecha_filter = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            fecha_filter = None

    # Consultas base
    visitantes_visita = VisitanesVisita.objects.all()
    pertenencias = PertenenciasVisitante.objects.all()
    pases = PaseAcceso.objects.all()
    pases_disponibles = PaseAcceso.objects.filter(estado_pase='Disponible').count()
    eventos = EventoCapacitacion.objects.all()  # opcional

    # Diccionario: documento_identificacion -> nombre
    visitante_por_documento = {v.documento_identificacion: v.nombre for v in visitantes_visita}

    # --- Filtrar visitas ---
    filtros_visita = Q()
    if q:
        # Filtrar visitantes que contienen 'q' en su nombre
        visitantes_match = VisitanesVisita.objects.filter(nombre__icontains=q)
        cod_visitas = visitantes_match.values_list('cod_visita', flat=True).distinct()
        filtros_visita &= Q(cod_visita__in=cod_visitas)
    if persona:
        filtros_visita &= Q(persona_visitada=persona)
    if fecha_filter:
        filtros_visita &= Q(fecha_visita=fecha_filter)
    
    # Aquí se filtran las visitas según el estado deseado (por ejemplo, 'agendado')
    visitas_result = Visita.objects.filter(filtros_visita, estado_visitante='agendado').order_by('fecha_visita', 'hora_ingreso')
    
    # --- Filtrar eventos ---
    # Primero, filtrar en EventoVisitante por participante (q) si se proporciona
    if q:
        evento_visitantes_match = EventoVisitante.objects.filter(nombre_visitante__icontains=q)
    else:
        evento_visitantes_match = EventoVisitante.objects.all()
    id_eventos = evento_visitantes_match.values_list('id_evento', flat=True).distinct()
    
    # Filtrar eventos por fecha
    if fecha_filter:
        eventos_result = EventoCapacitacion.objects.filter(id__in=id_eventos, fecha=fecha_filter)
    else:
        eventos_result = EventoCapacitacion.objects.filter(id__in=id_eventos)
    
    # Filtrar eventos por organizador (si se selecciona un colaborador distinto al valor por defecto)
    if persona:
        eventos_result = eventos_result.filter(organizador=persona)
    
    eventos_result = eventos_result.order_by('fecha', 'hora_inicio')
    
    # --- Construir diccionario de información de visitas ---
    visitas_info = {}
    for visita in visitas_result:
        visitas_info[visita.cod_visita] = {
            'visita': visita,
            'visitantes': [v for v in visitantes_visita if v.cod_visita == visita.cod_visita],
            'pertenencias': [p for p in pertenencias if p.cod_visita == visita.cod_visita],
        }
    
    # Para el select de colaboradores
    colaboradores = Colaborador.objects.filter(estado='activo')

    t_visitas = visitas_result.count()
    t_eventos = eventos_result.count()
    
    context = {
        'resultados_visitas': visitas_result,
        'resultados_eventos': eventos_result,
        't_visitas': t_visitas,
        't_eventos': t_eventos,
        'query': q,
        'persona': persona,
        'fecha': fecha_filter if fecha_filter else today,
        'visitantes_visita': visitantes_visita,
        'pertenencias': pertenencias,
        'visitas_info': visitas_info,
        'pases': pases,
        'eventos': eventos,
        'visitante_por_documento': visitante_por_documento,
        'pases_disponibles': pases_disponibles,
        'colaboradores': colaboradores,
    }
    return render(request, 'visitantes/recepcion/principales/busqueda_visitas_recepcion.html', context)

@login_required
def buscar_eventos_recepcion(request):
    # Recuperar parámetros de búsqueda
    q = request.GET.get('q', '').strip()
    persona = request.GET.get('persona_visitada', '').strip()  # valor seleccionado en el <select>
    fecha_str = request.GET.get('fecha', '').strip()  # formato YYYY-MM-DD
    
    today = timezone.localdate()
    fecha_filter = None
    if fecha_str:
        try:
            fecha_filter = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            fecha_filter = None

    # Consultas base
    visitantes_visita = VisitanesVisita.objects.all()
    pertenencias = PertenenciasVisitante.objects.all()
    pases = PaseAcceso.objects.all()
    pases_disponibles = PaseAcceso.objects.filter(estado_pase='Disponible').count()
    eventos = EventoCapacitacion.objects.all()  # opcional

    # Diccionario: documento_identificacion -> nombre
    visitante_por_documento = {v.documento_identificacion: v.nombre for v in visitantes_visita}
    
    # --- Filtrar eventos ---
    # Primero, filtrar en EventoVisitante por participante (q) si se proporciona
    if q:
        evento_visitantes_match = EventoVisitante.objects.filter(nombre_visitante__icontains=q)
    else:
        evento_visitantes_match = EventoVisitante.objects.all()
    id_eventos = evento_visitantes_match.values_list('id_evento', flat=True).distinct()
    
    # Filtrar eventos por fecha
    if fecha_filter:
        eventos_result = EventoCapacitacion.objects.filter(id__in=id_eventos, fecha=fecha_filter)
    else:
        eventos_result = EventoCapacitacion.objects.filter(id__in=id_eventos)
    
    # Filtrar eventos por organizador (si se selecciona un colaborador distinto al valor por defecto)
    if persona and persona.lower() != "colaborador":
        eventos_result = eventos_result.filter(organizador=persona)
    
    eventos_result = eventos_result.order_by('fecha', 'hora_inicio')
    
    
    # Para el select de colaboradores
    colaboradores = Colaborador.objects.filter(estado='activo')
    
    context = {
        'resultados_eventos': eventos_result,
        'query': q,
        'persona': persona,
        'fecha': fecha_filter if fecha_filter else today,
        'visitantes_visita': visitantes_visita,
        'pertenencias': pertenencias,
        'pases': pases,
        'eventos': eventos,
        'visitante_por_documento': visitante_por_documento,
        'pases_disponibles': pases_disponibles,
        'colaboradores': colaboradores,
    }
    return render(request, 'visitantes/recepcion/principales/busqueda_eventos_capacitaciones.html', context)

@login_required
def buscar_pase_recepcion(request):
    q = request.GET.get('q', '').strip()
    estado_pase = request.GET.get('estado_pase', '').strip()

    filtros = Q()
    if q:
        filtros &= Q(numero_pase__icontains=q)
    if estado_pase and estado_pase.lower() != "estado":
        filtros &= Q(estado_pase=estado_pase)
    
    pases = PaseAcceso.objects.filter(filtros)
    
    context = {
        'query': q,
        'estado_pase': estado_pase,
        'pases': pases,
    }
    return render(request, 'visitantes/recepcion/principales/pases.html', context)

@login_required
def visitas_recepcion(request):
    today = timezone.localdate()
    hay_visitas_agendadas = False
    hay_visitas_anteriores = False
    hay_visitas_dentro = False

    visitas_dentro = Visita.objects.filter(estado_visitante='out').order_by('fecha_visita', 'hora_ingreso')
    visitas_agendadas_hoy = Visita.objects.filter(
        Q(estado_visitante='agendado', agendado_presente='agendado'),
        fecha_visita=today
    ).order_by('fecha_visita', 'hora_ingreso')
    
    visitas_agendadas = Visita.objects.filter(
        Q(estado_visitante='agendado', agendado_presente='agendado'),
        fecha_visita__gt=today
    ).order_by('fecha_visita', 'hora_ingreso')
    
    visitas_anteriores = Visita.objects.filter(
        Q(agendado_presente='agendado'),
        fecha_visita__lt=today
    ).order_by('-fecha_visita', 'hora_ingreso')

    visitantes_visita = VisitanesVisita.objects.all()
    pertenencias = PertenenciasVisitante.objects.all()
    pases = PaseAcceso.objects.all()
    eventos = EventoCapacitacion.objects.all().order_by('fecha', 'hora_inicio')

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
    
    visitas_agendadas_hoy_info = {}
    for visita in visitas_agendadas_hoy:
        visitas_agendadas_hoy_info[visita.cod_visita] = {
            'visita': visita,
            # Filtrar visitantes cuyo cod_visita coincida
            'visitantes': [v for v in visitantes_visita if v.cod_visita == visita.cod_visita],
            # Filtrar pertenencias cuyo cod_visita coincida
            'pertenencias': [p for p in pertenencias if p.cod_visita == visita.cod_visita],
        }

    visitas_agendadas_info = {}
    for visita in visitas_agendadas:
        visitas_agendadas_info[visita.cod_visita] = {
            'visita': visita,
            # Filtrar visitantes cuyo cod_visita coincida
            'visitantes': [v for v in visitantes_visita if v.cod_visita == visita.cod_visita],
            # Filtrar pertenencias cuyo cod_visita coincida
            'pertenencias': [p for p in pertenencias if p.cod_visita == visita.cod_visita],
        }
        
    visitas_anteriores_info = {}
    for visita in visitas_anteriores:
        visitas_anteriores_info[visita.cod_visita] = {
            'visita': visita,
            # Filtrar visitantes cuyo cod_visita coincida
            'visitantes': [v for v in visitantes_visita if v.cod_visita == visita.cod_visita],
            # Filtrar pertenencias cuyo cod_visita coincida
            'pertenencias': [p for p in pertenencias if p.cod_visita == visita.cod_visita],
        }

    colaboradores = Colaborador.objects.filter(estado='activo')

    # Paginación para cada queryset    
    paginator_agendadas = Paginator(visitas_agendadas, 4)  # 10 elementos por página
    page_agendadas = request.GET.get('page_agendadas')
    visitas_agendadas_pag = paginator_agendadas.get_page(page_agendadas)

    paginator_anteriores = Paginator(visitas_anteriores, 4)
    page_anteriores = request.GET.get('page_anteriores')
    visitas_anteriores_pag = paginator_anteriores.get_page(page_anteriores)

    paginator_dentro = Paginator(visitas_dentro, 4)
    page_dentro = request.GET.get('page_dentro')
    visitas_dentro_pag = paginator_dentro.get_page(page_dentro)

    cont_visitas_agendadas = visitas_agendadas.count()
    if cont_visitas_agendadas > 0:
        hay_visitas_agendadas = True
    
    cont_visitas_anteriores = visitas_anteriores.count()
    if cont_visitas_anteriores > 0:
        hay_visitas_anteriores = True
    
    cont_visitas_dentro = visitas_dentro.count()
    if cont_visitas_dentro > 0:
        hay_visitas_dentro = True

    return render(request, 'visitantes/recepcion/principales/visitas.html', {
        'visitas_dentro': visitas_dentro_pag,
        'visitas_agendadas': visitas_agendadas_pag,
        'visitas_anteriores': visitas_anteriores_pag,
        'hay_visitas_agendadas': hay_visitas_agendadas,
        'hay_visitas_anteriores': hay_visitas_anteriores,
        'hay_visitas_dentro': hay_visitas_dentro,
        'visitas_agendadas_hoy': visitas_agendadas_hoy,
        'visitantes_visita': visitantes_visita,
        'pertenencias': pertenencias,
        'visitas_info': visitas_info,
        'visitas_agendadas_info': visitas_agendadas_info,
        'visitas_anteriores_info': visitas_anteriores_info,
        'visitas_agendadas_hoy_info': visitas_agendadas_hoy_info,
        'pases': pases,
        'eventos': eventos,
        'visitante_por_documento': visitante_por_documento,
        'colaboradores': colaboradores,
    })

@login_required
def eventos_capacitaciones(request):
    today = timezone.localdate()
    eventos_hoy = EventoCapacitacion.objects.filter(fecha=today).order_by('fecha', 'hora_inicio')
    eventos_proximos = EventoCapacitacion.objects.filter(fecha__gt=today).order_by('fecha', 'hora_inicio')
    eventos_anteriores = EventoCapacitacion.objects.filter(fecha__lt=today).order_by('-fecha', 'hora_inicio')
    # Para el select de colaboradores
    colaboradores = Colaborador.objects.filter(estado='activo')

    return render(request, 'visitantes/recepcion/principales/eventos_capacitaciones.html', {
        'eventos_hoy': eventos_hoy,
        'eventos_proximos': eventos_proximos,
        'eventos_anteriores': eventos_anteriores,
        'colaboradores': colaboradores,
    })

@login_required
def pases(request):
    pases = PaseAcceso.objects.filter(estado='activo').exclude(estado_pase='Perdido')
    visitas = Visita.objects.all()

    return render(request, 'visitantes/recepcion/principales/pases.html', {
        'pases': pases,
        'visitas': visitas,
    })

#* ************************************************************************ Secundarios: Detalles
@login_required
def detalles_evento(request,id):
    evento = EventoCapacitacion.objects.get(id=id)
    participantes_evento = EventoVisitante.objects.filter(id_evento=id)

    return render(request, 'visitantes/recepcion/secundarios/detalles_evento.html', {
        'evento': evento,
        'participantes_evento': participantes_evento,
    })

@login_required
def detalles_evento_visitas(request,id):
    evento = EventoCapacitacion.objects.get(id=id)
    participantes_evento = EventoVisitante.objects.filter(id_evento=id)

    return render(request, 'visitantes/recepcion/secundarios/detalles_evento_visitas.html', {
        'evento': evento,
        'participantes_evento': participantes_evento,
    })

#* ************************************************************************ Recepción: Formulario para crear visita.
@login_required
def nueva_visita(request):
    motivos = MotivoVisita.objects.filter(estado='activo')
    colaboradores = Colaborador.objects.filter(estado='activo')
    areasdeptos = AreaDepto.objects.filter(estado='activo')
    pases = PaseAcceso.objects.filter(Q(estado='activo') & Q(estado_pase='Disponible'))

    return render(request, 'visitantes/recepcion/formularios/nueva-visita.html', {
        'motivos': motivos,
        'colaboradores': colaboradores,
        'areasdeptos': areasdeptos,
        'pases': pases,
    })

import base64
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
User = get_user_model()

def guardar_visita(request):
    if request.method == "POST":
        # Recoger los datos del formulario
        motivo = request.POST.get("motivo")
        area_departamento = request.POST.get("area_departamento")

        persona_visitada_id = request.POST.get("persona_visitada")
        persona_visitada_instance = User.objects.get(pk=persona_visitada_id)

        num_pase = request.POST.get("pase_seleccionado")
        estado_visitante = 'in'
        agendado_presente = 'presente'
        
        # Obtener los datos JSON
        visitantes_json = request.POST.get("visitantes_data", "[]")
        materiales_json = request.POST.get("materiales_data", "[]")
        try:
            visitantes_data = json.loads(visitantes_json)
        except json.JSONDecodeError:
            visitantes_data = []
        try:
            materiales_data = json.loads(materiales_json)
        except json.JSONDecodeError:
            materiales_data = []

        # Determinar el tipo de visita
        tipo = "Individual" if len(visitantes_data) == 1 else "Grupal"
        
        # Generar cod_visita
        hoy = timezone.localdate()
        fecha_str = hoy.strftime("%Y%m%d")
        contador = Visita.objects.filter(created_at__date=hoy).count() + 1
        cod_visita = f"{fecha_str}-{contador:03d}"
        
        nombre_primero = visitantes_data[0]["nombre"] if visitantes_data else ""
        fecha_visita = hoy
        hora_ingreso = timezone.localtime().time()
        usuario_registro = request.user.id if request.user.is_authenticated else "Anonimo"
        
       # Procesar la foto: si se adjunta un archivo, o se captura mediante la cámara
        foto_documento = None
        if "foto_documento" in request.FILES:
            # Se adjuntó un archivo
            foto_uploaded = request.FILES["foto_documento"]
            if visitantes_data:
                doc_id = visitantes_data[0].get("documento", "").strip()
                if doc_id:
                    extension = foto_uploaded.name.split('.')[-1]
                    foto_uploaded.name = f"doc_iden_{doc_id}.{extension}"
            foto_documento = foto_uploaded
        else:
            # No se adjuntó archivo, revisar si se capturó la imagen (Data URL)
            foto_data = request.POST.get("foto_documento_data", "")
            if foto_data:
                try:
                    format, imgstr = foto_data.split(';base64,')
                    ext = format.split('/')[-1]
                    doc_id = ""
                    if visitantes_data:
                        doc_id = visitantes_data[0].get("documento", "").strip()
                    filename = f"doc_iden_{doc_id}.{ext}" if doc_id else f"captured.{ext}"
                    foto_documento = ContentFile(base64.b64decode(imgstr), name=filename)
                except Exception as e:
                    print("Error al procesar la imagen capturada:", e)
        
        # Crear la Visita asignándole la foto (si la hay)
        visita = Visita.objects.create(
            cod_visita=cod_visita,
            visitante=nombre_primero,
            motivo=motivo,
            tipo=tipo,
            area_departamento=area_departamento,
            persona_visitada=persona_visitada_instance,
            fecha_visita=fecha_visita,
            hora_ingreso=hora_ingreso,
            usuario_registro=request.user,
            num_pase=num_pase,
            estado_visitante=estado_visitante,
            agendado_presente=agendado_presente,
            foto_documento_identificacion=foto_documento
        )
        print("2. Visita Guardada")
        if num_pase:
            pase = PaseAcceso.objects.get(numero_pase=num_pase)
            pase.estado_pase = 'En uso'
            pase.save()
            print("1. Pase ahora está En Uso")

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

        # Crear registros de PertenenciasVisitante
        for material in materiales_data:
            documento = material.get("documento", "")
            equipo = material.get("equipo", "")
            PertenenciasVisitante.objects.create(
                cod_visita=cod_visita,
                identificacion_visitante=documento,
                pertenencias_entrada=equipo,
                usuario_registro_ingreso=usuario_registro
            )
            print("5. Pertenencias guardadas")
        
        # Enviar correo al usuario visitado
        try:
            usuario_destino = User.objects.get(id=persona_visitada_id)
            if usuario_destino.email:
                subject = "Notificación: Nueva Visita Registrada"
                message = f"Hola {usuario_destino.first_name},\n\nSe ha registrado una nueva visita para ti del visitante: {nombre_primero}, con fecha {fecha_visita} y hora de ingreso {hora_ingreso}.\n\nSaludos,\nEquipo CCIT"
                send_mail(
                    subject,
                    message,
                    None,  # O puedes usar DEFAULT_FROM_EMAIL si lo configuraste en settings.py
                    [usuario_destino.email],
                    fail_silently=False,
                )
                print("Correo enviado a", usuario_destino.email)
        except User.DoesNotExist:
            print("Usuario no encontrado para enviar correo.")

        messages.success(request, "Visita registrada exitosamente.")
        return redirect('inicio_recepcion')
    else:
        # Renderiza el formulario (carga de motivos, colaboradores, etc.)
        motivos = MotivoVisita.objects.filter(estado='activo')
        colaboradores = Colaborador.objects.filter(estado='activo')
        areasdeptos = AreaDepto.objects.filter(estado='activo')
        pases = PaseAcceso.objects.filter(estado_pase='activo')
        
        print("0. Nada pasó")
        return render(request, 'visitantes/nueva-visita.html', {
            'motivos': motivos,
            'colaboradores': colaboradores,
            'areasdeptos': areasdeptos,
            'pases': pases,
        })
    
#* ************************************************************************ Recepción: Formulario para Completar una Visita Agendada
@login_required
def ingresar_visita_agendada(request,id):
    visita = Visita.objects.get(id=id)
    visitantes_visita = VisitanesVisita.objects.filter(cod_visita=visita.cod_visita)
    motivos = MotivoVisita.objects.filter(estado='activo')
    acciones = AccionVisita.objects.filter(estado='activo')
    colaboradores = Colaborador.objects.filter(estado='activo')
    areasdeptos = AreaDepto.objects.filter(estado='activo')
    pases = PaseAcceso.objects.filter(Q(estado='activo') & Q(estado_pase='Disponible'))

    return render(request, 'visitantes/recepcion/formularios/ingresar_visita_agendada.html', {
        'motivos': motivos,
        'acciones': acciones,
        'colaboradores': colaboradores,
        'areasdeptos': areasdeptos,
        'pases': pases,
        'visita': visita,
        'visitantes_visita': visitantes_visita,
    })

import json
import base64
from django.core.files.base import ContentFile
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

@login_required
def guardar_ingresar_visita_agendada(request):
    if request.method == "POST":
        id = request.POST.get("id")
        visita = get_object_or_404(Visita, id=id)

        # Recoger datos del formulario
        persona_visitada_id = request.POST.get("persona_visitada")
        persona_visitada_instance = User.objects.get(pk=persona_visitada_id)
        print(f'{persona_visitada_id} - {persona_visitada_instance}')
        num_pase = request.POST.get("pase_seleccionado")
        
        cod_visita = visita.cod_visita
        estado_visitante = 'in'

        if num_pase:
            pase = PaseAcceso.objects.get(numero_pase=num_pase)
            pase.estado_pase = 'En uso'
            pase.save()
            print("1. Pase ahora está En Uso")
        
        # Obtener los datos JSON de visitantes y materiales
        visitantes_json = request.POST.get("visitantes_data", "[]")
        materiales_json = request.POST.get("materiales_data", "[]")
        try:
            visitantes_data = json.loads(visitantes_json)
        except json.JSONDecodeError:
            visitantes_data = []
        try:
            materiales_data = json.loads(materiales_json)
        except json.JSONDecodeError:
            materiales_data = []

        tipo = "Individual" if len(visitantes_data) == 1 else "Grupal"
        nombre_primero = visitantes_data[0]["nombre"] if visitantes_data else ""
        hora_ingreso = timezone.localtime().time()
        usuario_registro = request.user if request.user.is_authenticated else "Anonimo"
        
        # Procesar la foto: archivo o Data URL.
        foto_documento = None
        if "foto_documento" in request.FILES:
            foto_uploaded = request.FILES["foto_documento"]
            if visitantes_data:
                doc_id = visitantes_data[0].get("documento", "").strip()
                if doc_id:
                    extension = foto_uploaded.name.split('.')[-1]
                    foto_uploaded.name = f"doc_iden_{doc_id}.{extension}"
            foto_documento = foto_uploaded
        else:
            foto_data = request.POST.get("foto_documento_data", "")
            if foto_data:
                try:
                    format, imgstr = foto_data.split(';base64,')
                    ext = format.split('/')[-1]
                    doc_id = ""
                    if visitantes_data:
                        doc_id = visitantes_data[0].get("documento", "").strip()
                    filename = f"doc_iden_{doc_id}.{ext}" if doc_id else f"captured.{ext}"
                    foto_documento = ContentFile(base64.b64decode(imgstr), name=filename)
                except Exception as e:
                    print("Error al procesar la imagen capturada:", e)
        
        # Actualizar la Visita
        visita.visitante = nombre_primero
        visita.tipo = tipo
        visita.hora_ingreso = hora_ingreso
        visita.usuario_registro = usuario_registro
        if num_pase:
            visita.num_pase = num_pase
        visita.estado_visitante = estado_visitante
        visita.foto_documento_identificacion = foto_documento
        visita.save()
        print("2. Visita Guardada")
        
        # Actualizar o crear registros de Visitante
        for dato in visitantes_data:
            nombre = dato.get("nombre", "")
            documento = dato.get("documento", "")
            Visitante.objects.update_or_create(
                cod_visita=cod_visita,
                documento_identificacion=documento,
                defaults={'nombre': nombre}
            )
            print("3. Visitante actualizado o creado")
        
        # Actualizar o crear registros de VisitanesVisita
        # Supongamos que cada objeto en visitantes_data ahora tiene un campo "id" (si existe) o None.
        for dato in visitantes_data:
            rec_id = dato.get("id")  # Esto vendría del input hidden o del atributo data de la fila.
            nombre = dato.get("nombre", "").strip()
            documento = dato.get("documento", "").strip()
            
            if rec_id:  
                # Actualizamos el registro con ese id.
                VisitanesVisita.objects.filter(id=rec_id).update(nombre=nombre, documento_identificacion=documento)
            else:
                # Si no hay id, usamos update_or_create para buscar por cod_visita y, por ejemplo, por nombre si no existe un documento.
                VisitanesVisita.objects.update_or_create(
                    cod_visita=cod_visita,
                    documento_identificacion=documento,  # o, si está vacío, podrías buscar por nombre
                    defaults={'nombre': nombre}
                )
        
        # Crear registros de PertenenciasVisitante
        for material in materiales_data:
            documento = material.get("documento", "")
            equipo = material.get("equipo", "")
            PertenenciasVisitante.objects.create(
                cod_visita=cod_visita,
                identificacion_visitante=documento,
                pertenencias_entrada=equipo,
                usuario_registro_ingreso=usuario_registro
            )
            print("5. Pertenencias guardadas")

        # Enviar correo al usuario visitado
        try:
            usuario_destino = User.objects.get(id=persona_visitada_id)
            if usuario_destino.email:
                subject = "Notificación: Nueva Visita Registrada"
                hora_ingreso_formateada = hora_ingreso.strftime("%H:%M")
                message = f"Hola {usuario_destino.first_name},\n\nSe ha registrado una nueva visita para ti del visitante: '{nombre_primero}', con fecha {visita.fecha_visita} y hora de ingreso {hora_ingreso_formateada}.\n\nSaludos,\nEquipo CCIT"
                send_mail(
                    subject,
                    message,
                    None,  # O puedes usar DEFAULT_FROM_EMAIL si lo configuraste en settings.py
                    [usuario_destino.email],
                    fail_silently=False,
                )
                print("Correo enviado a", usuario_destino.email)
        except User.DoesNotExist:
            print("Usuario no encontrado para enviar correo.")

        messages.success(request, "Visita registrada exitosamente.")
        return redirect('inicio_recepcion')
    else:
        motivos = MotivoVisita.objects.filter(estado='activo')
        colaboradores = Colaborador.objects.filter(estado='activo')
        areasdeptos = AreaDepto.objects.filter(estado='activo')
        pases = PaseAcceso.objects.filter(estado_pase='activo')
        print("0. Nada pasó")
        return render(request, 'visitantes/nueva-visita-agendada.html', {
            'motivos': motivos,
            'colaboradores': colaboradores,
            'areasdeptos': areasdeptos,
            'pases': pases,
        })
    
@login_required
def cambiar_pase(request):
    if request.method == "POST":
        id = request.POST.get("id")
        visita = get_object_or_404(Visita, id=id)

        pase_actual = request.POST.get("pase_actual")
        num_pase = request.POST.get("pase_seleccionado")
        
        if pase_actual:
            pase = PaseAcceso.objects.get(numero_pase=pase_actual)
            pase.estado_pase = 'Disponible'
            pase.save()
        
        if num_pase:
            pase = PaseAcceso.objects.get(numero_pase=num_pase)
            pase.estado_pase = 'En uso'
            pase.save()
        
        visita.num_pase = num_pase
        visita.save()
        
        messages.success(request, "El pase se cambió correctamente.")
        return redirect('inicio_recepcion')

#* ************************************************************************ Parametros: Motivos
@login_required
def motivos(request):
    motivos = MotivoVisita.objects.all()

    return render(request, 'parametros/parametros.html', {
        'motivos': motivos
    })

def crear_motivo(request):
    """
    Vista para crear un nuevo MotivoVisita usando un formulario HTML.
    Se asigna el estado 'activo' por defecto.
    """
    if request.method == 'POST':
        descripcion = request.POST.get('descripcion')
        accion = request.POST.get('accion')

        # Se pueden agregar validaciones adicionales aquí
        MotivoVisita.objects.create(
            descripcion=descripcion,
            accion=accion,
            estado='activo'
        )
        messages.success(request, "Motivo agregado correctamente.")
        return redirect(request.META.get('HTTP_REFERER', '/'))  # Regresa donde estaba
    messages.error(request, "No se agregó el motivo.")
    return render(request, 'parametros/parametros.html')


def editar_motivo(request, motivo_id):
    """
    Vista para editar un MotivoVisita existente usando un formulario HTML.
    """
    motivo = get_object_or_404(MotivoVisita, id=motivo_id)
    if request.method == 'POST':
        motivo.descripcion = request.POST.get('descripcion')
        motivo.accion = request.POST.get('accion')
        motivo.save()
        messages.success(request, "Motivo editado correctamente.")
        return redirect(request.META.get('HTTP_REFERER', '/'))  # Regresa donde estaba
    messages.error(request, "No se editó el motivo.")
    return render(request, 'motivos/editar_motivo.html', {'motivo': motivo})


def cambiar_estado_motivo(request):
    """
    Vista para cambiar el estado del motivo a 'inactivo' mediante AJAX.
    Se espera recibir por POST el 'motivo_id'.
    """
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        motivo_id = request.POST.get('motivo_id')
        motivo = get_object_or_404(MotivoVisita, id=motivo_id)
        if motivo.estado == 'activo':
            motivo.estado = 'inactivo'
        elif motivo.estado == 'inactivo':
            motivo.estado = 'activo'
        motivo.save()
        return JsonResponse({
            'success': True,
            'motivo_id': motivo_id,
            'estado': motivo.estado
        })
    return JsonResponse({'success': False}, status=400)

#* ************************************************************************ Parametros: Acciones
@login_required
def acciones(request):
    acciones_base = AccionVisita.objects.all()

    paginator_acciones = Paginator(acciones_base, 10)
    page_acciones = request.GET.get('page_acciones')
    acciones = paginator_acciones.get_page(page_acciones)

    return render(request, 'parametros/acciones.html', {
        'acciones': acciones
    })
    

def crear_accion(request):
    if request.method == 'POST':
        accion = request.POST.get('accion')
        AccionVisita.objects.create(
            accion=accion,
            estado='activo'
        )
        messages.success(request, "Acción agregada correctamente.")
        return redirect(request.META.get('HTTP_REFERER', '/'))  # Regresa donde estaba
    messages.error(request, "No se agregó la acción.")
    return render(request, 'parametros/acciones.html')


def editar_accion(request, accion_id):
    accion = get_object_or_404(AccionVisita, id=accion_id)
    if request.method == 'POST':
        accion.accion = request.POST.get('accion')
        accion.save()
        messages.success(request, "Acción editada correctamente.")
        return redirect(request.META.get('HTTP_REFERER', '/'))  # Regresa donde estaba
    messages.error(request, "No se editó la acción.")
    return redirect(request.META.get('HTTP_REFERER', '/'))  # Regresa donde estaba

def cambiar_estado_accion(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        accion_id = request.POST.get('accion_id')
        accion = get_object_or_404(AccionVisita, id=accion_id)
        if accion.estado == 'activo':
            accion.estado = 'inactivo'
        elif accion.estado == 'inactivo':
            accion.estado = 'activo'
        accion.save()
        return JsonResponse({
            'success': True,
            'accion_id': accion_id,
            'estado': accion.estado
        })
    return JsonResponse({'success': False}, status=400)

#* ************************************************************************ Parametros: Colaboradores
@login_required
def colaboradores(request):
    colaboradores = Colaborador.objects.all()

    return render(request, 'parametros/colaboradores.html', {
        'colaboradores': colaboradores
    })

@login_required
def buscar_colaboradores(request):
    nombre_query = request.GET.get('nombre', '').strip()

    if nombre_query:
        # Filtrar colaboradores por el campo 'nombre' que contenga el criterio (insensible a mayúsculas/minúsculas)
        colaboradores = Colaborador.objects.filter(nombre__icontains=nombre_query)
    else:
        colaboradores = Colaborador.objects.all()

    return render(request, 'parametros/colaboradores.html', {
        'colaboradores': colaboradores,
        'nombre_query': nombre_query,  # Para mantener el valor en el formulario si lo deseas
    })

def crear_colaborador(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        usuario = request.POST.get('usuario')
        Colaborador.objects.create(
            nombre=nombre,
            usuario=usuario,
            estado='activo'
        )
        messages.success(request, "Colaborador agregado correctamente.")
        return redirect(request.META.get('HTTP_REFERER', '/'))  # Regresa donde estaba
    messages.error(request, "No se agregó el colaborador.")
    return render(request, 'parametros/colaboradores.html')


def editar_colaborador(request, colaborador_id):
    colaborador = get_object_or_404(Colaborador, id=colaborador_id)
    if request.method == 'POST':
        colaborador.nombre = request.POST.get('nombre')
        colaborador.usuario = request.POST.get('usuario')
        colaborador.save()
        messages.success(request, "Colaborador editado correctamente.")
        return redirect(request.META.get('HTTP_REFERER', '/'))  # Regresa donde estaba
    messages.error(request, "No se editó el colaborador.")
    return redirect(request.META.get('HTTP_REFERER', '/'))  # Regresa donde estaba

def cambiar_estado_colaborador(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        colaborador_id = request.POST.get('colaborador_id')
        colaborador = get_object_or_404(Colaborador, id=colaborador_id)
        if colaborador.estado == 'activo':
            colaborador.estado = 'inactivo'
        elif colaborador.estado == 'inactivo':
            colaborador.estado = 'activo'
        colaborador.save()
        return JsonResponse({
            'success': True,
            'colaborador_id': colaborador_id,
            'estado': colaborador.estado
        })
    return JsonResponse({'success': False}, status=400)

#* ************************************************************************ AJAX
def buscar_visitante_ajax(request):
    query = request.GET.get('q', '')
    visitantes = Visitante.objects.filter(nombre__icontains=query)
    data = []
    for v in visitantes:
        data.append({
            'id': v.id,
            'nombre': v.nombre,
            'documento': v.documento_identificacion,
        })
    return JsonResponse(data, safe=False)
    
#* ************************************************************************ Recepción: Dar salida a una visita
def salida_visita(request):
    if request.method == "POST":
        # Recibir el código de visita enviado desde el formulario (hidden)
        cod_visita = request.POST.get("cod_visita")
        if not cod_visita:
            messages.error(request, "No se proporcionó el código de visita.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        # Obtener la Visita y actualizar estado y hora de salida
        try:
            visita = Visita.objects.get(cod_visita=cod_visita)
        except Visita.DoesNotExist:
            messages.error(request, "La visita no existe.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        visita.estado_visitante = 'out'
        visita.hora_salida = timezone.localtime().time()  # Hora actual local
        visita.save()
        
        # Actualizar el pase: obtener num_pase de la visita y actualizar su estado a 'Disponible'
        num_pase = visita.num_pase
        if num_pase:
            try:
                pase = PaseAcceso.objects.get(numero_pase=num_pase)
                pase.estado_pase = 'Disponible'
                pase.save()
            except PaseAcceso.DoesNotExist:
                # Opcional: registrar un log o notificar
                pass

        # Actualizar los registros de PertenenciasVisitante asociados a este cod_visita
        pertenencias = PertenenciasVisitante.objects.filter(cod_visita=cod_visita)
        fecha_actual_str = timezone.localdate().strftime("%Y%m%d")
        for p in pertenencias:
            # Actualizar pertenencias_salida si se envía
            salida_valor = request.POST.get(f'pertenencias_salida_{p.id}', '')
            if salida_valor:
                p.pertenencias_salida = salida_valor

            # Actualizar observaciones_salida si se envía
            obs_valor = request.POST.get(f'observaciones_salida_{p.id}', '')
            if obs_valor:
                p.observaciones_salida = obs_valor

            # Si se envía un archivo para documento soporte (input name="doc_soporte_<p.id>")
            if f'doc_soporte_{p.id}' in request.FILES:
                archivo = request.FILES[f'doc_soporte_{p.id}']
                extension = archivo.name.split('.')[-1]
                # Renombrar con el patrón: [cod_visita]_[identificacion_visitante]_[fecha_actual].[ext]
                archivo.name = f"{cod_visita}_{p.identificacion_visitante}_{fecha_actual_str}.{extension}"
                p.documento_soporte = archivo

            # Si se envía un archivo para aceptación (input name="aceptacion_<p.id>")
            if f'aceptacion_{p.id}' in request.FILES:
                archivo2 = request.FILES[f'aceptacion_{p.id}']
                p.aceptacion = archivo2

            # Registrar quien hizo la salida (usuario en sesión)
            p.usuario_registro_salida = request.user.id if request.user.is_authenticated else "Anonimo"
            p.save()

        messages.success(request, "Salida registrada exitosamente.")
        return redirect(request.META.get('HTTP_REFERER', '/'))
    else:
        messages.error(request, "Método no permitido.")
        return redirect(request.META.get('HTTP_REFERER', '/'))