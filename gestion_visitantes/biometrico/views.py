from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from .utils import sincronizar_usuarios
from .pyzk.zkmodules.zk.base import ZK
from django.core.paginator import Paginator
from django.db.models import Q, Min, Max
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.contrib import messages
from django.contrib.auth.models import User

def home_rrhh(request):
    return render(request, 'rrhh/home.html')

def datos_crudos_reloj(request):
    zk = ZK('192.168.2.107', port=4370, timeout=5)
    usuarios = []
    asistencias = []
    error = None

    try:
        conn = zk.connect()
        conn.disable_device()

        usuarios_raw = conn.get_users()
        asistencias_raw = conn.get_attendance()

        usuarios = [u.__dict__ for u in usuarios_raw]
        asistencias = [a.__dict__ for a in asistencias_raw]

        conn.enable_device()
        conn.disconnect()
    except Exception as e:
        error = str(e)

    return render(request, 'rrhh/usuarios/datos_crudos.html', {
        'usuarios': usuarios,
        'asistencias': asistencias,
        'error': error
    })

def listar_usuarios(request):
    from .utils import sincronizar_usuarios
    sincronizar_usuarios()

    search_query = request.GET.get("search", "")
    usuarios_qs = UsuarioReloj.objects.all()
    if search_query:
        usuarios_qs = usuarios_qs.filter(
            Q(nombre__icontains=search_query) | Q(user_id__icontains=search_query)
        )

    paginator = Paginator(usuarios_qs.order_by("user_id"), 10)
    page_number = request.GET.get("page")
    usuarios = paginator.get_page(page_number)

    return render(request, "rrhh/usuarios/listar_usuarios.html", {
        "usuarios": usuarios,
        "search_query": search_query
    })

def agregar_usuario(request):
    if request.method == "POST":
        user_id = request.POST['user_id']
        nombre = request.POST['nombre']
        password = request.POST['password']
        card = request.POST['card']

        ultimo_uid = UsuarioReloj.objects.aggregate(models.Max('uid'))['uid__max'] or 0
        nuevo_uid = ultimo_uid + 1

        UsuarioReloj.objects.create(
            uid=nuevo_uid,
            user_id=int(user_id),
            nombre=nombre,
            password=password,
            card=card
        )

        zk = ZK('192.168.2.107', port=4370, timeout=5)
        try:
            conn = zk.connect()
            conn.disable_device()

            if password and card:
                conn.set_user(
                    uid=nuevo_uid,
                    user_id=user_id,
                    name=nombre,
                    password=password,
                    card=card
                )
            elif password and not card:
                conn.set_user(
                    uid=nuevo_uid,
                    user_id=user_id,
                    name=nombre,
                    password=password,
                )
            elif not password and card:
                conn.set_user(
                    uid=nuevo_uid,
                    user_id=user_id,
                    name=nombre,
                    card=card
                )
            elif not password and not card:
                conn.set_user(
                    uid=nuevo_uid,
                    user_id=user_id,
                    name=nombre,
                )
            conn.enable_device()
            conn.disconnect()
        except Exception as e:
            print(f"❌ Error al agregar al reloj: {e}")

    return redirect("listar_usuarios")

def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(UsuarioReloj, id=usuario_id)

    if request.method == "POST":
        usuario.nombre = request.POST.get('nombre', '').strip()
        usuario.password = request.POST.get('password', 0).strip()
        usuario.card = request.POST.get('card', 0).strip()
        usuario.save()

        zk = ZK('192.168.2.107', port=4370, timeout=5)

        try:
            conn = zk.connect()
            conn.disable_device()
            
            if usuario.password and usuario.card:
                conn.set_user(
                    uid=int(usuario.uid),
                    user_id=str(usuario.user_id),
                    name=usuario.nombre,
                    password=usuario.password,
                    card=usuario.card
                )
            elif usuario.password and not usuario.card:
                conn.set_user(
                    uid=int(usuario.uid),
                    user_id=str(usuario.user_id),
                    name=usuario.nombre,
                    password=usuario.password
                )
            elif usuario.card and not usuario.password:
                conn.set_user(
                    uid=int(usuario.uid),
                    user_id=str(usuario.user_id),
                    name=usuario.nombre,
                    card=usuario.card
                )
            elif not usuario.password and not usuario.card:
                conn.set_user(
                    uid=int(usuario.uid),
                    user_id=str(usuario.user_id),
                    name=usuario.nombre
                )

            conn.enable_device()
            conn.disconnect()
            messages.success(request, "✅ Usuario editado correctamente en el reloj y base de datos.")

        except Exception as e:
            messages.error(request, f"❌ Error al editar en el reloj: {e}")
            print(f"❌ Error al editar en el reloj: {e}")

    return redirect("listar_usuarios")

