from .pyzk.zkmodules.zk.base import ZK
from .models import *
from datetime import datetime
    
def sincronizar_usuarios():
    zk = ZK('192.168.2.107', port=4370, timeout=5)
    sincronizados = 0

    try:
        conn = zk.connect()
        conn.disable_device()

        usuarios_reloj = conn.get_users()

        for u in usuarios_reloj:
            user_id = str(u.user_id) if u.user_id not in (None, '', 0) else str(u.uid)

            # print(f"[🔍] Registrando: user_id={user_id}, uid={u.uid}, nombre={u.name}")

            _, _ = UsuarioReloj.objects.update_or_create(
                user_id=user_id,
                defaults={
                    'uid': int(u.uid) if u.uid not in (None, '') else 0,
                    'nombre': u.name,
                    'privilegio': u.privilege,
                    'password': u.password or '',
                    'card': u.card or '',
                    'grupo': int(u.group_id) if u.group_id not in (None, '') else 1,
                    'enabled': True
                }
            )
            sincronizados += 1

        conn.enable_device()
        conn.disconnect()
        print(f"✅ Se sincronizaron {sincronizados} usuarios.")
        return sincronizados

    except Exception as e:
        print(f"❌ Error al sincronizar usuarios: {e}")
        return 0


from collections import defaultdict

def sincronizar_asistencias():
    zk = ZK('192.168.2.107', port=4370, timeout=5)
    auth_map = {
        0: "PIN",
        1: "Huella",
        2: "Tarjeta",
        3: "Huella + PIN",
        4: "Tarjeta + PIN",
        5: "Huella + Tarjeta",
        6: "Huella + Tarjeta + PIN"
    }

    try:
        conn = zk.connect()
        conn.disable_device()

        asistencias = conn.get_attendance()
        user_ids_existentes = set(UsuarioReloj.objects.values_list('user_id', flat=True))

        ultimo_registro = RegistroAsistencia.objects.order_by('-fecha', '-hora').first()
        ultima_fecha_hora = datetime.combine(ultimo_registro.fecha, ultimo_registro.hora) if ultimo_registro else None

        # Agrupar registros por (user_id, fecha)
        registros_por_usuario_fecha = defaultdict(list)
        for r in asistencias:
            fecha_hora = r.timestamp
            user_id = str(r.user_id)

            if user_id not in user_ids_existentes:
                continue
            if ultima_fecha_hora and fecha_hora <= ultima_fecha_hora:
                continue

            registros_por_usuario_fecha[(user_id, fecha_hora.date())].append({
                'hora': fecha_hora.time(),
                'punch': r.punch
            })

        guardados = 0

        for (user_id, fecha), registros in registros_por_usuario_fecha.items():
            registros_ordenados = sorted(registros, key=lambda x: x['hora'])

            for i, reg in enumerate(registros_ordenados):
                if i == 0:
                    tipo_evento = "Entrada"
                elif i == len(registros_ordenados) - 1:
                    tipo_evento = "Salida"
                else:
                    tipo_evento = "Extra"

                RegistroAsistencia.objects.create(
                    usuario_id=user_id,
                    fecha=fecha,
                    hora=reg['hora'],
                    tipo_evento=tipo_evento,
                    metodo_autenticacion=auth_map.get(reg['punch'], "Desconocido")
                )
                guardados += 1

        conn.enable_device()
        conn.disconnect()
        print("✅ Asistencias sincronizadas correctamente.")
        return guardados

    except Exception as e:
        print(f"❌ Error al sincronizar asistencias: {e}")
        return 0
