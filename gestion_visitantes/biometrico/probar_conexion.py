# from .pyzk.zkmodules.zk.base import ZK

# def probar_conexion():
#     zk = ZK('192.168.2.107', port=4370, timeout=5)

#     try:
#         conn = zk.connect()
#         conn.disable_device()

#         print("✅ Conectado al reloj ZKTeco")

#         users = conn.get_users()
#         print(f"Usuarios registrados: {len(users)}")

#         attendance = conn.get_attendance()
#         print(f"Registros de asistencia: {len(attendance)}")

#         conn.enable_device()
#         conn.disconnect()
#     except Exception as e:
#         print(f"❌ Error: {e}")

# # Ejecutar si es script directo
# if __name__ == "__main__":
#     probar_conexion()