def convertir_entero(valor, por_defecto=0):
    try:
        return int(valor)
    except (ValueError, TypeError):
        return por_defecto

def eliminar_usuario(request, usuario_id):
    usuario = get_object_or_404(UsuarioReloj, id=usuario_id)
    zk = ZK('192.168.2.107', port=4370, timeout=5)
    try:
        conn = zk.connect()
        conn.disable_device()
        conn.delete_user(uid=usuario.uid)
        conn.enable_device()
        conn.disconnect()
    except Exception as e:
        print(f"❌ Error al eliminar del reloj: {e}")

    usuario.delete()
    return redirect("listar_usuarios")

#* -------------------------------------------------------------------------------- Asistencias
from django.http import JsonResponse
from django.views.decorators.http import require_GET

@require_GET
def sincronizar_datos_ajax(request):
    try:
        from .utils import sincronizar_usuarios, sincronizar_asistencias

        sincronizar_usuarios()
        nuevos = sincronizar_asistencias()  # <- modificaremos esto para que retorne cuántos

        return JsonResponse({'status': 'ok', 'nuevos': nuevos})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def listar_asistencias(request):
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)

    fecha_inicio = request.GET.get('fecha_inicio') or hoy.strftime('%Y-%m-%d')
    fecha_fin = request.GET.get('fecha_fin') or hoy.strftime('%Y-%m-%d')
    busqueda = request.GET.get('busqueda', '')
    usuario_id = request.GET.get('usuario_id', '')

    # Filtrar asistencias en base a fecha
    asistencias = RegistroAsistencia.objects.filter(
        fecha__range=[fecha_inicio, fecha_fin]
    )

    if usuario_id:
        asistencias = asistencias.filter(usuario__user_id=usuario_id)

    if busqueda:
        asistencias = asistencias.filter(
            Q(usuario__nombre__icontains=busqueda) |
            Q(usuario__user_id__icontains=busqueda)
        )

    # Agrupar por usuario + fecha con entrada y salida
    agrupadas_qs = asistencias.values('usuario__user_id', 'usuario__nombre', 'fecha')\
        .annotate(entrada=Min('hora'), salida=Max('hora'))\
        .order_by('fecha', 'usuario__nombre')

    agrupadas = []
    detalles_asistencias = {}

    for asistencia in agrupadas_qs:
        user_id = asistencia['usuario__user_id']
        fecha = asistencia['fecha']
        clave = f"{user_id}_{fecha.strftime('%Y-%m-%d')}"

        registros = RegistroAsistencia.objects.filter(
            usuario__user_id=user_id,
            fecha=fecha
        ).order_by('hora')

        detalles_asistencias[clave] = registros

        agrupadas.append({
            'usuario_id': user_id,
            'usuario_nombre': asistencia['usuario__nombre'],
            'fecha': fecha,
            'entrada': asistencia['entrada'],
            'salida': asistencia['salida'],
            'clave': clave
        })

    usuarios = UsuarioReloj.objects.all()

    contexto = {
        'asistencias': agrupadas,
        'usuarios': usuarios,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'busqueda': busqueda,
        'detalles_asistencias': detalles_asistencias,
        'usuario_id': usuario_id
    }

    return render(request, 'rrhh/asistencias/asistencias.html', contexto)


#* ----------------------------------------------------------------------------------------------- TALENTO HUMANO (ADMIN)
def listar_colaboradores(request):
    colaboradores = Colaborador.objects.all().order_by('-activo', 'nombre_completo')
    return render(request, 'rrhh/colaboradores/lista_colaboradores.html', {'colaboradores': colaboradores})

from django.http import JsonResponse
from django.db.models import Q

def listar_colaboradores(request):
    q = request.GET.get("buscar", "")
    colaboradores = Colaborador.objects.all()

    if q:
        colaboradores = colaboradores.filter(
            Q(nombre_completo__icontains=q) | Q(codigo_empleado__icontains=q)
        )

    colaboradores = colaboradores.order_by('-activo', 'nombre_completo')
    return render(request, 'rrhh/rh_admin/lista_colaboradores.html', {
        'colaboradores': colaboradores,
        'buscar': q
    })

def ver_colaborador(request, colaborador_id):
    colaborador = get_object_or_404(Colaborador, id=colaborador_id)
    historial_horarios = HistorialHorario.objects.filter(colaborador=colaborador).select_related('horario').order_by('-fecha_inicio')

    return render(request, 'rrhh/rh_admin/ver_colaborador.html', {
        'colaborador': colaborador,
        'historial_horarios': historial_horarios,
        'horarios': HorarioLaboral.objects.all(),  # Para el modal de creación/edición
    })

def crear_colaborador(request):
    usuarios = User.objects.all()
    horarios = HorarioLaboral.objects.all()
    
    if request.method == "POST":
        colaborador = Colaborador(
            usuario_sistema_id=request.POST.get('usuario_sistema') or None,
            aprobador_id=request.POST.get('aprobador') or None,
            nombre_completo=request.POST.get('nombre_completo'),
            identificacion=request.POST.get('identificacion'),
            codigo_empleado=request.POST.get('codigo_empleado'),
            puesto=request.POST.get('puesto'),
            departamento=request.POST.get('departamento'),
            correo=request.POST.get('correo'),
            telefono=request.POST.get('telefono'),
            direccion=request.POST.get('direccion'),
            fecha_ingreso=request.POST.get('fecha_ingreso'),
            foto=request.FILES.get('foto'),
            horario_id=request.POST.get('horario') or None
        )
        colaborador.save()
        # ✅ Crear historial de horario si hay horario asignado
        if colaborador.horario:
            HistorialHorario.objects.create(
                colaborador=colaborador,
                horario=colaborador.horario,
                fecha_inicio=timezone.now().date()
            )
            return redirect('listar_colaboradores')

    return render(request, 'rrhh/rh_admin/crear_colaborador.html', {
        'usuarios': usuarios,
        'horarios': horarios,
    })

def editar_colaborador(request, colaborador_id):
    colaborador = get_object_or_404(Colaborador, id=colaborador_id)
    usuarios = User.objects.all()
    horarios = HorarioLaboral.objects.all()

    if request.method == 'POST':
        # 🟡 Detectar nuevo horario
        nuevo_horario_id = request.POST.get('horario')
        nuevo_horario = HorarioLaboral.objects.filter(id=nuevo_horario_id).first() if nuevo_horario_id else None

        # 🟢 Si cambió el horario, guardar en el historial
        if colaborador.horario != nuevo_horario:
            # Cierra historial anterior (si existe y no está cerrado)
            historial_anterior = HistorialHorario.objects.filter(
                colaborador=colaborador,
                fecha_fin__isnull=True
            ).order_by('-fecha_inicio').first()

            if historial_anterior:
                historial_anterior.fecha_fin = timezone.now().date() - timedelta(days=1)
                historial_anterior.save()

            # Crea nuevo historial
            if nuevo_horario:
                HistorialHorario.objects.create(
                    colaborador=colaborador,
                    horario=nuevo_horario,
                    fecha_inicio=timezone.now().date()
                )

        # 🔄 Actualizar campos del colaborador
        colaborador.nombre_completo = request.POST.get('nombre_completo')
        colaborador.identificacion = request.POST.get('identificacion')
        colaborador.codigo_empleado = request.POST.get('codigo_empleado')
        colaborador.puesto = request.POST.get('puesto')
        colaborador.departamento = request.POST.get('departamento')
        colaborador.fecha_ingreso = request.POST.get('fecha_ingreso') or None
        colaborador.correo = request.POST.get('correo')
        colaborador.telefono = request.POST.get('telefono')
        colaborador.direccion = request.POST.get('direccion')

        user_id = request.POST.get('usuario_sistema')
        aprobador_id = request.POST.get('aprobador')
        colaborador.usuario_sistema = User.objects.filter(id=user_id).first() if user_id else None
        colaborador.aprobador = User.objects.filter(id=aprobador_id).first() if aprobador_id else None
        colaborador.horario = nuevo_horario

        if 'foto' in request.FILES:
            colaborador.foto = request.FILES['foto']

        colaborador.save()
        messages.success(request, "✅ Colaborador actualizado correctamente.")
        return redirect('ver_colaborador', colaborador_id=colaborador.id)

    return render(request, 'rrhh/rh_admin/editar_colaborador.html', {
        'colaborador': colaborador,
        'usuarios': usuarios,
        'horarios': horarios,
    })

def cambiar_estado_colaborador(request, colaborador_id):
    if request.method == 'POST':
        try:
            colaborador = Colaborador.objects.get(id=colaborador_id)
            colaborador.activo = not colaborador.activo
            colaborador.save()
            return JsonResponse({'status': 'ok', 'nuevo_estado': colaborador.activo})
        except Colaborador.DoesNotExist:
            return JsonResponse({'status': 'error', 'mensaje': 'Colaborador no encontrado'})
    return JsonResponse({'status': 'error', 'mensaje': 'Método no permitido'}, status=405)

def expediente_colaborador(request, colaborador_id):
    colaborador = get_object_or_404(Colaborador, id=colaborador_id)
    documentos = colaborador.documentos.all().order_by('-fecha_subida')
    return render(request, 'rrhh/colaboradores/expediente.html', {
        'colaborador': colaborador,
        'documentos': documentos
    })

def listar_colaboradores_reporte(request):
    query = request.GET.get("busqueda", "")
    colaboradores = Colaborador.objects.filter(
        Q(nombre_completo__icontains=query) | Q(codigo_empleado__icontains=query)
    ).order_by("nombre_completo")

    contexto = {
        "colaboradores": colaboradores,
        "busqueda": query,
    }
    return render(request, "rrhh/reportes/listar_colaboradores.html", contexto)

def editar_reporte_colaborador(request, colaborador_id):
    colaborador = get_object_or_404(Colaborador, id=colaborador_id)
    hoy = timezone.now().date()

    # Rango de fechas
    inicio = request.GET.get("fecha_inicio", hoy.replace(day=1))
    fin = request.GET.get("fecha_fin", hoy)

    # Convertir string a fecha si es necesario
    if isinstance(inicio, str):
        inicio = datetime.strptime(inicio, "%Y-%m-%d").date()
    if isinstance(fin, str):
        fin = datetime.strptime(fin, "%Y-%m-%d").date()

    # Obtener registros existentes o generarlos si no hay
    registros = ReporteAsistenciaColaborador.objects.filter(
        colaborador=colaborador,
        fecha__range=[inicio, fin]
    ).order_by("fecha")

    if not registros.exists():
        dias = (fin - inicio).days + 1
        for i in range(dias):
            fecha = inicio + timedelta(days=i)
            jornada = "FIN DE SEMANA" if fecha.weekday() in (5, 6) else "Normal"
            ReporteAsistenciaColaborador.objects.get_or_create(
                colaborador=colaborador,
                fecha=fecha,
                defaults={
                    'jornada': jornada,
                    'horario': '08:00 a 17:00',
                }
            )
        registros = ReporteAsistenciaColaborador.objects.filter(
            colaborador=colaborador,
            fecha__range=[inicio, fin]
        ).order_by("fecha")

    # ✅ Obtener entrada y salida desde los registros de asistencia (en memoria)
    for r in registros:
        marcajes = RegistroAsistencia.objects.filter(
            usuario__user_id=colaborador.codigo_empleado,
            fecha=r.fecha
        ).order_by("hora")

        if marcajes.exists():
            r.entrada = marcajes.first().hora
            r.salida = marcajes.last().hora
        else:
            r.entrada = None
            r.salida = None

    # ✅ Si se envía el formulario (POST)
    if request.method == "POST":
        for registro in registros:
            registro.razon = request.POST.get(f"razon_{registro.id}", "")
            registro.justificacion = request.POST.get(f"justificacion_{registro.id}", "")
            registro.columna_1 = request.POST.get(f"col1_{registro.id}", "")
            registro.columna_2 = request.POST.get(f"col2_{registro.id}", "")
            registro.columna_3 = request.POST.get(f"col3_{registro.id}", "")
            registro.columna_4 = request.POST.get(f"col4_{registro.id}", "")
            registro.columna_5 = request.POST.get(f"col5_{registro.id}", "")
            registro.save()

        messages.success(request, "✅ Cambios guardados correctamente.")
        return redirect("editar_reporte_colaborador", colaborador_id=colaborador.id)

    contexto = {
        "colaborador": colaborador,
        "registros": registros,
        "fecha_inicio": inicio,
        "fecha_fin": fin,
    }
    return render(request, 'rrhh/reportes/editar_reporte_colaborador.html', contexto)

