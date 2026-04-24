from django.core.exceptions import PermissionDenied

def admin_only(view_func):
    def wrap(request, *args, **kwargs):
        if request.user.role == 'admin':
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied # Kirish taqiqlangan!
    return wrap