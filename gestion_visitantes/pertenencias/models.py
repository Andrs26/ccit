from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class PertenenciasVisitante(models.Model):
    """Registro de pertenencias al ingresar y salir"""
    cod_visita = models.CharField(max_length=50)
    identificacion_visitante = models.CharField(max_length=50)
    pertenencias_entrada = models.TextField()
    pertenencias_salida = models.TextField(null=True, blank=True)
    observaciones_ingreso = models.TextField(null=True, blank=True)
    observaciones_salida = models.TextField(null=True, blank=True)
    documento_soporte = models.FileField(upload_to='documentos/', blank=True, null=True)
    aceptacion = models.FileField(upload_to='aceptacion/', blank=True, null=True)
    usuario_registro_ingreso = models.CharField(max_length=50)
    usuario_registro_salida = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.visitante.nombre} - Pertenencias"