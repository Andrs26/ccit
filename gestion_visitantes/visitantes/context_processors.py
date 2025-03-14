from django.contrib.auth.models import User

def grupos_usuario(request):
    if request.user.is_authenticated:
        grupos = request.user.groups.all()
        usuarios = User.objects.filter(is_active=True)  # Solo usuarios activos
    else:
        grupos = []
        usuarios = []
    return {
        'user_grupos': grupos,
        'users': usuarios,
    }