from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.utils.timezone import now
from .models import *
import requests
from concurrent.futures import ThreadPoolExecutor
from django.contrib import messages

def verificar_estado(servicio):
    try:
        r = requests.get(servicio.url, timeout=5)
        status_code = r.status_code
        detalle = r.reason
    except requests.RequestException as e:
        status_code = "ERROR"
        detalle = str(e)

    # Guardar en la base de datos
    ChequeoServicio.objects.create(servicio=servicio, estado=status_code, detalle=detalle)
    servicio.ultimo_estado = status_code
    servicio.ultimo_detalle = detalle
    servicio.ultima_revision = now()
    servicio.save()

    return {
        "servicio": servicio,
        "status": status_code,
        "detalle": detalle,
        "revision": servicio.ultima_revision,
    }

def listar_servicios(request):
    servicios = ServicioWeb.objects.filter(activo=True)
    resultados = []
    errores = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        for resultado in executor.map(verificar_estado, servicios):
            servicio = resultado["servicio"]
            status = resultado["status"]
            detalle = resultado["detalle"]

            # Icono de estado
            if status == 200:
                icono = "🟢"
            elif isinstance(status, int) and 300 <= status < 400:
                icono = "🟡"
            else:
                icono = "🔴"
                errores.append(f"{servicio.nombre} ({servicio.url}) - {status}: {detalle}")

            resultados.append({
                "servicio": servicio,
                "status": status,
                "detalle": detalle,
                "icono": icono,
                "revision": resultado["revision"],
            })

    # Notificación por correo si hay errores
    if errores:
        grupo = Group.objects.filter(name="visitas_it_group").first()
        if grupo:
            correos = grupo.user_set.values_list('email', flat=True)
            mensaje = "\n".join(errores)
            send_mail(
                subject="⚠️ Servicios con errores detectados",
                message=mensaje,
                from_email=None,
                recipient_list=list(correos),
                fail_silently=True
            )

    return render(request, 'monitor/estado_servicios.html', {'resultados': resultados})

def crear_servicio(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        url = request.POST.get('url')
        descripcion = request.POST.get('descripcion')
        activo = request.POST.get('activo') == 'on'

        ServicioWeb.objects.create(nombre=nombre, url=url, descripcion=descripcion, activo=activo)
        messages.success(request, "Servicio agregado correctamente.")
    return redirect('listar_servicios')

def editar_servicio(request, pk):
    servicio = get_object_or_404(ServicioWeb, pk=pk)
    if request.method == 'POST':
        servicio.nombre = request.POST.get('nombre')
        servicio.url = request.POST.get('url')
        servicio.descripcion = request.POST.get('descripcion')
        servicio.activo = request.POST.get('activo') == 'on'
        servicio.save()
        messages.success(request, "Servicio actualizado correctamente.")
    return redirect('listar_servicios')

def eliminar_servicio(request, pk):
    servicio = get_object_or_404(ServicioWeb, pk=pk)
    if request.method == 'POST':
        servicio.delete()
        messages.success(request, "Servicio eliminado correctamente.")
    return redirect('listar_servicios')