from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML, CSS
import tempfile
import datetime
from datetime import datetime, timedelta
from django.db.models import Min, Max
import os
import tempfile
from django.conf import settings
from django.http import FileResponse

WEEKDAY_TO_DIA = {
    0: '0', 1: '1', 2: '2',
    3: '3', 4: '4', 5: '5', 6: '6'
}

def obtener_horario_para_fecha(colaborador, fecha):
    """
    Devuelve el horario válido según el historial en la fecha dada.
    Si no hay historial en esa fecha o el horario no incluye ese día, retorna None.
    """
    dia_str = WEEKDAY_TO_DIA[fecha.weekday()]

    historial = (
        HistorialHorario.objects
        .filter(
            colaborador=colaborador,
            fecha_inicio__lte=fecha
        )
        .filter(models.Q(fecha_fin__isnull=True) | models.Q(fecha_fin__gte=fecha))
        .order_by('-fecha_inicio')
        .first()
    )

    if historial and historial.horario.dias.filter(dia=dia_str).exists():
        return historial.horario

    return None

def generar_pdf_reporte_colaborador(request, colaborador_id):
    colaborador = get_object_or_404(Colaborador, id=colaborador_id)
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    try:
        inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    except Exception:
        return HttpResponse("Fechas inválidas", status=400)

    # Obtener marcajes
    marcajes = RegistroAsistencia.objects.filter(
        usuario__user_id=colaborador.codigo_empleado,
        fecha__range=(inicio, fin)
    ).values('fecha').annotate(
        entrada_real=Min('hora'),
        salida_real=Max('hora')
    )
    asistencias_por_fecha = {m['fecha']: m for m in marcajes}

    registros = []
    delta = (fin - inicio).days

    for i in range(delta + 1):
        fecha_actual = inicio + timedelta(days=i)
        asistencia = asistencias_por_fecha.get(fecha_actual)
        dia_str = WEEKDAY_TO_DIA[fecha_actual.weekday()]
        es_fin_de_semana = fecha_actual.weekday() in [5, 6]

        horario_str = ''

        horario = obtener_horario_para_fecha(colaborador, fecha_actual)

        if horario:
            horario_dia = horario.dias.filter(dia=dia_str).first()
            if horario_dia:
                horario_str = f"{horario_dia.hora_entrada.strftime('%H:%M')} a {horario_dia.hora_salida.strftime('%H:%M')}"

        registros.append({
            'fecha': fecha_actual,
            'jornada': 'FIN DE SEMANA' if es_fin_de_semana else 'Normal',
            'horario': horario_str,
            'entrada_real': asistencia['entrada_real'] if asistencia else None,
            'salida_real': asistencia['salida_real'] if asistencia else None,
            'razon': '', 'justificacion': '',
            'columna_1': '', 'columna_2': '', 'columna_3': '',
            'columna_4': '', 'columna_5': ''
        })

    html_string = render_to_string("rrhh/pdf/reporte_colaborador_pdf.html", {
        'colaborador': colaborador,
        'registros': registros,
        'fecha_inicio': inicio,
        'fecha_fin': fin,
        'fecha_generado': datetime.now().strftime("%d/%m/%Y"),
        'logo_url': request.build_absolute_uri('/static/img/logo_ccit.png'),
    })

    temp_dir = os.path.join(settings.BASE_DIR, "temp_pdfs")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"reporte_{colaborador.codigo_empleado}.pdf")

    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(
        target=temp_path,
        stylesheets=[CSS(string='''
            @page {
                size: letter landscape;
                margin: 4cm 0.2cm 0.2cm 0.2cm;
                @top-center {
                    content: element(header);
                }
            }
            #encabezado {
                display: block;
                margin-bottom: 10px;
            }
            body {
                font-family: Arial, sans-serif;
                font-size: 10px;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                table-layout: auto;
            }
            th, td {
                border: 1px solid #ccc;
                padding: 1px;
                text-align: center;
                vertical-align: middle;
                word-wrap: break-word;
            }
            th {
                background-color: #eee;
            }
            td.jornada {
                width: 5%;
            }
            td.horario {
                width: 3%;
            }
            td.razon {
                width: 8%;
            }
            td.justificacion {
                width: 15%;
            }
            tfoot td {
                font-size: 10px;
            }
            tfoot tr:first-child td {
                border-top: 2px solid #000;
                height: 20px;
            }
            tr.total-horas {
                page-break-inside: avoid;
            }
        ''')]
    )

    with open(temp_path, "rb") as f:
        response = HttpResponse(f.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="reporte_{colaborador.codigo_empleado}.pdf"'
        return response

from django.utils.translation import gettext_lazy as _

DIAS_SEMANA = [
    (0, _('Lunes')),
    (1, _('Martes')),
    (2, _('Miércoles')),
    (3, _('Jueves')),
    (4, _('Viernes')),
    (5, _('Sábado')),
    (6, _('Domingo')),
]

def listar_horarios(request):
    horarios = HorarioLaboral.objects.prefetch_related('dias').all()
    return render(request, 'parametros/horarios_laborales.html', {
        'horarios': horarios,
        'dias_semana': DIAS_SEMANA
    })

def crear_horario(request):
    nombre = request.POST.get('nombre')
    if not nombre:
        messages.error(request, "El nombre es obligatorio.")
        return redirect('listar_horarios')

    horario = HorarioLaboral.objects.create(nombre=nombre)

    for dia, _ in DIAS_SEMANA:
        entrada = request.POST.get(f'entrada_{dia}')
        salida = request.POST.get(f'salida_{dia}')
        if entrada and salida:
            HorarioDia.objects.create(
                horario=horario,
                dia=dia,
                hora_entrada=entrada,
                hora_salida=salida
            )

    messages.success(request, "✅ Horario creado correctamente.")
    return redirect('horarios_laborales')

def editar_horario(request, horario_id):
    horario = get_object_or_404(HorarioLaboral, id=horario_id)
    horario.nombre = request.POST.get('nombre', horario.nombre)
    horario.save()

    dias_recibidos = []

    for dia, _ in DIAS_SEMANA:
        entrada = request.POST.get(f'entrada_{dia}')
        salida = request.POST.get(f'salida_{dia}')

        if entrada and salida:
            dias_recibidos.append(dia)
            HorarioDia.objects.update_or_create(
                horario=horario,
                dia=dia,
                defaults={
                    'hora_entrada': entrada,
                    'hora_salida': salida
                }
            )
        else:
            # Eliminar si el día está incompleto o fue eliminado
            HorarioDia.objects.filter(horario=horario, dia=dia).delete()

    messages.success(request, "✅ Horario actualizado correctamente.")
    return redirect('horarios_laborales')

def eliminar_horario(request, horario_id):
    horario = get_object_or_404(HorarioLaboral, id=horario_id)
    horario.delete()
    messages.success(request, "✅ Horario eliminado correctamente.")
    return redirect('horarios_laborales')


def agregar_historial_horario(request, colaborador_id):
    colaborador = get_object_or_404(Colaborador, id=colaborador_id)
    if request.method == 'POST':
        horario_id = request.POST.get('horario_id')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin') or None

        if horario_id and fecha_inicio:
            HistorialHorario.objects.create(
                colaborador=colaborador,
                horario_id=horario_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )
            messages.success(request, "✅ Historial de horario agregado.")
        else:
            messages.error(request, "⚠️ Datos incompletos.")
    return redirect('ver_colaborador', colaborador_id=colaborador.id)

def editar_historial_horario(request, historial_id):
    historial = get_object_or_404(HistorialHorario, id=historial_id)
    if request.method == 'POST':
        horario_id = request.POST.get('horario_id')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin') or None

        if horario_id and fecha_inicio:
            historial.horario_id = horario_id
            historial.fecha_inicio = fecha_inicio
            historial.fecha_fin = fecha_fin
            historial.save()
            messages.success(request, "✅ Historial actualizado correctamente.")
        else:
            messages.error(request, "⚠️ Datos incompletos.")
    return redirect('ver_colaborador', colaborador_id=historial.colaborador.id)

def eliminar_historial_horario(request, historial_id):
    historial = get_object_or_404(HistorialHorario, id=historial_id)
    colaborador_id = historial.colaborador.id
    historial.delete()
    messages.success(request, "✅ Historial eliminado.")
    return redirect('ver_colaborador', colaborador_id=colaborador_id)