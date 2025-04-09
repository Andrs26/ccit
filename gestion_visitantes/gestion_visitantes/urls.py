"""
URL configuration for gestion_visitantes project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from usuarios import views
from logs import views as logs
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', include('eventos.urls')),
    path('', include('lista_negra.urls')),
    path('', include('logs.urls')),
    path('', include('pases.urls')),
    path('registro-entrada-salida/', include('pertenencias.urls')),
    path('', include('usuarios.urls')),
    path('', include('visitantes.urls')),
    path('', include('colaboradores.urls')),
    path('', include('biometrico.urls')),
    path('servicios/', logs.listar_servicios, name='listar_servicios'),
    path('servicios/crear/', logs.crear_servicio, name='crear_servicio'),
    path('servicios/editar/<int:pk>/', logs.editar_servicio, name='editar_servicio'),
    path('servicios/eliminar/<int:pk>/', logs.eliminar_servicio, name='eliminar_servicio'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)