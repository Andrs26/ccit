def grupos_usuario(request):
    if request.user.is_authenticated:
        grupos = request.user.groups.all()
    else:
        grupos = []
    return {'user_grupos': grupos}
