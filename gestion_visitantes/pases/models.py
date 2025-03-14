from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class PaseAcceso(models.Model):
    """Registro de pases de acceso a instalaciones"""
    numero_pase = models.CharField(max_length=50, unique=True)
    lugares_acceso = models.TextField()
    estado = models.CharField(max_length=50, choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')])
    estado_pase = models.CharField(max_length=50)
    comentario_reporte = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.numero_pase
