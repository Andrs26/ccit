from django.db import models

# Create your models here.
from django.utils import timezone

class ServicioWeb(models.Model):
    nombre = models.CharField(max_length=100)
    url = models.URLField()
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    ultimo_estado = models.CharField(max_length=10, blank=True, null=True)
    ultimo_detalle = models.TextField(blank=True, null=True)
    ultima_revision = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.nombre

class ChequeoServicio(models.Model):
    servicio = models.ForeignKey(ServicioWeb, on_delete=models.CASCADE, related_name='chequeos')
    estado = models.CharField(max_length=10)
    detalle = models.TextField()
    fecha = models.DateTimeField(default=timezone.now)