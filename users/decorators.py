from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrap(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrap
    return decorator

admin_only = role_required('admin')
teacher_only = role_required('teacher')
student_only = role_required('student')
parent_only = role_required('parent')
admin_or_teacher = role_required('admin', 'teacher')