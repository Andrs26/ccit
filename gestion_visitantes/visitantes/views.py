from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.cache import cache
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.db.models.functions import TruncDate
from django.utils.timezone import now
from django.http import JsonResponse
from django.utils import timezone
from django.urls import reverse
import pandas as pd
import traceback  # Para imprimir el error completo en la consola
import random
import json
import io
import os

""" Importación de los modelos """
from usuarios.models import *
from visitantes.models import *

# Create your views here.
@login_required
def visitas(request):
    return render(request, 'inicio/inicio.html', {
        # 'is_admin_group': is_admin_group,
        # 'is_super_admin': is_super_admin,
        # 'is_estandar_group': is_estandar_group,
        # 'disabled': disabled,
        # 'estado_asamblea': estado_asamblea
    })

@login_required
def nueva_visita(request):
    return render(request, 'visitantes/nueva-visita.html')