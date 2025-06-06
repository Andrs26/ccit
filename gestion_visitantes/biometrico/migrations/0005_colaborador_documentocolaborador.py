# Generated by Django 5.1 on 2025-04-04 15:18

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('biometrico', '0004_alter_usuarioreloj_user_id'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Colaborador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo_empleado', models.CharField(max_length=10, unique=True)),
                ('identificacion', models.CharField(max_length=20, unique=True)),
                ('nombre_completo', models.CharField(max_length=200)),
                ('correo', models.EmailField(blank=True, max_length=254, null=True)),
                ('telefono', models.CharField(blank=True, max_length=20)),
                ('direccion', models.TextField(blank=True)),
                ('puesto', models.CharField(blank=True, max_length=100)),
                ('departamento', models.CharField(blank=True, max_length=100)),
                ('fecha_ingreso', models.DateField(blank=True, null=True)),
                ('foto', models.ImageField(blank=True, null=True, upload_to='fotos_colaboradores/')),
                ('activo', models.BooleanField(default=True)),
                ('aprobador', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='colaborador_visitantes', to=settings.AUTH_USER_MODEL)),
                ('usuario_sistema', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='colaborador_biometrico', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='DocumentoColaborador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('archivo', models.FileField(upload_to='documentos_colaboradores/')),
                ('fecha_subida', models.DateTimeField(auto_now_add=True)),
                ('colaborador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documentos', to='biometrico.colaborador')),
            ],
        ),
    ]
