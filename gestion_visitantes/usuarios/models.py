from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pin = models.CharField(max_length=6, blank=True, null=True)
    first_login = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username
    
class Eventos(models.Model):
    cod_asamblea = models.CharField(max_length=500)
    accion = models.CharField(max_length=500)
    usuario_registro = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)