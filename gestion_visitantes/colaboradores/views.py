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
@login_required
def colaboradores_home(request):
    today = timezone.localdate()
    visitas_dentro = Visita.objects.filter(estado_visitante='in', persona_visitada=request.user.username).order_by('fecha_visita','hora_ingreso')
    
    visitas_agendadas_hoy = Visita.objects.filter(
        Q(estado_visitante='agendado', agendado_presente='agendado', persona_visitada=request.user.username),
        fecha_visita=today
    ).order_by('fecha_visita', 'hora_ingreso')

    visitas_agendadas = Visita.objects.filter(
        Q(estado_visitante='agendado', agendado_presente='agendado', persona_visitada=request.user.username),
        fecha_visita__gt=today
    ).order_by('fecha_visita', 'hora_ingreso')

    visitantes_visita = VisitanesVisita.objects.all()
    pertenencias = PertenenciasVisitante.objects.all()
    pases = PaseAcceso.objects.all()
    eventos_hoy = EventoCapacitacion.objects.filter(organizador=request.user.username, fecha=today).order_by('fecha', 'hora_inicio')
    eventos_proximos = EventoCapacitacion.objects.filter(organizador=request.user.username, fecha__gt=today).order_by('fecha', 'hora_inicio')

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
    
    return render(request, 'colaboradores/inicio_visitas.html', {
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
    })

#* ************************************************************************ Recepción: Mostrar datos
@login_required
def visitas_colaborador(request):
    today = timezone.localdate()
    visitas_dentro = Visita.objects.filter(estado_visitante='out', persona_visitada=request.user.username).order_by('fecha_visita', 'hora_ingreso')
    
    visitas_agendadas = Visita.objects.filter(
        Q(estado_visitante='agendado', agendado_presente='agendado', persona_visitada=request.user.username),
        fecha_visita=today
    ).order_by('fecha_visita', 'hora_ingreso')
    
    visitas_proximas_agendadas = Visita.objects.filter(
        Q(estado_visitante='agendado', agendado_presente='agendado', persona_visitada=request.user.username),
        fecha_visita__gt=today
    ).order_by('fecha_visita', 'hora_ingreso')
    
    visitas_agendadas_anteriormente = Visita.objects.filter(
        Q(agendado_presente='agendado', persona_visitada=request.user.username),
        fecha_visita__lt=today
    ).exclude(estado_visitante='in').order_by('fecha_visita', 'hora_ingreso')

    visitantes_visita = VisitanesVisita.objects.all()
    pertenencias = PertenenciasVisitante.objects.all()
    pases = PaseAcceso.objects.all()
    eventos_hoy = EventoCapacitacion.objects.filter(organizador=request.user.username, fecha=today).order_by('fecha', 'hora_inicio')
    eventos_proximos = EventoCapacitacion.objects.filter(organizador=request.user.username, fecha__gt=today).order_by('fecha', 'hora_inicio')
    eventos_anteriores = EventoCapacitacion.objects.filter(organizador=request.user.username, fecha__lt=today).order_by('fecha', 'hora_inicio')

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
    
    visitas_agendadas_info = {}
    for visita in visitas_agendadas:
        visitas_agendadas_info[visita.cod_visita] = {
            'visita': visita,
            # Filtrar visitantes cuyo cod_visita coincida
            'visitantes': [v for v in visitantes_visita if v.cod_visita == visita.cod_visita],
            # Filtrar pertenencias cuyo cod_visita coincida
            'pertenencias': [p for p in pertenencias if p.cod_visita == visita.cod_visita],
        }
    
    visitas_proximas_agendadas_info = {}
    for visita in visitas_proximas_agendadas:
        visitas_proximas_agendadas_info[visita.cod_visita] = {
            'visita': visita,
            # Filtrar visitantes cuyo cod_visita coincida
            'visitantes': [v for v in visitantes_visita if v.cod_visita == visita.cod_visita],
            # Filtrar pertenencias cuyo cod_visita coincida
            'pertenencias': [p for p in pertenencias if p.cod_visita == visita.cod_visita],
        }
    
    visitas_agendadas_anteriormente_info = {}
    for visita in visitas_agendadas_anteriormente:
        visitas_agendadas_anteriormente_info[visita.cod_visita] = {
            'visita': visita,
            # Filtrar visitantes cuyo cod_visita coincida
            'visitantes': [v for v in visitantes_visita if v.cod_visita == visita.cod_visita],
            # Filtrar pertenencias cuyo cod_visita coincida
            'pertenencias': [p for p in pertenencias if p.cod_visita == visita.cod_visita],
        }
    
    return render(request, 'visitantes/colaborador/visitas.html', {
        'visitas_dentro': visitas_dentro,
        'visitas_agendadas': visitas_agendadas,
        'visitas_proximas_agendadas': visitas_proximas_agendadas,
        'visitas_agendadas_anteriormente': visitas_agendadas_anteriormente,
        'visitantes_visita': visitantes_visita,
        'pertenencias': pertenencias,
        'visitas_info': visitas_info,
        'visitas_agendadas_info': visitas_agendadas_info,
        'visitas_proximas_agendadas_info': visitas_proximas_agendadas_info,
        'visitas_agendadas_anteriormente_info': visitas_agendadas_anteriormente_info,
        'pases': pases,
        'eventos_hoy': eventos_hoy,
        'eventos_proximos': eventos_proximos,
        'eventos_anteriores': eventos_anteriores,
        'visitante_por_documento': visitante_por_documento,
    })

#* ************************************************************************ Recepción: Eventos
@login_required
def eventos_capacitaciones_colaborador(request):
    today = timezone.localdate()
    eventos = EventoCapacitacion.objects.filter(organizador=request.user.username)
    eventos_hoy = EventoCapacitacion.objects.filter(organizador=request.user.username, fecha=today).order_by('fecha', 'hora_inicio')
    eventos_proximos = EventoCapacitacion.objects.filter(organizador=request.user.username, fecha__gt=today).order_by('fecha', 'hora_inicio')
    eventos_anteriores = EventoCapacitacion.objects.filter(organizador=request.user.username, fecha__lt=today).order_by('fecha', 'hora_inicio')

    return render(request, 'visitantes/colaborador/eventos_capacitaciones.html', {
        'eventos': eventos,
        'eventos_hoy': eventos_hoy,
        'eventos_proximos': eventos_proximos,
        'eventos_anteriores': eventos_anteriores,
    })

@login_required
def detalles_evento(request,id):
    evento = EventoCapacitacion.objects.get(id=id)
    participantes_evento = EventoVisitante.objects.filter(id_evento=id)

    return render(request, 'visitantes/colaborador/detalles_evento.html', {
        'evento': evento,
        'participantes_evento': participantes_evento,
    })

#* ************************************************************************ Detalle Visita
@login_required
def detalle_visita_agendada(request,id):
    visita = Visita.objects.get(id=id)
    visitantes_visita = VisitanesVisita.objects.filter(cod_visita=visita.cod_visita)
    motivos = MotivoVisita.objects.filter(estado='activo')
    acciones = AccionVisita.objects.filter(estado='activo')
    colaboradores = Colaborador.objects.filter(estado='activo')
    areasdeptos = AreaDepto.objects.filter(estado='activo')
    pases = PaseAcceso.objects.filter(Q(estado='activo') & Q(estado_pase='Disponible'))

    return render(request, 'visitantes/colaborador/detalle_visita_agendada.html', {
        'motivos': motivos,
        'acciones': acciones,
        'colaboradores': colaboradores,
        'areasdeptos': areasdeptos,
        'pases': pases,
        'visita': visita,
        'visitantes_visita': visitantes_visita,
    })

@login_required
def detalle_visita_dentro(request,id):
    visita = Visita.objects.get(id=id)
    visitantes_visita = VisitanesVisita.objects.filter(cod_visita=visita.cod_visita)
    motivos = MotivoVisita.objects.filter(estado='activo')
    acciones = AccionVisita.objects.filter(estado='activo')
    colaboradores = Colaborador.objects.filter(estado='activo')
    areasdeptos = AreaDepto.objects.filter(estado='activo')
    pases = PaseAcceso.objects.filter(Q(estado='activo') & Q(estado_pase='Disponible'))

    return render(request, 'visitantes/colaborador/detalle_visita_dentro.html', {
        'motivos': motivos,
        'acciones': acciones,
        'colaboradores': colaboradores,
        'areasdeptos': areasdeptos,
        'pases': pases,
        'visita': visita,
        'visitantes_visita': visitantes_visita,
    })

@login_required
def nueva_visita(request):
    motivos = MotivoVisita.objects.filter(estado='activo')
    colaboradores = Colaborador.objects.filter(estado='activo')
    areasdeptos = AreaDepto.objects.filter(estado='activo')
    pases = PaseAcceso.objects.filter(Q(estado='activo') & Q(estado_pase='Disponible'))

    return render(request, 'visitantes/colaborador/nueva-visita.html', {
        'motivos': motivos,
        'colaboradores': colaboradores,
        'areasdeptos': areasdeptos,
        'pases': pases,
    })

def guardar_visita(request):
    if request.method == "POST":
        # Recoger los datos del formulario
        motivo = request.POST.get("motivo")
        accion = request.POST.get("accion")
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
        contador = Visita.objects.filter(created_at__date=hoy).count() + 1
        cod_visita = f"{fecha_str}-{contador:03d}"
        
        nombre_primero = visitantes_data[0]["nombre"] if visitantes_data else ""
        hora_ingreso = request.POST.get("hora")
        
        # Crear la Visita asignándole la foto (si la hay)
        visita = Visita.objects.create(
            cod_visita=cod_visita,
            visitante=nombre_primero,
            motivo=motivo,
            accion=accion,
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
        return redirect('colaboradores_home')
    else:
        # Renderiza el formulario (carga de motivos, colaboradores, etc.)
        motivos = MotivoVisita.objects.filter(estado='activo')
        colaboradores = Colaborador.objects.filter(estado='activo')
        areasdeptos = AreaDepto.objects.filter(estado='activo')
        pases = PaseAcceso.objects.filter(estado_pase='activo')
        
        print("0. Nada pasó")
        return render(request, 'visitantes/colaborador/nueva-visita.html', {
            'motivos': motivos,
            'colaboradores': colaboradores,
            'areasdeptos': areasdeptos,
            'pases': pases,
        })
    
def salida_mea_visita(request):
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
            p.usuario_registro_salida = request.user.username if request.user.is_authenticated else "Anonimo"
            p.save()

        messages.success(request, "Salida de [Material/Equipo/Articulos] registrada exitosamente.")
        return redirect('colaboradores_home')
    else:
        messages.error(request, "Método no permitido.")
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
#* ************************************************************************ Colaborador: Formulario para crear evento.
@login_required
def nuevo_evento(request):
    colaboradores = Colaborador.objects.filter(estado='activo')

    return render(request, 'visitantes/colaborador/nuevo_evento.html', {
        'colaboradores': colaboradores,
    })

#* ************************************************************************ Recepción: Nueva Visita Agendada
@login_required
def nueva_visita_agendada(request,id):
    visita = Visita.objects.get(id=id)
    visitantes_visita = VisitanesVisita.objects.filter(cod_visita=visita.cod_visita)
    motivos = MotivoVisita.objects.filter(estado='activo')
    acciones = AccionVisita.objects.filter(estado='activo')
    colaboradores = Colaborador.objects.filter(estado='activo')
    areasdeptos = AreaDepto.objects.filter(estado='activo')
    pases = PaseAcceso.objects.filter(Q(estado='activo') & Q(estado_pase='Disponible'))

    return render(request, 'visitantes/colaborador/nueva-visita-agendada.html', {
        'motivos': motivos,
        'acciones': acciones,
        'colaboradores': colaboradores,
        'areasdeptos': areasdeptos,
        'pases': pases,
        'visita': visita,
        'visitantes_visita': visitantes_visita,
    })

#* ************************************************************************ Editar Visita Agendada
@login_required
def editar_visita_agendada(request):
    if request.method == "POST":
        id = request.POST.get("id")
        visita = get_object_or_404(Visita, id=id)

        # Recoger datos del formulario
        motivo = request.POST.get("motivo")
        accion = request.POST.get("accion")
        area_departamento = request.POST.get("area_departamento")
        persona_visitada = request.POST.get("persona_visitada")
        hora_ingreso = request.POST.get("hora")
        fecha_visita = request.POST.get("fecha")
        cod_visita = visita.cod_visita
        
        # Obtener los datos JSON de visitantes y materiales
        visitantes_json = request.POST.get("visitantes_data", "[]")
        
        try:
            visitantes_data = json.loads(visitantes_json)
        except json.JSONDecodeError:
            visitantes_data = []

        tipo = "Individual" if len(visitantes_data) == 1 else "Grupal"
        nombre_primero = visitantes_data[0]["nombre"] if visitantes_data else ""
        usuario_registro = request.user.username if request.user.is_authenticated else "Anonimo"
        
        # Procesar la foto: archivo o Data URL.
        
        # Actualizar la Visita
        visita.visitante = nombre_primero
        visita.motivo = motivo
        visita.accion = accion
        visita.tipo = tipo
        visita.area_departamento = area_departamento
        visita.persona_visitada = persona_visitada
        visita.usuario_registro = usuario_registro
        visita.hora_ingreso = hora_ingreso
        visita.fecha_visita = fecha_visita
        visita.save()
        print("2. Visita Guardada")
        
        # Primero, eliminar los registros existentes para esa visita.
        Visitante.objects.filter(cod_visita=cod_visita).delete()
        VisitanesVisita.objects.filter(cod_visita=cod_visita).delete()

        # Luego, para cada dato en visitantes_data, crear nuevos registros.
        for dato in visitantes_data:
            nombre = dato.get("nombre", "").strip()
            documento = dato.get("documento", "").strip()
            Visitante.objects.create(
                cod_visita=cod_visita,
                nombre=nombre,
                documento_identificacion=documento
            )
            VisitanesVisita.objects.create(
                cod_visita=cod_visita,
                nombre=nombre,
                documento_identificacion=documento
            )

        messages.success(request, "Visita registrada exitosamente.")
        return redirect(request.META.get('HTTP_REFERER', '/'))
    else:
        messages.error(request, "Algo no va bien")
        return redirect(request.META.get('HTTP_REFERER', '/'))