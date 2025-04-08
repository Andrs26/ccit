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


def sincronizar_asistencias():
    zk = ZK('192.168.2.107', port=4370, timeout=5)
    status_map = {
        0: "Entrada",
        1: "Salida",
        2: "Salida (extra)"
    }
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

        # ✅ Verificamos los user_id válidos
        user_ids_existentes = set(UsuarioReloj.objects.values_list('user_id', flat=True))

        # ✅ Obtener el último registro guardado localmente
        ultimo_registro = RegistroAsistencia.objects.order_by('-fecha', '-hora').first()
        ultima_fecha_hora = None
        if ultimo_registro:
            ultima_fecha_hora = datetime.combine(ultimo_registro.fecha, ultimo_registro.hora)

        # ✅ Recorremos los registros nuevos
        guardados = 0
        for r in asistencias:
            user_id = str(r.user_id)

            # ✅ Evita error FK
            if user_id not in user_ids_existentes:
                continue

            fecha_hora = r.timestamp

            # ✅ Ignorar registros antiguos o iguales al último
            if ultima_fecha_hora and fecha_hora <= ultima_fecha_hora:
                continue

            RegistroAsistencia.objects.create(
            usuario_id=user_id,
            fecha=fecha_hora.date(),
            hora=fecha_hora.time(),
            tipo_evento=status_map.get(r.status, f"Desconocido ({r.status})"),
            metodo_autenticacion=auth_map.get(r.punch, "Desconocido")
)

            guardados += 1

        conn.enable_device()
        conn.disconnect()
        print("✅ Asistencias sincronizadas correctamente.")
        return guardados
    except Exception as e:
        print(f"❌ Error al sincronizar asistencias: {e}")
        return 0