import uuid
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Visitante(models.Model):
    """Registro de datos básicos de los visitantes"""
    cod_visita = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=255)
    documento_identificacion = models.CharField(max_length=50, unique=True)
    foto_documento_identificacion = models.ImageField(upload_to='visitantes/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre


class MotivoVisita(models.Model):
    """Lista de motivos de visita (reunión, entrevista, entrega, etc.)"""
    descripcion = models.CharField(max_length=255, unique=True)
    estado = models.CharField(max_length=50, choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.descripcion


class TipoVisita(models.Model):
    """Lista de tipos de visita (individual, grupo, escolta, etc.)"""
    descripcion = models.CharField(max_length=255, unique=True)
    estado = models.CharField(max_length=50, choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.descripcion


class Visita(models.Model):
    """Registro de visitas con información del visitante, motivo y tipo"""
    cod_visita = models.CharField(max_length=50, unique=True)
    visitante = models.CharField(max_length=500)
    motivo = models.TextField()
    tipo = models.TextField()
    area_departamento = models.CharField(max_length=255)
    persona_visitada = models.CharField(max_length=255)
    fecha_visita = models.DateField()
    hora_ingreso = models.TimeField()
    hora_salida = models.TimeField(null=True, blank=True)
    usuario_registro = models.CharField(max_length=50)
    num_pase = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.visitante.nombre} - {self.fecha_visita}"


class Acompanante(models.Model):
    """Registro de acompañantes en visitas grupales o con escolta"""
    visita = models.CharField(max_length=500)
    nombre = models.CharField(max_length=255)
    documento_identificacion = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre
