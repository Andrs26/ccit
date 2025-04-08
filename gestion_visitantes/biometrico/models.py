from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.
class UsuarioReloj(models.Model):
    uid = models.IntegerField()
    user_id = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    privilegio = models.IntegerField(default=0)
    password = models.CharField(max_length=50, blank=True)
    card = models.CharField(max_length=50, blank=True)
    grupo = models.IntegerField(default=1)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user_id} - {self.nombre}"

class RegistroAsistencia(models.Model):
    usuario = models.ForeignKey(UsuarioReloj, to_field='user_id', on_delete=models.SET_NULL, null=True)
    fecha = models.DateField(blank=True, null=True)
    hora = models.TimeField(blank=True, null=True)
    tipo_evento = models.CharField(max_length=20)
    metodo_autenticacion = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.usuario} - {self.fecha} {self.hora} - {self.tipo_evento}"

User = get_user_model()

class Colaborador(models.Model):
    usuario_sistema = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='colaborador_biometrico')
    aprobador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='colaborador_visitantes')

    codigo_empleado = models.CharField(max_length=10, unique=True)  # 🔥 NUEVO
    identificacion = models.CharField(max_length=20, unique=True)
    nombre_completo = models.CharField(max_length=200)
    correo = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)
    puesto = models.CharField(max_length=100, blank=True)
    departamento = models.CharField(max_length=100, blank=True)
    fecha_ingreso = models.DateField(null=True, blank=True)
    foto = models.ImageField(upload_to='fotos_colaboradores/', null=True, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre_completo


class DocumentoColaborador(models.Model):
    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE, related_name='documentos')
    nombre = models.CharField(max_length=100)
    archivo = models.FileField(upload_to='documentos_colaboradores/')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.colaborador.nombre_completo}"

class ReporteAsistenciaColaborador(models.Model):
    colaborador = models.ForeignKey('Colaborador', on_delete=models.CASCADE)
    fecha = models.DateField()
    jornada = models.CharField(max_length=20, default="Normal")  # Automática
    horario = models.CharField(max_length=50, default="08:00 a 17:00")  # Luego vendrá del colaborador
    entrada = models.TimeField(null=True, blank=True)
    salida = models.TimeField(null=True, blank=True)
    razon = models.CharField(max_length=255, blank=True, null=True)
    justificacion = models.CharField(max_length=255, blank=True, null=True)
    columna_1 = models.CharField(max_length=255, blank=True, null=True)
    columna_2 = models.CharField(max_length=255, blank=True, null=True)
    columna_3 = models.CharField(max_length=255, blank=True, null=True)
    columna_4 = models.CharField(max_length=255, blank=True, null=True)
    columna_5 = models.CharField(max_length=255, blank=True, null=True)
    total_horas = models.DurationField(null=True, blank=True)

    class Meta:
        unique_together = ('colaborador', 'fecha')
