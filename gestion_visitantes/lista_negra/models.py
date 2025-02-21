from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class ListaNegra(models.Model):
    """Registro de visitantes con acceso restringido"""
    documento_identificacion = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=255)
    foto_documento_identificacion = models.ImageField(upload_to='lista_negra/', blank=True, null=True)
    motivo = models.TextField()
    usuario_registro = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre